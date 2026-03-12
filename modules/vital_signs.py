import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

sys.path.append('..')
from config import config
from core.arduino_comm import ArduinoComm, VitalSigns, arduino
from core.utils import format_blood_pressure, format_heart_rate, format_temperature


@dataclass
class VitalSignsHistory:
    vitals: VitalSigns
    recorded_at: datetime


class VitalSignsMonitor:
    
    def __init__(self, arduino_comm: Optional[ArduinoComm] = None):
        self.arduino = arduino_comm or arduino
        self.history: list[VitalSignsHistory] = []
        self.max_history = 100
        self.callbacks: list[Callable[[VitalSigns], None]] = []
        self.alert_callbacks: list[Callable[[str, str], None]] = []
        self._is_monitoring = False
        
        self.thresholds = {
            "bp_systolic_high": 140,
            "bp_systolic_low": 90,
            "bp_diastolic_high": 90,
            "bp_diastolic_low": 60,
            "hr_high": 100,
            "hr_low": 60,
            "temp_high": 38.0,
            "temp_low": 35.5,
            "sugar_high": 140,
            "sugar_low": 70
        }
        
        self.manual_readings = {
            "sugar": 0,
            "weight": 0
        }
        
        self.arduino.add_callback(self._on_vitals_received)
    
    def _on_vitals_received(self, vitals: VitalSigns):
        self._add_to_history(vitals)
        self._check_alerts(vitals)
        
        for callback in self.callbacks:
            try:
                callback(vitals)
            except Exception as e:
                print(f"❌ Vitals callback error: {e}")
    
    def _add_to_history(self, vitals: VitalSigns):
        entry = VitalSignsHistory(
            vitals=vitals,
            recorded_at=datetime.now()
        )
        self.history.append(entry)
        
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def _check_alerts(self, vitals: VitalSigns):
        alerts = []
        
        if vitals.systolic >= self.thresholds["bp_systolic_high"]:
            alerts.append(("danger", f"⚠️ ضغط الدم مرتفع: {vitals.systolic}/{vitals.diastolic} mmHg"))
        elif vitals.systolic <= self.thresholds["bp_systolic_low"]:
            alerts.append(("warning", f"⬇️ ضغط الدم منخفض: {vitals.systolic}/{vitals.diastolic} mmHg"))
        
        if vitals.diastolic >= self.thresholds["bp_diastolic_high"]:
            alerts.append(("danger", f"⚠️ الضغط الانبساطي مرتفع: {vitals.diastolic} mmHg"))
        
        if vitals.heart_rate >= self.thresholds["hr_high"]:
            alerts.append(("warning", f"💓 نبضات القلب سريعة: {vitals.heart_rate} نبضة/دقيقة"))
        elif vitals.heart_rate <= self.thresholds["hr_low"]:
            alerts.append(("info", f"💓 نبضات القلب بطيئة: {vitals.heart_rate} نبضة/دقيقة"))
        
        if vitals.temperature >= self.thresholds["temp_high"]:
            alerts.append(("danger", f"🌡️ حرارة مرتفعة: {vitals.temperature}°C"))
        elif vitals.temperature <= self.thresholds["temp_low"]:
            alerts.append(("warning", f"🌡️ حرارة منخفضة: {vitals.temperature}°C"))
        
        for level, message in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(level, message)
                except Exception as e:
                    print(f"❌ Alert callback error: {e}")
    
    def start_monitoring(self):
        if not self._is_monitoring:
            self._is_monitoring = True
            self.arduino.start_reading()
            print("📊 Started vital signs monitoring")
    
    def stop_monitoring(self):
        if self._is_monitoring:
            self._is_monitoring = False
            self.arduino.stop_reading()
            print("⏹️ Stopped vital signs monitoring")
    
    def add_callback(self, callback: Callable[[VitalSigns], None]):
        self.callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable[[str, str], None]):
        self.alert_callbacks.append(callback)
    
    def get_current_vitals(self) -> VitalSigns:
        return self.arduino.get_current_vitals()
    
    def set_manual_reading(self, key: str, value: float):
        if key in self.manual_readings:
            self.manual_readings[key] = value
            vitals = self.get_current_vitals() 
            for callback in self.callbacks:
                 try: callback(vitals)
                 except: pass

    def get_formatted_vitals(self) -> dict:
        vitals = self.get_current_vitals()
        
        sugar_val = self.manual_readings["sugar"]
        sugar_status = "طبيعي"
        if sugar_val > self.thresholds["sugar_high"]: sugar_status = "مرتفع"
        elif sugar_val < self.thresholds["sugar_low"]: sugar_status = "منخفض"
        if sugar_val == 0: sugar_status = "غير مدخل"

        return {
            "blood_pressure": format_blood_pressure(vitals.systolic, vitals.diastolic),
            "heart_rate": format_heart_rate(vitals.heart_rate),
            "temperature": format_temperature(vitals.temperature),
            "sugar": {
                "value": str(int(sugar_val)) if sugar_val > 0 else "--",
                "unit": "mg/dL",
                "status": sugar_status
            },
            "weight": {
                 "value": str(self.manual_readings["weight"]) if self.manual_readings["weight"] > 0 else "--",
                 "unit": "kg",
                 "status": "ثابت"
            },
            "timestamp": vitals.timestamp,
            "is_valid": vitals.is_valid
        }
    
    def get_history(self, count: int = 10) -> list[VitalSignsHistory]:
        return self.history[-count:]
    
    def get_averages(self, minutes: int = 30) -> dict:
        cutoff_time = time.time() - (minutes * 60)
        recent = [h for h in self.history if h.vitals.timestamp >= cutoff_time]
        
        if not recent:
            return None
        
        avg_systolic = sum(h.vitals.systolic for h in recent) / len(recent)
        avg_diastolic = sum(h.vitals.diastolic for h in recent) / len(recent)
        avg_hr = sum(h.vitals.heart_rate for h in recent) / len(recent)
        avg_temp = sum(h.vitals.temperature for h in recent) / len(recent)
        
        return {
            "systolic": round(avg_systolic),
            "diastolic": round(avg_diastolic),
            "heart_rate": round(avg_hr),
            "temperature": round(avg_temp, 1),
            "sample_count": len(recent),
            "period_minutes": minutes
        }
    
    def set_threshold(self, name: str, value: float):
        if name in self.thresholds:
            self.thresholds[name] = value
            print(f"⚙️ Set threshold {name} = {value}")
    
    def get_status_summary(self) -> str:
        vitals = self.get_current_vitals()
        formatted = self.get_formatted_vitals()
        
        lines = [
            "📊 العلامات الحيوية الحالية:",
            "",
            f"🩸 ضغط الدم: {formatted['blood_pressure']['value']} {formatted['blood_pressure']['unit']}",
            f"   الحالة: {formatted['blood_pressure']['status']}",
            "",
            f"💓 نبضات القلب: {formatted['heart_rate']['value']} {formatted['heart_rate']['unit']}",
            f"   الحالة: {formatted['heart_rate']['status']}",
            "",
            f"🌡️ درجة الحرارة: {formatted['temperature']['value']} {formatted['temperature']['unit']}",
            f"   الحالة: {formatted['temperature']['status']}",
        ]
        
        return "\n".join(lines)
    
    def test(self):
        print("🧪 Testing Vital Signs Monitor...")
        
        self.start_monitoring()
        time.sleep(3)
        vitals = self.get_current_vitals()
        print(f"\n📊 Current vitals:")
        print(f"   BP: {vitals.systolic}/{vitals.diastolic} mmHg")
        print(f"   HR: {vitals.heart_rate} bpm")
        print(f"   Temp: {vitals.temperature}°C")
        
        formatted = self.get_formatted_vitals()
        print(f"\n📊 Formatted:")
        print(f"   BP Status: {formatted['blood_pressure']['status']}")
        print(f"   HR Status: {formatted['heart_rate']['status']}")
        print(f"   Temp Status: {formatted['temperature']['status']}")
        
        self.stop_monitoring()
        
        print("\n✅ Vital Signs Monitor test completed")


vital_signs_monitor = VitalSignsMonitor()


if __name__ == "__main__":
    vital_signs_monitor.test()
