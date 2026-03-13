"""
AI Robot Operating System - Home Screen
نظام تشغيل الروبوت الطبي الذكي - الشاشة الرئيسية

The main dashboard showing vital signs, quick actions,
and upcoming medication reminders.

لوحة المعلومات الرئيسية التي تعرض العلامات الحيوية والإجراءات السريعة
وتذكيرات الأدوية القادمة.
"""

import customtkinter as ctk
from datetime import datetime
import threading
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS
from gui.widgets.vital_card import VitalCard
from gui.widgets.nav_button import QuickActionButton
from core.utils import get_arabic_date, get_arabic_time, get_time_of_day
from core.arabic_utils import fix_arabic as _


class HomeScreen(ctk.CTkFrame):
    
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        
        self.app = app_controller
        self.vital_cards = {}
        
        self._create_layout()
        self._start_time_update()
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.scroll_container.grid(row=0, column=0, sticky="nsew")
        self.scroll_container.grid_columnconfigure(0, weight=1)
        
        self._create_header()
        self._create_vitals_section()
        self._create_quick_actions()
        self._create_alerts_section()
    
    def _create_header(self):
        self.header_frame = ctk.CTkFrame(
            self.scroll_container,
            fg_color="transparent"
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 5))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.greeting_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.greeting_frame.grid(row=0, column=0, sticky="w")
        
        self.greeting_label = ctk.CTkLabel(
            self.greeting_frame,
            text=_(f"{get_time_of_day()}! 👋"),
            font=(FONTS["family"], FONTS["size_2xl"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.greeting_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.greeting_frame,
            text=_("كيف حالك اليوم؟"),
            font=(FONTS["family"], FONTS["size_md"]),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.subtitle_label.pack(anchor="w")
        
        self.datetime_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.datetime_frame.grid(row=0, column=1, sticky="e")
        
        self.time_label = ctk.CTkLabel(
            self.datetime_frame,
            text=get_arabic_time(),
            font=(FONTS["family_en"], FONTS["size_3xl"], "bold"),
            text_color=COLORS["primary"],
            anchor="e"
        )
        self.time_label.pack(anchor="e")
        
        self.date_label = ctk.CTkLabel(
            self.datetime_frame,
            text=get_arabic_date(),
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.date_label.pack(anchor="e")
    
    def _create_vitals_section(self):
        self.vitals_frame = ctk.CTkFrame(
            self.scroll_container,
            fg_color="transparent"
        )
        self.vitals_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        
        self.vitals_title = ctk.CTkLabel(
            self.vitals_frame,
            text=_("📊 العلامات الحيوية"),
            font=(FONTS["family"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        self.vitals_title.pack(anchor="e", pady=(0, 10))
        
        self.cards_container = ctk.CTkFrame(
            self.vitals_frame,
            fg_color="transparent"
        )
        self.cards_container.pack(fill="x")
        
        for i in range(3):
            self.cards_container.grid_columnconfigure(i, weight=1)
        
        self.bp_card = VitalCard(
            self.cards_container,
            title=_("ضغط الدم"),
            icon="🩸",
            value="--/--",
            unit="mmHg",
            status=_("جاري القياس..."),
            color=COLORS["danger"]
        )
        self.bp_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.vital_cards["bp"] = self.bp_card
        
        self.hr_card = VitalCard(
            self.cards_container,
            title="نبضات القلب",
            icon="💓",
            value="--",
            unit="نبضة/دقيقة",
            status="جاري القياس...",
            color=COLORS["danger"]
        )
        self.hr_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.vital_cards["hr"] = self.hr_card
        
        self.temp_card = VitalCard(
            self.cards_container,
            title="درجة الحرارة",
            icon="🌡️",
            value="--",
            unit="°C",
            status="جاري القياس...",
            color=COLORS["warning"]
        )
        self.temp_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.vital_cards["temp"] = self.temp_card
    
    def _create_quick_actions(self):
        self.actions_frame = ctk.CTkFrame(
            self.scroll_container,
            fg_color="transparent"
        )
        self.actions_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        
        self.actions_title = ctk.CTkLabel(
            self.actions_frame,
            text="⚡ الإجراءات السريعة",
            font=(FONTS["family"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        self.actions_title.pack(anchor="e", pady=(0, 10))
        
        self.actions_container = ctk.CTkFrame(
            self.actions_frame,
            fg_color="transparent"
        )
        self.actions_container.pack(fill="x")
        
        for i in range(3):
            self.actions_container.grid_columnconfigure(i, weight=1)

        self.meds_btn = QuickActionButton(
            self.actions_container,
            text="الأدوية",
            icon="💊",
            color=COLORS["warning"],
            command=lambda: self._navigate_to("meds")
        )
        self.meds_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.chat_btn = QuickActionButton(
            self.actions_container,
            text="المحادثة",
            icon="💬",
            color=COLORS["primary"],
            command=lambda: self._navigate_to("chat")
        )
        self.chat_btn.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.food_btn = QuickActionButton(
            self.actions_container,
            text="تحليل الطعام",
            icon="📷",
            color=COLORS["success"],
            command=lambda: self._navigate_to("food")
        )
        self.food_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    def _create_alerts_section(self):
        self.alerts_frame = ctk.CTkFrame(
            self.scroll_container,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["xl"],
            border_width=2,
            border_color=COLORS["border_light"]
        )
        self.alerts_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 20))
        
        self.alerts_title = ctk.CTkLabel(
            self.alerts_frame,
            text="⏰ الأدوية القادمة",
            font=(FONTS["family"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        self.alerts_title.pack(anchor="e", padx=20, pady=(15, 10))
        
        self.alerts_list = ctk.CTkScrollableFrame(
            self.alerts_frame,
            fg_color="transparent"
        )
        self.alerts_list.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        
        self._add_medication_alert("Concor 5mg", "08:00", "صباحاً", pending=True)
        self._add_medication_alert("Aspirin Protect 100mg", "14:00", "بعد الغداء", pending=True)
        self._add_medication_alert("Zestril 10mg", "20:00", "مساءً", pending=True)
    
    def _add_medication_alert(self, name: str, time: str, timing: str, pending: bool = True):
        alert_frame = ctk.CTkFrame(
            self.alerts_list,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["lg"]
        )
        alert_frame.pack(fill="x", pady=5)
        
        time_label = ctk.CTkLabel(
            alert_frame,
            text=time,
            font=(FONTS["family_en"], FONTS["size_md"], "bold"),
            text_color=COLORS["primary"],
            width=60
        )
        time_label.pack(side="right", padx=15, pady=10)
        
        info_frame = ctk.CTkFrame(alert_frame, fg_color="transparent")
        info_frame.pack(side="right", fill="x", expand=True, pady=10)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=name,
            font=(FONTS["family"], FONTS["size_md"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        name_label.pack(anchor="e")
        
        timing_label = ctk.CTkLabel(
            info_frame,
            text=timing,
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_muted"],
            anchor="e"
        )
        timing_label.pack(anchor="e")
        
        status_icon = "⏳" if pending else "✅"
        icon_color = COLORS["warning"] if pending else COLORS["success"]
        
        icon_label = ctk.CTkLabel(
            alert_frame,
            text=status_icon,
            font=(FONTS["family"], FONTS["size_xl"]),
            text_color=icon_color
        )
        icon_label.pack(side="left", padx=15)
    
    def _navigate_to(self, screen: str):
        if self.app:
            self.app.show_screen(screen)
    
    def _start_time_update(self):
        self._update_time()
    
    def _update_time(self):
        self.time_label.configure(text=get_arabic_time())
        self.greeting_label.configure(text=f"{get_time_of_day()}! 👋")
        self.after(30000, self._update_time)
    
    def update_vitals(self, vitals_data: dict):
        if "blood_pressure" in vitals_data:
            bp = vitals_data["blood_pressure"]
            self.bp_card.update_value(
                bp["value"],
                bp["unit"],
                bp["status"]
            )
        
        if "heart_rate" in vitals_data:
            hr = vitals_data["heart_rate"]
            self.hr_card.update_value(
                hr["value"],
                hr["unit"],
                hr["status"]
            )
        
        if "temperature" in vitals_data:
            temp = vitals_data["temperature"]
            self.temp_card.update_value(
                temp["value"],
                temp["unit"],
                temp["status"]
            )
