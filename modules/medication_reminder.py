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
    
    def _save_state(self):
        state = {"last_reset_date": self._last_reset_date.isoformat(), "medications": {}}
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
        except:
            pass

    def _load_state(self):
        if not os.path.exists(self._state_file): return
        try:
            with open(self._state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            last_reset = state.get("last_reset_date")
            if last_reset: self._last_reset_date = datetime.fromisoformat(last_reset).date()
            meds_state = state.get("medications", {})
            for med in self.medications:
                if med.name in meds_state:
                    ms = meds_state[med.name]
                    med.taken_today = ms.get("taken_today", False)
                    med.is_active = ms.get("is_active", True)
                    med.calculated_dose = ms.get("calculated_dose")
                    med.calculation_sugar = ms.get("calculation_sugar")
                    lt = ms.get("last_taken")
                    if lt: med.last_taken = datetime.fromisoformat(lt)
        except:
            pass
            
    def _check_midnight_reset(self):
        current_date = datetime.now().date()
        if current_date > self._last_reset_date:
            self.reset_daily_status()
            self._last_reset_date = current_date
            self._save_state()
    
    def _load_medications(self):
        self.medications = [
            Medication(name="Glucophage XR 1000mg", generic_name="Metformin HCl", dose="1 tablet",
                       timing="After dinner", purpose="Blood sugar regulation", schedule_times=["21:00"]),
            Medication(name="Concor 5mg", generic_name="Bisoprolol", dose="1 tablet",
                       timing="Morning", purpose="Heart rate regulation", schedule_times=["08:00"]),
            Medication(name="Zestril 10mg", generic_name="Lisinopril", dose="1 tablet",
                       timing="Evening", purpose="Blood pressure treatment", schedule_times=["20:00"]),
            Medication(name="Ator 20mg", generic_name="Atorvastatin", dose="1 tablet",
                       timing="Before bed", purpose="Cholesterol lowering", schedule_times=["22:00"]),
            Medication(name="Aspirin Protect 100mg", generic_name="Acetylsalicylic Acid", dose="1 tablet",
                       timing="After lunch", purpose="Blood thinning", schedule_times=["14:00"]),
            Medication(name="Lantus SoloStar", generic_name="Insulin Glargine", dose="20 units subcutaneous",
                       timing="Before bed", purpose="Long-acting insulin", schedule_times=["22:30"],
                       is_injection=True, storage_notes="Refrigerate (2-8°C)"),
        ]
        self._load_state()
        self._check_midnight_reset()
    
    def get_medications(self): return self.medications
    def get_active_medications(self): return [m for m in self.medications if m.is_active]
    
    def add_medication(self, medication: Medication):
        self.medications.append(medication)
        self._save_state()
    
    def remove_medication(self, medication_name: str):
        initial = len(self.medications)
        self.medications = [m for m in self.medications if m.name != medication_name]
        if len(self.medications) < initial:
            self._save_state()
            return True
        return False
    
    def mark_as_taken(self, medication_name: str):
        for med in self.medications:
            if med.name == medication_name:
                med.last_taken = datetime.now()
                med.taken_today = True
                self._save_state()
                return True
        return False
    
    def reset_daily_status(self):
        for med in self.medications:
            med.taken_today = False
            med.calculated_dose = None
            med.calculation_sugar = None
        self._save_state()
    
    def get_due_medications(self) -> list[Medication]:
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        due = []
        for med in self.medications:
            if not med.is_active or med.taken_today: continue
            for st in med.schedule_times:
                try:
                    h, m = map(int, st.split(':'))
                    sched = h * 60 + m
                    if sched <= current_minutes <= sched + 30:
                        due.append(med)
                        break
                except: continue
        return due
    
    def get_upcoming_medications(self, hours: int = 24) -> list[tuple[Medication, str]]:
        current_minutes = datetime.now().hour * 60 + datetime.now().minute
        upcoming = []
        for med in self.medications:
            for st in med.schedule_times:
                try:
                    h, m = map(int, st.split(':'))
                    diff = (h * 60 + m) - current_minutes
                    if diff < 0: diff += 24 * 60
                    if 0 <= diff <= hours * 60:
                        upcoming.append((med, st, diff))
                except: continue
        upcoming.sort(key=lambda x: x[2])
        return [(i[0], i[1]) for i in upcoming]
    
    def calculate_insulin_dose(self, blood_sugar: int, target_sugar: int = 100,
                               correction_factor: int = 50, base_dose: int = 20) -> dict:
        if blood_sugar <= 0:
            return {"error": True, "message": "Please enter a valid blood sugar reading"}
        if blood_sugar < 70:
            return {"error": True, "warning": True,
                    "message": "⚠️ Low blood sugar! Do not take insulin now",
                    "recommendation": "Consume fast-acting sugar and recheck in 15 minutes"}
        if blood_sugar <= target_sugar + 30:
            correction_dose = 0
            status = "Normal"
            recommendation = "Take base dose only"
        else:
            difference = blood_sugar - target_sugar
            correction_dose = round(difference / correction_factor)
            if correction_dose <= 2: status = "Slightly High"
            elif correction_dose <= 4: status = "High"
            else: status = "Very High"
            recommendation = f"Add {correction_dose} correction units to base dose"
        total_dose = base_dose + correction_dose
        return {
            "error": False, "blood_sugar": blood_sugar, "blood_sugar_status": status,
            "target_sugar": target_sugar, "base_dose": base_dose,
            "correction_dose": correction_dose, "total_dose": total_dose,
            "recommendation": recommendation,
            "warning": blood_sugar > 300,
            "warning_message": "⚠️ Blood sugar very high! Consult your doctor" if blood_sugar > 300 else ""
        }
    
    def add_callback(self, callback): self.callbacks.append(callback)
    
    def _notify_callbacks(self, alert):
        for cb in self.callbacks:
            try: cb(alert)
            except: pass
    
    def _scheduler_loop(self):
        last_notified = {}
        while self._scheduler_running:
            self._check_midnight_reset()
            current_time = time.time()
            now_dt = datetime.now()
            if now_dt.second == 0:
                for med in self.get_due_medications():
                    if current_time - last_notified.get(med.name, 0) > 300:
                        display_msg = f"Time for {med.name}\nDose: {med.dose}"
                        voice_msg = f"حان وقت العلاج، {med.name.split(' ')[0]}"
                        if med.name == "Lantus SoloStar":
                            try:
                                dose = med.calculated_dose
                                sugar = med.calculation_sugar
                                if not dose:
                                    from modules.vital_signs import vital_signs_monitor
                                    sugar = vital_signs_monitor.manual_readings.get("sugar", 0)
                                    if sugar > 0:
                                        calc = self.calculate_insulin_dose(int(sugar))
                                        if not calc.get("error"): dose = calc['total_dose']
                                if dose and sugar:
                                    display_msg = f"Insulin dose time\nCalculated dose: {dose} units\n(Based on sugar {sugar})"
                                    voice_msg = f"حان وقت جرعة الأنسولين، الجرعة المطلوبة هي {dose} وحدة"
                            except: pass
                        alert = MedicationAlert(medication=med, scheduled_time=med.schedule_times[0] if med.schedule_times else "N/A",
                            alert_time=now_dt, alert_type="schedule", message=display_msg, voice_message=voice_msg)
                        self._notify_callbacks(alert)
                        last_notified[med.name] = current_time
            if SCHEDULE_AVAILABLE:
                try: schedule.run_pending()
                except: pass
            time.sleep(1)
    
    def start_scheduler(self):
        if not self._scheduler_running:
            self._scheduler_running = True
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()
    
    def stop_scheduler(self):
        self._scheduler_running = False
        if self._scheduler_thread: self._scheduler_thread.join(timeout=2)
    
    def test(self): return True


medication_reminder = MedicationReminder()

if __name__ == "__main__":
    medication_reminder.test()
