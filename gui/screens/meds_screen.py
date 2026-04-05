"""
AI Robot Operating System - Medications Screen
Screen for managing medications, reminders, and insulin calculations.
"""

import customtkinter as ctk
from typing import Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS
from core.arabic_utils import fix_arabic as _
from modules.medication_reminder import medication_reminder, Medication
from modules.vital_signs import vital_signs_monitor


class MedicationCard(ctk.CTkFrame):
    def __init__(self, master, medication: Medication, on_take_callback=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"],
                         border_width=2, border_color=COLORS["border_light"], **kwargs)
        self.medication = medication
        self.on_take = on_take_callback
        self._create_layout()
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        icon = "💉" if self.medication.is_injection else "💊"
        ctk.CTkLabel(self, text=icon, font=(FONTS["family"], 28), width=50).grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        ctk.CTkLabel(self, text=self.medication.name, font=(FONTS["family_en"], FONTS["size_md"], "bold"),
                     text_color=COLORS["text_primary"], anchor="w").grid(row=0, column=1, sticky="w", padx=10, pady=(10, 0))
        ctk.CTkLabel(self, text=f"{self.medication.dose} - {self.medication.timing}",
                     font=(FONTS["family_en"], FONTS["size_sm"]), text_color=COLORS["text_muted"],
                     anchor="w").grid(row=1, column=1, sticky="w", padx=10, pady=(0, 10))
        ctk.CTkLabel(self, text=self.medication.purpose, font=(FONTS["family_en"], FONTS["size_xs"]),
                     text_color=COLORS["text_secondary"], anchor="w").grid(row=2, column=1, sticky="w", padx=10, pady=(0, 10))
        if self.medication.taken_today:
            ctk.CTkLabel(self, text="✅", font=(FONTS["family"], 24), text_color=COLORS["success"]).grid(row=0, column=2, rowspan=3, padx=15)
        else:
            self.take_btn = ctk.CTkButton(self, text="Done", font=(FONTS["family_en"], FONTS["size_sm"]), width=60, height=35,
                                          fg_color=COLORS["success"], hover_color=COLORS["success_hover"], command=self._mark_taken)
            self.take_btn.grid(row=0, column=2, rowspan=3, padx=15)
    
    def _mark_taken(self):
        medication_reminder.mark_as_taken(self.medication.name)
        self.medication.taken_today = True
        self.take_btn.destroy()
        ctk.CTkLabel(self, text="✅", font=(FONTS["family"], 24), text_color=COLORS["success"]).grid(row=0, column=2, rowspan=3, padx=15)
        if self.on_take:
            self.on_take(self.medication)


class InsulinCalculator(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"], **kwargs)
        self._create_layout()
    
    def _create_layout(self):
        ctk.CTkLabel(self, text="💉 Insulin Dose Calculator", font=(FONTS["family_en"], FONTS["size_lg"], "bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(self, text="Calculate dose using latest reading", font=(FONTS["family_en"], FONTS["size_sm"]),
                     text_color=COLORS["text_secondary"], anchor="w").pack(anchor="w", padx=20, pady=(0, 15))
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(sf, text="Blood Sugar (mg/dL):", font=(FONTS["family_en"], FONTS["size_sm"]),
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=10)
        self.sugar_entry = ctk.CTkEntry(sf, placeholder_text="e.g. 150", font=(FONTS["family_en"], FONTS["size_md"]),
                                        width=120, height=40, fg_color=COLORS["bg_input"], border_color=COLORS["border"], corner_radius=RADIUS["md"])
        self.sugar_entry.pack(side="left")
        af = ctk.CTkFrame(self, fg_color="transparent")
        af.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(af, text="Calculate Dose", font=(FONTS["family_en"], FONTS["size_md"], "bold"),
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], width=120, height=40,
                      command=self._calculate).pack(side="left")
        self.result_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["lg"])
        self.result_frame.pack(fill="x", padx=20, pady=(10, 20))
        self.result_label = ctk.CTkLabel(self.result_frame, text="Enter blood sugar to calculate dose",
                                         font=(FONTS["family_en"], FONTS["size_md"]), text_color=COLORS["text_muted"], anchor="center")
        self.result_label.pack(pady=20)
    
    def _calculate(self):
        manual_val = self.sugar_entry.get().strip()
        if manual_val:
            try:
                sugar_val = int(manual_val)
                vital_signs_monitor.set_manual_reading("sugar", sugar_val)
            except ValueError:
                self.result_label.configure(text="❌ Please enter a valid number", text_color=COLORS["danger"])
                return
        else:
            try: sugar_val = vital_signs_monitor.manual_readings.get("sugar", 0)
            except: sugar_val = 0
        if not sugar_val or sugar_val <= 0:
            self.result_label.configure(text="❌ No sugar reading. Enter value above.", text_color=COLORS["danger"])
            return
        result = medication_reminder.calculate_insulin_dose(int(sugar_val))
        if result.get("error"):
            self.result_label.configure(text=result.get("message", "Error"), text_color=COLORS["danger"])
            return
        for med in medication_reminder.medications:
            if med.name == "Lantus SoloStar":
                med.calculated_dose = result['total_dose']
                med.calculation_sugar = result['blood_sugar']
                medication_reminder._save_state()
                break
        lines = [f"📊 Blood Sugar: {result['blood_sugar']} mg/dL ({result['blood_sugar_status']})", "",
                 f"💉 Base Dose: {result['base_dose']} units", f"➕ Correction: {result['correction_dose']} units",
                 "━━━━━━━━━━━━━━━━━", f"📌 Total Dose: {result['total_dose']} units", "", f"💡 {result['recommendation']}"]
        if result.get("warning"):
            lines.extend(["", result.get("warning_message", "")])
        self.result_label.configure(text="\n".join(lines), text_color=COLORS["success"] if not result.get("warning") else COLORS["warning"])


class MedsScreen(ctk.CTkFrame):
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app_controller
        self._create_layout()
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"], scrollbar_button_hover_color=COLORS["primary"])
        self.scroll_container.grid(row=0, column=0, sticky="nsew")
        self.scroll_container.grid_columnconfigure(0, weight=1, uniform="meds")
        self.scroll_container.grid_columnconfigure(1, weight=1, uniform="meds")
        tf = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        tf.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(tf, text="💊 Medications & Treatments", font=(FONTS["family_en"], FONTS["size_2xl"], "bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(tf, text="Manage medications, reminders & insulin calculator", font=(FONTS["family_en"], FONTS["size_sm"]),
                     text_color=COLORS["text_secondary"], anchor="w").pack(anchor="w")
        self._create_medications_list()
        self._create_insulin_section()
    
    def _create_medications_list(self):
        self.meds_frame = ctk.CTkFrame(self.scroll_container, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"])
        self.meds_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 5), pady=10)
        hf = ctk.CTkFrame(self.meds_frame, fg_color="transparent")
        hf.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(hf, text="📋 Medication List", font=(FONTS["family_en"], FONTS["size_lg"], "bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(side="left")
        meds = medication_reminder.get_active_medications()
        taken = sum(1 for m in meds if m.taken_today)
        self.stats_label = ctk.CTkLabel(hf, text=f"✅ {taken}/{len(meds)} completed",
                                        font=(FONTS["family_en"], FONTS["size_sm"]), text_color=COLORS["success"])
        self.stats_label.pack(side="right")
        self.meds_list = ctk.CTkScrollableFrame(self.meds_frame, fg_color="transparent")
        self.meds_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self._populate_medications()
    
    def _populate_medications(self):
        for w in self.meds_list.winfo_children(): w.destroy()
        for med in medication_reminder.get_active_medications():
            MedicationCard(self.meds_list, medication=med, on_take_callback=self._on_medication_taken).pack(fill="x", pady=5)
    
    def _on_medication_taken(self, medication):
        meds = medication_reminder.get_active_medications()
        taken = sum(1 for m in meds if m.taken_today)
        self.stats_label.configure(text=f"✅ {taken}/{len(meds)} completed")
    
    def _create_insulin_section(self):
        self.insulin_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.insulin_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 20), pady=10)
        self.calculator = InsulinCalculator(self.insulin_frame)
        self.calculator.pack(fill="x", pady=(0, 10))
        self._create_schedule_display()
    
    def _create_schedule_display(self):
        self.schedule_frame = ctk.CTkFrame(self.insulin_frame, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"])
        self.schedule_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.schedule_frame, text="📅 Schedule", font=(FONTS["family_en"], FONTS["size_lg"], "bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(anchor="w", padx=20, pady=(15, 10))
        self.schedule_list = ctk.CTkScrollableFrame(self.schedule_frame, fg_color="transparent")
        self.schedule_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self._populate_schedule()
    
    def _populate_schedule(self):
        for w in self.schedule_list.winfo_children(): w.destroy()
        upcoming = medication_reminder.get_upcoming_medications(24)
        if not upcoming:
            ctk.CTkLabel(self.schedule_list, text="No upcoming medications in 24h",
                         font=(FONTS["family_en"], FONTS["size_md"]), text_color=COLORS["text_muted"]).pack(pady=20)
            return
        for med, t in upcoming:
            f = ctk.CTkFrame(self.schedule_list, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["lg"])
            f.pack(fill="x", pady=5)
            icon = "💉" if med.is_injection else "💊"
            si = "✅" if med.taken_today else "⏳"
            sc = COLORS["success"] if med.taken_today else COLORS["text_muted"]
            ctk.CTkLabel(f, text=t, font=(FONTS["family_en"], FONTS["size_md"], "bold"), text_color=COLORS["primary"], width=60).pack(side="left", padx=5, pady=8)
            ctk.CTkLabel(f, text=f"{icon} {med.name}", font=(FONTS["family_en"], FONTS["size_sm"]), text_color=COLORS["text_primary"], anchor="w").pack(side="left", fill="x", expand=True, pady=8, padx=5)
            ctk.CTkLabel(f, text=si, font=(FONTS["family"], 16), text_color=sc, width=30).pack(side="right", padx=10)
    
    def on_hide(self): pass
    def on_show(self):
        self._populate_medications()
        self._populate_schedule()
