import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Callable, Optional

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("⚠️ Schedule library not installed. pip install schedule")

sys.path.append('..')
from config import config


@dataclass
class Medication:
    name: str
    generic_name: str = ""
    dose: str = ""
    timing: str = ""
    purpose: str = ""
    schedule_times: list = field(default_factory=list)
    is_injection: bool = False
    storage_notes: str = ""
    is_active: bool = True
    
    last_taken: Optional[datetime] = None
    taken_today: bool = False
    
    calculated_dose: Optional[int] = None
    calculation_sugar: Optional[int] = None


@dataclass
class MedicationAlert:
    medication: Medication
    scheduled_time: str
    alert_time: datetime
    is_dismissed: bool = False
    is_taken: bool = False
    alert_type: str = "reminder"
    message: str = ""
    voice_message: str = ""


class MedicationReminder:
    
    def __init__(self):
        self.medications: list[Medication] = []
        self.alerts: list[MedicationAlert] = []
        self.callbacks: list[Callable[[MedicationAlert], None]] = []
        self._scheduler_running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._state_file = os.path.join(config.DATA_DIR, "meds_state.json")
        self._last_reset_date = datetime.now().date()
        self._load_medications()
        if SCHEDULE_AVAILABLE:
            schedule.every().day.at("00:00").do(self.reset_daily_status)
            print("✅ Daily reset scheduled for midnight.")
    
    def _save_state(self):
        state = {
            "last_reset_date": self._last_reset_date.isoformat(),
            "medications": {}
        }
        for med in self.medications:
            state["medications"][med.name] = {
                "taken_today": med.taken_today,
                "last_taken": med.last_taken.isoformat() if med.last_taken else None,
                "is_active": med.is_active,
                "calculated_dose": med.calculated_dose,
                "calculation_sugar": med.calculation_sugar
            }
        try:
            os.makedirs(os.path.dirname(self._state_file), exist_ok=True)
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"⚠️ Failed to save medication state: {e}")

    def _load_state(self):
        if not os.path.exists(self._state_file):
            return
            
        try:
            with open(self._state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            last_reset_date_str = state.get("last_reset_date")
            if last_reset_date_str:
                self._last_reset_date = datetime.fromisoformat(last_reset_date_str).date()
            
            meds_state = state.get("medications", {})
            for med in self.medications:
                if med.name in meds_state:
                    med_state = meds_state[med.name]
                    med.taken_today = med_state.get("taken_today", False)
                    med.is_active = med_state.get("is_active", True)
                    med.calculated_dose = med_state.get("calculated_dose")
                    med.calculation_sugar = med_state.get("calculation_sugar")
                    last_taken_str = med_state.get("last_taken")
                    if last_taken_str:
                        med.last_taken = datetime.fromisoformat(last_taken_str)
            print("✅ Medication state loaded.")
        except Exception as e:
            print(f"⚠️ Failed to load medication state: {e}")
            
    def _check_midnight_reset(self):
        current_date = datetime.now().date()
        if current_date > self._last_reset_date:
            print(f"🗓️ New day detected. Resetting daily status from {self._last_reset_date} to {current_date}.")
            self.reset_daily_status()
            self._last_reset_date = current_date
            self._save_state()
    
    def _load_medications(self):
        self.medications = [
            Medication(
                name="Glucophage XR 1000mg",
                generic_name="Metformin HCl",
                dose="قرص واحد",
                timing="بعد العشاء",
                purpose="تنظيم السكر",
                schedule_times=["21:00"],
                is_active=True
            ),
            Medication(
                name="Concor 5mg",
                generic_name="Bisoprolol",
                dose="قرص واحد",
                timing="صباحاً",
                purpose="تنظيم ضربات القلب",
                schedule_times=["08:00"],
                is_active=True
            ),
            Medication(
                name="Zestril 10mg",
                generic_name="Lisinopril",
                dose="قرص واحد",
                timing="مساءً",
                purpose="علاج الضغط",
                schedule_times=["20:00"],
                is_active=True
            ),
            Medication(
                name="Ator 20mg",
                generic_name="Atorvastatin",
                dose="قرص واحد",
                timing="قبل النوم",
                purpose="خفض الكوليسترول",
                schedule_times=["22:00"],
                is_active=True
            ),
            Medication(
                name="Aspirin Protect 100mg",
                generic_name="Acetylsalicylic Acid",
                dose="قرص واحد",
                timing="بعد الغداء",
                purpose="سيولة الدم",
                schedule_times=["14:00"],
                is_active=True
            ),
            Medication(
                name="Lantus SoloStar",
                generic_name="Insulin Glargine - حقنة أنسولين",
                dose="20 وحدة تحت الجلد",
                timing="قبل النوم",
                purpose="تنظيم السكر طويل المفعول",
                schedule_times=["22:30"],
                is_injection=True,
                storage_notes="في الثلاجة (2-8°C)",
                is_active=True
            )
        ]
        self._load_state()
        self._check_midnight_reset()
        print(f"✅ Loaded {len(self.medications)} medications and state")
    
    def get_medications(self) -> list[Medication]:
        return self.medications
    
    def get_active_medications(self) -> list[Medication]:
        return [m for m in self.medications if m.is_active]
    
    def add_medication(self, medication: Medication):
        self.medications.append(medication)
        self._save_state()
        print(f"➕ Added medication: {medication.name}")
    
    def remove_medication(self, medication_name: str):
        initial_count = len(self.medications)
        self.medications = [m for m in self.medications if m.name != medication_name]
        if len(self.medications) < initial_count:
            self._save_state()
            print(f"➖ Removed medication: {medication_name}")
            return True
        return False
    
    def mark_as_taken(self, medication_name: str):
        for med in self.medications:
            if med.name == medication_name:
                med.last_taken = datetime.now()
                med.taken_today = True
                self._save_state()
                print(f"✅ Marked as taken: {med.name}")
                return True
        return False
    
    def reset_daily_status(self):
        for med in self.medications:
            med.taken_today = False
            med.calculated_dose = None
            med.calculation_sugar = None
        self._save_state()
        print("🔄 Reset daily medication status and calculations")
    
    def get_due_medications(self) -> list[Medication]:
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        due_meds = []
        
        for med in self.medications:
            if not med.is_active or med.taken_today:
                continue
            
            for scheduled_time_str in med.schedule_times:
                try:
                    sched_hour, sched_minute = map(int, scheduled_time_str.split(':'))
                    
                    sched_total_minutes = sched_hour * 60 + sched_minute
                    current_total_minutes = current_hour * 60 + current_minute
                    
                    if sched_total_minutes <= current_total_minutes <= sched_total_minutes + 30:
                        due_meds.append(med)
                        break
                except ValueError:
                    print(f"⚠️ Invalid schedule time format for {med.name}: {scheduled_time_str}")
                    continue
        
        return due_meds
    
    def get_upcoming_medications(self, hours: int = 24) -> list[tuple[Medication, str]]:
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        upcoming = []
        
        for med in self.medications:
            for scheduled_time in med.schedule_times:
                try:
                    sched_hour, sched_minute = map(int, scheduled_time.split(':'))
                    sched_minutes = sched_hour * 60 + sched_minute
                    
                    diff = sched_minutes - current_minutes
                    
                    if diff < 0:
                        diff += 24 * 60
                    
                    if 0 <= diff <= hours * 60:
                        upcoming.append((med, scheduled_time, diff))
                except ValueError:
                    continue
        
        upcoming.sort(key=lambda x: x[2])
        return [(item[0], item[1]) for item in upcoming]
    
    def calculate_insulin_dose(self, blood_sugar: int, 
                               target_sugar: int = 100,
                               correction_factor: int = 50,
                               base_dose: int = 20) -> dict:
        if blood_sugar <= 0:
            return {
                "error": True,
                "message": "يرجى إدخال قراءة سكر صحيحة"
            }
        
        if blood_sugar < 70:
            return {
                "error": True,
                "warning": True,
                "message": "⚠️ انخفاض السكر! لا تأخذ الأنسولين الآن",
                "recommendation": "تناول سكريات سريعة وأعد القياس بعد 15 دقيقة"
            }
        
        if blood_sugar <= target_sugar + 30:
            correction_dose = 0
            status = "طبيعي"
            recommendation = "خذ الجرعة الأساسية فقط"
        else:
            difference = blood_sugar - target_sugar
            correction_dose = round(difference / correction_factor)
            
            if correction_dose <= 2:
                status = "مرتفع قليلاً"
            elif correction_dose <= 4:
                status = "مرتفع"
            else:
                status = "مرتفع جداً"
            
            recommendation = f"أضف {correction_dose} وحدة تصحيحية للجرعة الأساسية"
        
        total_dose = base_dose + correction_dose
        
        return {
            "error": False,
            "blood_sugar": blood_sugar,
            "blood_sugar_status": status,
            "target_sugar": target_sugar,
            "base_dose": base_dose,
            "correction_dose": correction_dose,
            "total_dose": total_dose,
            "recommendation": recommendation,
            "warning": blood_sugar > 300,
            "warning_message": "⚠️ السكر مرتفع جداً! استشر الطبيب" if blood_sugar > 300 else ""
        }
    
    def add_callback(self, callback: Callable[[MedicationAlert], None]):
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, alert: MedicationAlert):
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"❌ Callback error: {e}")
    
    def _scheduler_loop(self):
        last_notified = {}
        
        while self._scheduler_running:
            self._check_midnight_reset()
            current_time = time.time()
            
            now_dt = datetime.now()
            if now_dt.second == 0: 
                due_meds = self.get_due_medications()
                for med in due_meds:
                    last_time = last_notified.get(med.name, 0)
                    if current_time - last_time > 300:
                        display_msg = f"حان موعد أخذ دواء {med.name} ({med.dose})"
                        voice_msg = f"حان وقت العلاج، {med.name.split(' ')[0]}"
                        
                        if med.name == "Lantus SoloStar":
                            try:
                                sugar = med.calculation_sugar
                                dose = med.calculated_dose
                                
                                if not dose:
                                    from modules.vital_signs import vital_signs_monitor
                                    sugar = vital_signs_monitor.manual_readings.get("sugar", 0)
                                    if sugar > 0:
                                        calc = self.calculate_insulin_dose(int(sugar))
                                        if not calc.get("error"):
                                            dose = calc['total_dose']
                                
                                if dose and sugar:
                                    display_msg = f"حان وقت جرعة الأنسولين\nالجرعة المحسوبة: {dose} وحدة\n(بناءً على سكر {sugar})"
                                    voice_msg = f"حان وقت جرعة الأنسولين، الجرعة المطلوبة هي {dose} وحدة"
                            except Exception as e:
                                print(f"⚠️ Error calculating insulin for alert: {e}")

                        alert = MedicationAlert(
                            medication=med,
                            scheduled_time=med.schedule_times[0] if med.schedule_times else "N/A",
                            alert_time=now_dt,
                            alert_type="schedule",
                            message=display_msg,
                            voice_message=voice_msg
                        )
                        
                        self._notify_callbacks(alert)
                        last_notified[med.name] = current_time
            
            if SCHEDULE_AVAILABLE:
                try:
                    schedule.run_pending()
                except Exception as e:
                    print(f"⚠️ Scheduler error: {e}")
            
            time.sleep(1)
    
    def start_scheduler(self):
        if not self._scheduler_running:
            self._scheduler_running = True
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop, 
                daemon=True
            )
            self._scheduler_thread.start()
            print("⏰ Medication scheduler started")
    
    def stop_scheduler(self):
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=2)
        print("⏹️ Medication scheduler stopped")
    
    def get_schedule_display(self) -> str:
        lines = ["📋 جدول الأدوية اليومي:\n"]
        
        time_groups = {}
        for med in self.get_active_medications():
            for t in med.schedule_times:
                if t not in time_groups:
                    time_groups[t] = []
                time_groups[t].append(med)
        
        for t in sorted(time_groups.keys()):
            lines.append(f"\n🕐 {t}:")
            for med in time_groups[t]:
                status = "✅" if med.taken_today else "⏳"
                icon = "💉" if med.is_injection else "💊"
                lines.append(f"   {status} {icon} {med.name} - {med.dose}")
        
        return "\n".join(lines)
    
    def test(self):
        print("🧪 Testing Medication Reminder...")
        
        print(f"\n📋 Loaded {len(self.medications)} medications:")
        for med in self.medications:
            icon = "💉" if med.is_injection else "💊"
            print(f"   {icon} {med.name} - {med.timing}")
        
        due = self.get_due_medications()
        print(f"\n⏰ Due now: {len(due)} medications")
        
        upcoming = self.get_upcoming_medications(4)
        print(f"📅 Coming up (4h): {len(upcoming)} medications")
        
        print("\n💉 Insulin calculation test:")
        result = self.calculate_insulin_dose(200)
        print(f"   Blood sugar: {result['blood_sugar']} mg/dL")
        print(f"   Status: {result['blood_sugar_status']}")
        print(f"   Total dose: {result['total_dose']} units")
        print(f"   {result['recommendation']}")
        
        print("\n✅ Medication Reminder test completed")


medication_reminder = MedicationReminder()


if __name__ == "__main__":
    medication_reminder.test()
