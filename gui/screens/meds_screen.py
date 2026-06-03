"""
AI Robot Operating System - Medications Screen
Screen for managing medications, reminders, and insulin calculations.
Fully responsive - 3 vertical sections, no outer scroll.
"""

import customtkinter as ctk
from typing import Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS, responsive
from core.arabic_utils import fix_arabic as _
from modules.medication_reminder import medication_reminder, Medication
from modules.vital_signs import vital_signs_monitor


class MedicationCard(ctk.CTkFrame):
    def __init__(self, master, medication: Medication, on_take_callback=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=RADIUS["md"],
                         border_width=1, border_color=COLORS["border_light"], **kwargs)
        self.medication = medication
        self.on_take = on_take_callback
        self._create_layout()
    
    def _create_layout(self):
        r = responsive
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        icon = "💉" if self.medication.is_injection else "💊"
        ctk.CTkLabel(self, text=icon, font=r.font_ar(base_size=18), width=r.size(35)).grid(
            row=0, column=0, rowspan=2, padx=r.pad(6), pady=r.pad(4))
        ctk.CTkLabel(self, text=self.medication.name, font=r.font(base_size=11, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w").grid(
            row=0, column=1, sticky="w", padx=r.pad(4), pady=(r.pad(4), 0))
        
        info_text = f"{self.medication.dose} - {self.medication.timing}"
        ctk.CTkLabel(self, text=info_text,
                     font=r.font(base_size=9), text_color=COLORS["text_muted"],
                     anchor="w").grid(row=1, column=1, sticky="w", padx=r.pad(4), pady=(0, r.pad(4)))
        
        if self.medication.taken_today:
            ctk.CTkLabel(self, text="✅", font=r.font_ar(base_size=16), text_color=COLORS["success"]).grid(
                row=0, column=2, rowspan=2, padx=r.pad(8))
        else:
            self.take_btn = ctk.CTkButton(self, text="Done", font=r.font(base_size=9),
                                          width=r.size(45), height=r.size(28),
                                          fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                                          command=self._mark_taken)
            self.take_btn.grid(row=0, column=2, rowspan=2, padx=r.pad(8))
    
    def _mark_taken(self):
        medication_reminder.mark_as_taken(self.medication.name)
        self.medication.taken_today = True
        self.take_btn.destroy()
        r = responsive
        ctk.CTkLabel(self, text="✅", font=r.font_ar(base_size=16), text_color=COLORS["success"]).grid(
            row=0, column=2, rowspan=2, padx=r.pad(8))
        if self.on_take:
            self.on_take(self.medication)


class InsulinCalculator(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"],
                         border_width=1, border_color=COLORS["border_light"], **kwargs)
        self._create_layout()
    
    def _create_layout(self):
        r = responsive
        
        # Title
        ctk.CTkLabel(self, text="💉 Insulin Dose Calculator",
                     font=r.font(base_size=13, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(
            anchor="w", padx=r.pad(12), pady=(r.pad(8), r.pad(2)))
        
        # Input row
        sf = ctk.CTkFrame(self, fg_color="transparent")
        sf.pack(fill="x", padx=r.pad(12), pady=r.pad(4))
        
        ctk.CTkLabel(sf, text="Blood Sugar (mg/dL):",
                     font=r.font(base_size=10),
                     text_color=COLORS["text_secondary"]).pack(side="left", padx=r.pad(4))
        
        self.sugar_entry = ctk.CTkEntry(sf, placeholder_text="e.g. 150",
                                        font=r.font(base_size=11),
                                        width=r.size(100), height=r.size(32),
                                        fg_color=COLORS["bg_input"],
                                        border_color=COLORS["border"],
                                        corner_radius=RADIUS["md"])
        self.sugar_entry.pack(side="left", padx=r.pad(4))
        
        ctk.CTkButton(sf, text="Calculate",
                      font=r.font(base_size=10, weight="bold"),
                      fg_color=COLORS["secondary"],
                      hover_color=COLORS["secondary_hover"],
                      width=r.size(80), height=r.size(32),
                      command=self._calculate).pack(side="left", padx=r.pad(4))
        
        # Result
        self.result_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["md"])
        self.result_frame.pack(fill="both", expand=True, padx=r.pad(12), pady=(r.pad(4), r.pad(8)))
        
        self.result_label = ctk.CTkLabel(self.result_frame,
                                         text="Enter blood sugar to calculate dose",
                                         font=r.font(base_size=10),
                                         text_color=COLORS["text_muted"], anchor="center")
        self.result_label.pack(expand=True, pady=r.pad(8))
    
    def _calculate(self):
        r = responsive
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
        lines = [
            f"📊 Blood Sugar: {result['blood_sugar']} mg/dL ({result['blood_sugar_status']})", "",
            f"💉 Base Dose: {result['base_dose']} units",
            f"➕ Correction: {result['correction_dose']} units",
            "━━━━━━━━━━━━━━━━━",
            f"📌 Total Dose: {result['total_dose']} units", "",
            f"💡 {result['recommendation']}"
        ]
        if result.get("warning"):
            lines.extend(["", result.get("warning_message", "")])
        self.result_label.configure(
            text="\n".join(lines),
            font=r.font(base_size=10),
            text_color=COLORS["success"] if not result.get("warning") else COLORS["warning"]
        )


class MedsScreen(ctk.CTkFrame):
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app_controller
        self._last_w = 0
        self._last_h = 0
        self._create_layout()
        self.bind("<Configure>", self._on_resize)
    
    def _on_resize(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if abs(w - self._last_w) < 30 and abs(h - self._last_h) < 30:
            return
        self._last_w = w
        self._last_h = h
        self._update_responsive()
    
    def _update_responsive(self):
        r = responsive
        self.title_label.configure(font=r.font(base_size=18, weight="bold"))
        self.subtitle_label.configure(font=r.font(base_size=10))
        self.schedule_title.configure(font=r.font(base_size=13, weight="bold"))
        self.meds_title_label.configure(font=r.font(base_size=13, weight="bold"))
        self.stats_label.configure(font=r.font(base_size=9))
    
    def _create_layout(self):
        r = responsive
        
        # Main grid - 3 vertical sections, no outer scroll
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)   # Title
        self.grid_rowconfigure(1, weight=3)   # Insulin Calculator ~30%
        self.grid_rowconfigure(2, weight=3)   # Schedule ~30%
        self.grid_rowconfigure(3, weight=4)   # Medications ~40%
        
        # Title
        tf = ctk.CTkFrame(self, fg_color="transparent")
        tf.grid(row=0, column=0, sticky="ew", padx=r.pad(15), pady=(r.pad(8), r.pad(4)))
        
        self.title_label = ctk.CTkLabel(tf, text="💊 Medications & Treatments",
                     font=r.font(base_size=18, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w")
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(tf, text="Manage medications, reminders & insulin calculator",
                     font=r.font(base_size=10),
                     text_color=COLORS["text_secondary"], anchor="w")
        self.subtitle_label.pack(anchor="w")
        
        # Section 1: Insulin Calculator
        self._create_insulin_section()
        
        # Section 2: Schedule Table
        self._create_schedule_section()
        
        # Section 3: Medication Status
        self._create_medications_section()
    
    def _create_insulin_section(self):
        r = responsive
        self.calculator = InsulinCalculator(self)
        self.calculator.grid(row=1, column=0, sticky="nsew", padx=r.pad(15), pady=(0, r.pad(4)))
    
    def _create_schedule_section(self):
        r = responsive
        self.schedule_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                                           corner_radius=RADIUS["lg"],
                                           border_width=1, border_color=COLORS["border_light"])
        self.schedule_frame.grid(row=2, column=0, sticky="nsew", padx=r.pad(15), pady=(0, r.pad(4)))
        
        self.schedule_title = ctk.CTkLabel(self.schedule_frame, text="📅 Schedule",
                     font=r.font(base_size=13, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w")
        self.schedule_title.pack(anchor="w", padx=r.pad(12), pady=(r.pad(8), r.pad(4)))
        
        self.schedule_list = ctk.CTkScrollableFrame(self.schedule_frame, fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
            scrollbar_button_hover_color=COLORS["primary"])
        self.schedule_list.pack(fill="both", expand=True, padx=r.pad(8), pady=(0, r.pad(8)))
        
        self._populate_schedule()
    
    def _create_medications_section(self):
        r = responsive
        self.meds_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                                       corner_radius=RADIUS["lg"],
                                       border_width=1, border_color=COLORS["border_light"])
        self.meds_frame.grid(row=3, column=0, sticky="nsew", padx=r.pad(15), pady=(0, r.pad(8)))
        
        hf = ctk.CTkFrame(self.meds_frame, fg_color="transparent")
        hf.pack(fill="x", padx=r.pad(12), pady=(r.pad(8), r.pad(4)))
        
        self.meds_title_label = ctk.CTkLabel(hf, text="📋 Medication List",
                     font=r.font(base_size=13, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w")
        self.meds_title_label.pack(side="left")
        
        meds = medication_reminder.get_active_medications()
        taken = sum(1 for m in meds if m.taken_today)
        self.stats_label = ctk.CTkLabel(hf, text=f"✅ {taken}/{len(meds)} completed",
                                        font=r.font(base_size=9),
                                        text_color=COLORS["success"])
        self.stats_label.pack(side="right")
        
        self.meds_list = ctk.CTkScrollableFrame(self.meds_frame, fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
            scrollbar_button_hover_color=COLORS["primary"])
        self.meds_list.pack(fill="both", expand=True, padx=r.pad(8), pady=(0, r.pad(8)))
        
        self._populate_medications()
    
    def _populate_medications(self):
        for w in self.meds_list.winfo_children(): w.destroy()
        r = responsive
        for med in medication_reminder.get_active_medications():
            MedicationCard(self.meds_list, medication=med,
                          on_take_callback=self._on_medication_taken).pack(fill="x", pady=r.pad(2))
    
    def _on_medication_taken(self, medication):
        meds = medication_reminder.get_active_medications()
        taken = sum(1 for m in meds if m.taken_today)
        self.stats_label.configure(text=f"✅ {taken}/{len(meds)} completed")
    
    def _populate_schedule(self):
        for w in self.schedule_list.winfo_children(): w.destroy()
        r = responsive
        upcoming = medication_reminder.get_upcoming_medications(24)
        if not upcoming:
            ctk.CTkLabel(self.schedule_list, text="No upcoming medications in 24h",
                         font=r.font(base_size=11),
                         text_color=COLORS["text_muted"]).pack(pady=r.pad(12))
            return
        for med, t in upcoming:
            f = ctk.CTkFrame(self.schedule_list, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["md"])
            f.pack(fill="x", pady=r.pad(2))
            icon = "💉" if med.is_injection else "💊"
            si = "✅" if med.taken_today else "⏳"
            sc = COLORS["success"] if med.taken_today else COLORS["text_muted"]
            ctk.CTkLabel(f, text=t, font=r.font(base_size=10, weight="bold"),
                        text_color=COLORS["primary"], width=r.size(50)).pack(
                side="left", padx=r.pad(4), pady=r.pad(4))
            ctk.CTkLabel(f, text=f"{icon} {med.name}", font=r.font(base_size=9),
                        text_color=COLORS["text_primary"], anchor="w").pack(
                side="left", fill="x", expand=True, pady=r.pad(4), padx=r.pad(4))
            ctk.CTkLabel(f, text=si, font=r.font_ar(base_size=12),
                        text_color=sc, width=r.size(24)).pack(
                side="right", padx=r.pad(6))
    
    def on_hide(self): pass
    def on_show(self):
        self._populate_medications()
        self._populate_schedule()
