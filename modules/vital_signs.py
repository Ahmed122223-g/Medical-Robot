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
            "bp_systolic_high": 140, "bp_systolic_low": 90,
            "bp_diastolic_high": 90, "bp_diastolic_low": 60,
            "hr_high": 100, "hr_low": 60,
            "temp_high": 38.0, "temp_low": 35.5,
            "sugar_high": 140, "sugar_low": 70
        }
        self.manual_readings = {"sugar": 0, "weight": 0}
        self.arduino.add_callback(self._on_vitals_received)
    
    def _on_vitals_received(self, vitals: VitalSigns):
        self._add_to_history(vitals)
        self._check_alerts(vitals)
        for callback in self.callbacks:
            try: callback(vitals)
            except: pass
    
    def _add_to_history(self, vitals: VitalSigns):
        self.history.append(VitalSignsHistory(vitals=vitals, recorded_at=datetime.now()))
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
    
    def _check_alerts(self, vitals: VitalSigns):
        alerts = []
        if vitals.systolic >= self.thresholds["bp_systolic_high"]:
            alerts.append(("danger", f"⚠️ High BP: {vitals.systolic}/{vitals.diastolic} mmHg"))
        elif vitals.systolic <= self.thresholds["bp_systolic_low"]:
            alerts.append(("warning", f"⬇️ Low BP: {vitals.systolic}/{vitals.diastolic} mmHg"))
        if vitals.diastolic >= self.thresholds["bp_diastolic_high"]:
            alerts.append(("danger", f"⚠️ High diastolic: {vitals.diastolic} mmHg"))
        if vitals.heart_rate >= self.thresholds["hr_high"]:
            alerts.append(("warning", f"💓 Fast heart rate: {vitals.heart_rate} bpm"))
        elif vitals.heart_rate <= self.thresholds["hr_low"]:
            alerts.append(("info", f"💓 Slow heart rate: {vitals.heart_rate} bpm"))
        if vitals.temperature >= self.thresholds["temp_high"]:
            alerts.append(("danger", f"🌡️ High temperature: {vitals.temperature}°C"))
        elif vitals.temperature <= self.thresholds["temp_low"]:
            alerts.append(("warning", f"🌡️ Low temperature: {vitals.temperature}°C"))
        for level, message in alerts:
            for callback in self.alert_callbacks:
                try: callback(level, message)
                except: pass
    
    def start_monitoring(self):
        if not self._is_monitoring:
            self._is_monitoring = True
            self.arduino.start_reading()
    
    def stop_monitoring(self):
        if self._is_monitoring:
            self._is_monitoring = False
            self.arduino.stop_reading()
    
    def add_callback(self, callback): self.callbacks.append(callback)
    def add_alert_callback(self, callback): self.alert_callbacks.append(callback)
    def get_current_vitals(self) -> VitalSigns: return self.arduino.get_current_vitals()
    
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
        sugar_status = "Normal"
        if sugar_val > self.thresholds["sugar_high"]: sugar_status = "High"
        elif sugar_val < self.thresholds["sugar_low"]: sugar_status = "Low"
        if sugar_val == 0: sugar_status = "Not entered"
        return {
            "blood_pressure": format_blood_pressure(vitals.systolic, vitals.diastolic),
            "heart_rate": format_heart_rate(vitals.heart_rate),
            "temperature": format_temperature(vitals.temperature),
            "sugar": {"value": str(int(sugar_val)) if sugar_val > 0 else "--", "unit": "mg/dL", "status": sugar_status},
            "weight": {"value": str(self.manual_readings["weight"]) if self.manual_readings["weight"] > 0 else "--", "unit": "kg", "status": "Stable"},
            "timestamp": vitals.timestamp, "is_valid": vitals.is_valid
        }
    
    def get_history(self, count: int = 10): return self.history[-count:]
    
    def get_averages(self, minutes: int = 30) -> dict:
        cutoff_time = time.time() - (minutes * 60)
        recent = [h for h in self.history if h.vitals.timestamp >= cutoff_time]
        if not recent: return None
        return {
            "systolic": round(sum(h.vitals.systolic for h in recent) / len(recent)),
            "diastolic": round(sum(h.vitals.diastolic for h in recent) / len(recent)),
            "heart_rate": round(sum(h.vitals.heart_rate for h in recent) / len(recent)),
            "temperature": round(sum(h.vitals.temperature for h in recent) / len(recent), 1),
            "sample_count": len(recent), "period_minutes": minutes
        }
    
    def set_threshold(self, name: str, value: float):
        if name in self.thresholds: self.thresholds[name] = value
    
    def get_status_summary(self) -> str:
        formatted = self.get_formatted_vitals()
        return (f"📊 Current Vital Signs:\n\n"
                f"🩸 Blood Pressure: {formatted['blood_pressure']['value']} {formatted['blood_pressure']['unit']}\n"
                f"   Status: {formatted['blood_pressure']['status']}\n\n"
                f"💓 Heart Rate: {formatted['heart_rate']['value']} {formatted['heart_rate']['unit']}\n"
                f"   Status: {formatted['heart_rate']['status']}\n\n"
                f"🌡️ Temperature: {formatted['temperature']['value']} {formatted['temperature']['unit']}\n"
                f"   Status: {formatted['temperature']['status']}")
    
    def test(self):
        self.start_monitoring()
        time.sleep(3)
        self.stop_monitoring()
        return True


vital_signs_monitor = VitalSignsMonitor()

if __name__ == "__main__":
    vital_signs_monitor.test()
