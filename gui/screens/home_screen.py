"""
AI Robot Operating System - Home Screen
Main dashboard showing vital signs, quick actions,
and upcoming medication reminders.
Fully responsive - no scrolling, SVG-like scaling.
"""

import customtkinter as ctk
from datetime import datetime
import threading
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS, responsive
from gui.widgets.vital_card import VitalCard
from gui.widgets.nav_button import QuickActionButton
from core.utils import get_arabic_date, get_arabic_time, get_time_of_day
from core.arabic_utils import fix_arabic as _
from modules.medication_reminder import medication_reminder


class HomeScreen(ctk.CTkFrame):
    
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        
        self.app = app_controller
        self.vital_cards = {}
        self._last_w = 0
        self._last_h = 0
        
        self._create_layout()
        self._start_time_update()
        
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
        """Update all fonts and sizes based on current dimensions."""
        r = responsive
        # Header
        self.greeting_label.configure(font=r.font(base_size=20, weight="bold"))
        self.subtitle_label.configure(font=r.font(base_size=12))
        self.time_label.configure(font=r.font(base_size=26, weight="bold"))
        self.date_label.configure(font=r.font(base_size=10))
        # Section titles
        self.vitals_title.configure(font=r.font(base_size=13, weight="bold"))
        self.actions_title.configure(font=r.font(base_size=13, weight="bold"))
        self.alerts_title.configure(font=r.font(base_size=13, weight="bold"))
        # Buttons
        for btn in [self.chat_btn, self.food_btn, self.meds_btn]:
            btn.configure(font=r.font(base_size=11, weight="bold"))
    
    def _create_layout(self):
        r = responsive
        
        # Main grid: no scroll, everything fits
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)   # Header ~8%
        self.grid_rowconfigure(1, weight=0)   # Vitals title
        self.grid_rowconfigure(2, weight=3)   # 3 vital cards ~25%
        self.grid_rowconfigure(3, weight=0)   # Actions title
        self.grid_rowconfigure(4, weight=1)   # 3 action buttons ~12%
        self.grid_rowconfigure(5, weight=0)   # Meds title
        self.grid_rowconfigure(6, weight=5)   # Medications section ~55%
        
        self._create_header()
        self._create_vitals_section()
        self._create_quick_actions()
        self._create_medications_section()
    
    def _create_header(self):
        r = responsive
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=r.pad(15), pady=(r.pad(6), r.pad(2)))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)
        
        self.greeting_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.greeting_frame.grid(row=0, column=0, sticky="w")
        
        self.greeting_label = ctk.CTkLabel(
            self.greeting_frame,
            text=f"{get_time_of_day()}! 👋",
            font=r.font(base_size=20, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.greeting_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.greeting_frame,
            text="How are you feeling today?",
            font=r.font(base_size=12),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.subtitle_label.pack(anchor="w")
        
        self.datetime_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.datetime_frame.grid(row=0, column=1, sticky="e")
        
        self.time_label = ctk.CTkLabel(
            self.datetime_frame,
            text=get_arabic_time(),
            font=r.font(base_size=26, weight="bold"),
            text_color=COLORS["primary"],
            anchor="e"
        )
        self.time_label.pack(anchor="e")
        
        self.date_label = ctk.CTkLabel(
            self.datetime_frame,
            text=get_arabic_date(),
            font=r.font(base_size=10),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.date_label.pack(anchor="e")
    
    def _create_vitals_section(self):
        r = responsive
        
        self.vitals_title = ctk.CTkLabel(
            self,
            text="📊 Vital Signs",
            font=r.font(base_size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.vitals_title.grid(row=1, column=0, sticky="w", padx=r.pad(15), pady=(r.pad(2), r.pad(2)))
        
        # Cards container: 3 columns side-by-side
        self.cards_container = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_container.grid(row=2, column=0, sticky="nsew", padx=r.pad(15), pady=(0, r.pad(2)))
        self.cards_container.grid_columnconfigure(0, weight=1, uniform="vital")
        self.cards_container.grid_columnconfigure(1, weight=1, uniform="vital")
        self.cards_container.grid_columnconfigure(2, weight=1, uniform="vital")
        self.cards_container.grid_rowconfigure(0, weight=1)
        
        self.bp_card = VitalCard(
            self.cards_container,
            title="Blood Pressure",
            icon="🩸",
            value="--/--",
            unit="mmHg",
            status="Measuring...",
            color=COLORS["danger"]
        )
        self.bp_card.grid(row=0, column=0, padx=r.pad(3), pady=r.pad(2), sticky="nsew")
        self.vital_cards["bp"] = self.bp_card
        
        self.hr_card = VitalCard(
            self.cards_container,
            title="Heart Rate",
            icon="💓",
            value="--",
            unit="bpm",
            status="Measuring...",
            color=COLORS["danger"]
        )
        self.hr_card.grid(row=0, column=1, padx=r.pad(3), pady=r.pad(2), sticky="nsew")
        self.vital_cards["hr"] = self.hr_card
        
        self.temp_card = VitalCard(
            self.cards_container,
            title="Temperature",
            icon="🌡️",
            value="--",
            unit="°C",
            status="Measuring...",
            color=COLORS["warning"]
        )
        self.temp_card.grid(row=0, column=2, padx=r.pad(3), pady=r.pad(2), sticky="nsew")
        self.vital_cards["temp"] = self.temp_card
    
    def _create_quick_actions(self):
        r = responsive
        
        self.actions_title = ctk.CTkLabel(
            self,
            text="⚡ Quick Actions",
            font=r.font(base_size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.actions_title.grid(row=3, column=0, sticky="w", padx=r.pad(15), pady=(r.pad(2), r.pad(2)))
        
        # 3 buttons side-by-side
        self.actions_container = ctk.CTkFrame(self, fg_color="transparent")
        self.actions_container.grid(row=4, column=0, sticky="nsew", padx=r.pad(15), pady=(0, r.pad(2)))
        self.actions_container.grid_columnconfigure(0, weight=1, uniform="action")
        self.actions_container.grid_columnconfigure(1, weight=1, uniform="action")
        self.actions_container.grid_columnconfigure(2, weight=1, uniform="action")
        self.actions_container.grid_rowconfigure(0, weight=1)
        
        self.chat_btn = QuickActionButton(
            self.actions_container,
            text="Chat",
            icon="💬",
            color=COLORS["primary"],
            command=lambda: self._navigate_to("chat")
        )
        self.chat_btn.grid(row=0, column=0, padx=r.pad(3), pady=r.pad(2), sticky="nsew")
        
        self.food_btn = QuickActionButton(
            self.actions_container,
            text="Food Analysis",
            icon="📷",
            color=COLORS["success"],
            command=lambda: self._navigate_to("food")
        )
        self.food_btn.grid(row=0, column=1, padx=r.pad(3), pady=r.pad(2), sticky="nsew")
        
        self.meds_btn = QuickActionButton(
            self.actions_container,
            text="Medications",
            icon="💊",
            color=COLORS["warning"],
            command=lambda: self._navigate_to("meds")
        )
        self.meds_btn.grid(row=0, column=2, padx=r.pad(3), pady=r.pad(2), sticky="nsew")

    def _create_medications_section(self):
        """Create medications section - styled like the meds screen, compact, no scroll."""
        r = responsive
        
        self.alerts_title = ctk.CTkLabel(
            self,
            text="⏰ Upcoming Medications",
            font=r.font(base_size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.alerts_title.grid(row=5, column=0, sticky="w", padx=r.pad(15), pady=(r.pad(2), r.pad(2)))
        
        self.alerts_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=1,
            border_color=COLORS["border_light"]
        )
        self.alerts_frame.grid(row=6, column=0, sticky="nsew", padx=r.pad(15), pady=(0, r.pad(8)))
        self.alerts_frame.grid_columnconfigure(0, weight=1)
        self.alerts_frame.grid_rowconfigure(0, weight=1)
        
        # Inner scrollable for medication items (they may overflow)
        self.alerts_list = ctk.CTkScrollableFrame(
            self.alerts_frame,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.alerts_list.pack(fill="both", expand=True, padx=r.pad(6), pady=r.pad(6))
        
        self._populate_home_medications()
    
    def _populate_home_medications(self):
        """Populate medication cards styled like the MedsScreen cards."""
        r = responsive
        
        # Clear existing
        for w in self.alerts_list.winfo_children():
            w.destroy()
        
        try:
            meds = medication_reminder.get_active_medications()
        except Exception:
            meds = []
        
        if not meds:
            # Fallback static meds
            self._add_medication_alert("Concor 5mg", "08:00", "Morning", pending=True)
            self._add_medication_alert("Aspirin Protect 100mg", "14:00", "After Lunch", pending=True)
            self._add_medication_alert("Zestril 10mg", "20:00", "Evening", pending=True)
            return
        
        for med in meds:
            alert_frame = ctk.CTkFrame(
                self.alerts_list,
                fg_color=COLORS["bg_secondary"],
                corner_radius=RADIUS["md"],
                border_width=1,
                border_color=COLORS["border_light"]
            )
            alert_frame.pack(fill="x", pady=r.pad(2))
            alert_frame.grid_columnconfigure(0, weight=0)
            alert_frame.grid_columnconfigure(1, weight=1)
            alert_frame.grid_columnconfigure(2, weight=0)
            
            icon = "💉" if med.is_injection else "💊"
            ctk.CTkLabel(
                alert_frame,
                text=icon,
                font=r.font_ar(base_size=18),
            ).grid(row=0, column=0, rowspan=2, padx=r.pad(8), pady=r.pad(4))
            
            ctk.CTkLabel(
                alert_frame,
                text=med.name,
                font=r.font(base_size=11, weight="bold"),
                text_color=COLORS["text_primary"],
                anchor="w"
            ).grid(row=0, column=1, sticky="w", padx=r.pad(4), pady=(r.pad(4), 0))
            
            ctk.CTkLabel(
                alert_frame,
                text=f"{med.dose} - {med.timing}",
                font=r.font(base_size=9),
                text_color=COLORS["text_muted"],
                anchor="w"
            ).grid(row=1, column=1, sticky="w", padx=r.pad(4), pady=(0, r.pad(4)))
            
            status_icon = "✅" if med.taken_today else "⏳"
            status_color = COLORS["success"] if med.taken_today else COLORS["warning"]
            ctk.CTkLabel(
                alert_frame,
                text=status_icon,
                font=r.font_ar(base_size=16),
                text_color=status_color
            ).grid(row=0, column=2, rowspan=2, padx=r.pad(8))
    
    def _add_medication_alert(self, name: str, time: str, timing: str, pending: bool = True):
        """Fallback static medication alert."""
        r = responsive
        alert_frame = ctk.CTkFrame(
            self.alerts_list,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["md"]
        )
        alert_frame.pack(fill="x", pady=r.pad(2))
        
        time_label = ctk.CTkLabel(
            alert_frame,
            text=time,
            font=r.font(base_size=11, weight="bold"),
            text_color=COLORS["primary"],
            width=r.size(50)
        )
        time_label.pack(side="left", padx=r.pad(10), pady=r.pad(6))
        
        info_frame = ctk.CTkFrame(alert_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, pady=r.pad(6))
        
        ctk.CTkLabel(
            info_frame,
            text=name,
            font=r.font(base_size=11, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=timing,
            font=r.font(base_size=9),
            text_color=COLORS["text_muted"],
            anchor="w"
        ).pack(anchor="w")
        
        status_icon = "⏳" if pending else "✅"
        icon_color = COLORS["warning"] if pending else COLORS["success"]
        
        ctk.CTkLabel(
            alert_frame,
            text=status_icon,
            font=r.font_ar(base_size=16),
            text_color=icon_color
        ).pack(side="right", padx=r.pad(10))
    
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
    
    def on_show(self):
        """Refresh medications when screen is shown."""
        self._populate_home_medications()
    
    def on_hide(self):
        pass
