"""
AI Robot Operating System - Medications Screen
نظام تشغيل الروبوت الطبي الذكي - شاشة الأدوية

Screen for managing medications, reminders, and insulin calculations.
شاشة لإدارة الأدوية والتذكيرات وحسابات الأنسولين.
"""

import customtkinter as ctk
from typing import Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS
from modules.medication_reminder import medication_reminder, Medication
from modules.vital_signs import vital_signs_monitor


class MedicationCard(ctk.CTkFrame):
    """
    Medication card widget
    بطاقة الدواء
    """
    
    def __init__(self, master, medication: Medication, on_take_callback=None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=2,
            border_color=COLORS["border_light"],
            **kwargs
        )
        
        self.medication = medication
        self.on_take = on_take_callback
        
        self._create_layout()
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        
        icon = "💉" if self.medication.is_injection else "💊"
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=(FONTS["family"], 28),
            width=50
        )
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        
        self.name_label = ctk.CTkLabel(
            self,
            text=self.medication.name,
            font=(FONTS["family"], FONTS["size_md"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        self.name_label.grid(row=0, column=1, sticky="e", padx=10, pady=(10, 0))
        
        dose_text = f"{self.medication.dose} - {self.medication.timing}"
        self.dose_label = ctk.CTkLabel(
            self,
            text=dose_text,
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_muted"],
            anchor="e"
        )
        self.dose_label.grid(row=1, column=1, sticky="e", padx=10, pady=(0, 10))
        
        self.purpose_label = ctk.CTkLabel(
            self,
            text=self.medication.purpose,
            font=(FONTS["family"], FONTS["size_xs"]),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.purpose_label.grid(row=2, column=1, sticky="e", padx=10, pady=(0, 10))
        
        if self.medication.taken_today:
            self.status_label = ctk.CTkLabel(
                self,
                text="✅",
                font=(FONTS["family"], 24),
                text_color=COLORS["success"]
            )
            self.status_label.grid(row=0, column=2, rowspan=3, padx=15)
        else:
            self.take_btn = ctk.CTkButton(
                self,
                text="تم",
                font=(FONTS["family"], FONTS["size_sm"]),
                width=60,
                height=35,
                fg_color=COLORS["success"],
                hover_color=COLORS["success_hover"],
                command=self._mark_taken
            )
            self.take_btn.grid(row=0, column=2, rowspan=3, padx=15)
    
    def _mark_taken(self):
        """Mark medication as taken - تحديد أخذ الدواء"""
        medication_reminder.mark_as_taken(self.medication.name)
        self.medication.taken_today = True
        
        self.take_btn.destroy()
        self.status_label = ctk.CTkLabel(
            self,
            text="✅",
            font=(FONTS["family"], 24),
            text_color=COLORS["success"]
        )
        self.status_label.grid(row=0, column=2, rowspan=3, padx=15)
        
        if self.on_take:
            self.on_take(self.medication)


class InsulinCalculator(ctk.CTkFrame):
    """
    Insulin dose calculator widget
    حاسبة جرعة الأنسولين
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            **kwargs
        )
        
        self._create_layout()
    
    def _create_layout(self):
        self.title_label = ctk.CTkLabel(
            self,
            text="💉 حاسبة جرعة الأنسولين",
            font=(FONTS["family"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        self.title_label.pack(anchor="e", padx=20, pady=(15, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self,
            text="حساب الجرعة باستخدام آخر قراءة متاحة (إذا وُجدت)",
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.subtitle_label.pack(anchor="e", padx=20, pady=(0, 15))
        
        self.sugar_input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.sugar_input_frame.pack(fill="x", padx=20, pady=5)
        
        self.sugar_label = ctk.CTkLabel(
            self.sugar_input_frame,
            text="قراءة السكر (mg/dL):",
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_secondary"]
        )
        self.sugar_label.pack(side="right", padx=10)
        
        self.sugar_entry = ctk.CTkEntry(
            self.sugar_input_frame,
            placeholder_text="مثال: 150",
            font=(FONTS["family_en"], FONTS["size_md"]),
            width=120,
            height=40,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            corner_radius=RADIUS["md"]
        )
        self.sugar_entry.pack(side="right")
        
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=20, pady=10)
        
        self.calc_btn = ctk.CTkButton(
            self.action_frame,
            text="حساب الجرعة",
            font=(FONTS["family"], FONTS["size_md"], "bold"),
            fg_color=COLORS["secondary"],
            hover_color=COLORS["secondary_hover"],
            width=120,
            height=40,
            command=self._calculate
        )
        self.calc_btn.pack(side="left")
        
        self.result_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["lg"]
        )
        self.result_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.result_label = ctk.CTkLabel(
            self.result_frame,
            text="أدخل قراءة السكر لحساب الجرعة",
            font=(FONTS["family"], FONTS["size_md"]),
            text_color=COLORS["text_muted"],
            anchor="center"
        )
        self.result_label.pack(pady=20)
    
    def _calculate(self):
        manual_val = self.sugar_entry.get().strip()
        
        if manual_val:
            try:
                sugar_val = int(manual_val)
                vital_signs_monitor.set_manual_reading("sugar", sugar_val)
            except ValueError:
                self.result_label.configure(
                    text="❌ يرجى إدخال رقم صحيح لقراءة السكر",
                    text_color=COLORS["danger"]
                )
                return
        else:
            try:
                sugar_val = vital_signs_monitor.manual_readings.get("sugar", 0)
            except Exception:
                sugar_val = 0

        if not sugar_val or sugar_val <= 0:
            self.result_label.configure(
                text="❌ لا توجد قراءة سكر. أدخل القراءة يدوياً أعلاه.",
                text_color=COLORS["danger"]
            )
            return

        result = medication_reminder.calculate_insulin_dose(int(sugar_val))
        
        if result.get("error"):
            self.result_label.configure(
                text=result.get("message", "خطأ"),
                text_color=COLORS["danger"]
            )
            return
        
        for med in medication_reminder.medications:
            if med.name == "Lantus SoloStar":
                med.calculated_dose = result['total_dose']
                med.calculation_sugar = result['blood_sugar']
                medication_reminder._save_state()
                break

        lines = [
            f"📊 مستوى السكر: {result['blood_sugar']} mg/dL ({result['blood_sugar_status']})",
            "",
            f"💉 الجرعة الأساسية: {result['base_dose']} وحدة",
            f"➕ جرعة التصحيح: {result['correction_dose']} وحدة",
            f"━━━━━━━━━━━━━━━━━",
            f"📌 الجرعة الإجمالية: {result['total_dose']} وحدة",
            "",
            f"💡 {result['recommendation']}"
        ]
        
        if result.get("warning"):
            lines.append("")
            lines.append(result.get("warning_message", ""))
        
        self.result_label.configure(
            text="\n".join(lines),
            text_color=COLORS["success"] if not result.get("warning") else COLORS["warning"]
        )


class MedsScreen(ctk.CTkFrame):
    
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        
        self.app = app_controller
        
        self._create_layout()
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="💊 الأدوية والعلاجات",
            font=(FONTS["family"], FONTS["size_2xl"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        self.title_label.pack(anchor="e")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="إدارة الأدوية والتذكيرات وحاسبة الأنسولين",
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.subtitle_label.pack(anchor="e")
        
        self._create_medications_list()
        
        self._create_insulin_section()
    
    def _create_medications_list(self):
        self.meds_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.meds_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        
        header_frame = ctk.CTkFrame(self.meds_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="📋 قائمة الأدوية",
            font=(FONTS["family"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        ).pack(side="right")
        
        meds = medication_reminder.get_active_medications()
        taken = sum(1 for m in meds if m.taken_today)
        
        self.stats_label = ctk.CTkLabel(
            header_frame,
            text=f"✅ {taken}/{len(meds)} مكتمل",
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["success"]
        )
        self.stats_label.pack(side="left")
        
        self.meds_list = ctk.CTkScrollableFrame(
            self.meds_frame,
            fg_color="transparent"
        )
        self.meds_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self._populate_medications()
    
    def _populate_medications(self):
        for widget in self.meds_list.winfo_children():
            widget.destroy()
        
        meds = medication_reminder.get_active_medications()
        
        for med in meds:
            card = MedicationCard(
                self.meds_list,
                medication=med,
                on_take_callback=self._on_medication_taken
            )
            card.pack(fill="x", pady=5)
    
    def _on_medication_taken(self, medication: Medication):
        meds = medication_reminder.get_active_medications()
        taken = sum(1 for m in meds if m.taken_today)
        self.stats_label.configure(text=f"✅ {taken}/{len(meds)} مكتمل")
    
    def _create_insulin_section(self):
        self.insulin_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.insulin_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        
        self.insulin_frame.grid_rowconfigure(0, weight=0)
        self.insulin_frame.grid_rowconfigure(1, weight=1)
        
        self.calculator = InsulinCalculator(self.insulin_frame)
        self.calculator.pack(fill="x", pady=(0, 10))
        
        self._create_schedule_display()
    
    def _create_schedule_display(self):
        self.schedule_frame = ctk.CTkFrame(
            self.insulin_frame,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.schedule_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            self.schedule_frame,
            text="📅 جدول المواعيد",
            font=(FONTS["family"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        ).pack(anchor="e", padx=20, pady=(15, 10))
        
        self.schedule_list = ctk.CTkScrollableFrame(
            self.schedule_frame,
            fg_color="transparent"
        )
        self.schedule_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self._populate_schedule()
        
    def _populate_schedule(self):
        for widget in self.schedule_list.winfo_children():
            widget.destroy()
            
        upcoming = medication_reminder.get_upcoming_medications(24)
        
        if not upcoming:
            ctk.CTkLabel(
                self.schedule_list,
                text="لا توجد أدوية قادمة في الـ 24 ساعة القادمة",
                font=(FONTS["family"], FONTS["size_md"]),
                text_color=COLORS["text_muted"]
            ).pack(pady=20)
            return
            
        for med, time in upcoming:
            item_frame = ctk.CTkFrame(
                self.schedule_list,
                fg_color=COLORS["bg_secondary"],
                corner_radius=RADIUS["lg"]
            )
            item_frame.pack(fill="x", pady=5)
            
            icon = "💉" if med.is_injection else "💊"
            
            status_icon = "✅" if med.taken_today else "⏳"
            status_color = COLORS["success"] if med.taken_today else COLORS["text_muted"]
            
            ctk.CTkLabel(
                item_frame,
                text=time,
                font=(FONTS["family_en"], FONTS["size_md"], "bold"),
                text_color=COLORS["primary"],
                width=60
            ).pack(side="right", padx=5, pady=8)
            
            ctk.CTkLabel(
                item_frame,
                text=f"{icon} {med.name}",
                font=(FONTS["family"], FONTS["size_sm"]),
                text_color=COLORS["text_primary"],
                anchor="e"
            ).pack(side="right", fill="x", expand=True, pady=8, padx=5)

            ctk.CTkLabel(
                item_frame,
                text=status_icon,
                font=(FONTS["family"], 16),
                text_color=status_color,
                width=30
            ).pack(side="left", padx=10)
    
    def on_hide(self):
        pass
    
    def on_show(self):
        self._populate_medications()
        self._populate_schedule()
