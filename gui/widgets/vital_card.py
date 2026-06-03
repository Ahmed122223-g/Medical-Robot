"""
AI Robot Operating System - Vital Card Widget
A custom widget for displaying vital signs with status indicators.
"""

import customtkinter as ctk
from typing import Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS, get_status_color, responsive
from core.arabic_utils import fix_arabic as _


class VitalCard(ctk.CTkFrame):
    """
    Vital Signs Card Widget - Responsive
    بطاقة العلامات الحيوية - متجاوبة
    """
    
    def __init__(
        self,
        master,
        title: str,
        icon: str,
        value: str = "--",
        unit: str = "",
        status: str = "",
        color: str = None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            border_width=2,
            border_color=COLORS["border_light"],
            **kwargs
        )
        
        self.title = title
        self.icon = icon
        self.color = color or COLORS["primary"]
        
        self._create_layout()
        self.update_value(value, unit, status)
        
        # Bind resize for responsive updates
        self.bind("<Configure>", self._on_resize)
        self._last_w = 0
    
    def _on_resize(self, event=None):
        w = self.winfo_width()
        if abs(w - self._last_w) < 20:
            return
        self._last_w = w
        self._update_fonts()
    
    def _update_fonts(self):
        """Update all fonts based on current responsive scale."""
        r = responsive
        self.icon_label.configure(font=r.font_ar(base_size=22))
        self.title_label.configure(font=r.font(base_size=12, weight="bold"))
        self.value_label.configure(font=r.font(base_size=32, weight="bold"))
        self.unit_label.configure(font=r.font_ar(base_size=10))
        self.status_label.configure(font=r.font_ar(base_size=10))
    
    def _create_layout(self):
        """Create the card layout - إنشاء تخطيط البطاقة"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        
        r = responsive
        
        self.header_frame = ctk.CTkFrame(
            self, 
            fg_color="transparent"
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=r.pad(10), pady=(r.pad(8), r.pad(2)))
        
        self.icon_label = ctk.CTkLabel(
            self.header_frame,
            text=self.icon,
            font=r.font_ar(base_size=22),
            text_color=self.color
        )
        self.icon_label.pack(side="left", padx=(0, r.pad(5)))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=self.title,
            font=r.font(base_size=12, weight="bold"),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.title_label.pack(side="left", fill="x", expand=True)
        
        self.value_frame = ctk.CTkFrame(
            self, 
            fg_color="transparent"
        )
        self.value_frame.grid(row=1, column=0, sticky="nsew", padx=r.pad(10), pady=r.pad(2))
        
        self.value_label = ctk.CTkLabel(
            self.value_frame,
            text="--",
            font=r.font(base_size=32, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="center"
        )
        self.value_label.pack(expand=True)
        
        self.unit_label = ctk.CTkLabel(
            self.value_frame,
            text="",
            font=r.font_ar(base_size=10),
            text_color=COLORS["text_muted"],
            anchor="center"
        )
        self.unit_label.pack()
        
        self.status_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["full"],
        )
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=r.pad(12), pady=(r.pad(2), r.pad(10)))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=r.font_ar(base_size=10),
            text_color=COLORS["text_secondary"],
            anchor="center"
        )
        self.status_label.pack(expand=True, fill="both", padx=r.pad(6), pady=r.pad(3))
    
    def update_value(self, value: str, unit: str = "", status: str = ""):
        """
        Update the displayed value
        تحديث القيمة المعروضة
        """
        self.value_label.configure(text=value)
        self.unit_label.configure(text=unit)
        
        if status:
            status_color = get_status_color(status)
            self.status_label.configure(text=status, text_color=status_color)
            self.status_frame.configure(fg_color=COLORS["bg_tertiary"])
    
    def set_color(self, color: str):
        self.color = color
        self.icon_label.configure(text_color=color)
    
    def animate_pulse(self):
        original_color = self.cget("border_color")
        self.configure(border_color=self.color, border_width=2)
        self.after(300, lambda: self.configure(border_color=original_color, border_width=1))


class CompactVitalCard(ctk.CTkFrame):
    """
    Compact Vital Signs Card (smaller version)
    بطاقة العلامات الحيوية المضغوطة
    """
    
    def __init__(
        self,
        master,
        title: str,
        icon: str,
        value: str = "--",
        unit: str = "",
        color: str = None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["md"],
            **kwargs
        )
        
        self.color = color or COLORS["primary"]
        self.title = title
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        r = responsive
        
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=r.font_ar(base_size=18),
            text_color=self.color,
            width=r.size(30)
        )
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=(r.pad(8), r.pad(4)), pady=r.pad(6))
        
        self.title_label = ctk.CTkLabel(
            self,
            text=self.title,
            font=r.font_ar(base_size=10),
            text_color=COLORS["text_muted"],
            anchor="w"
        )
        self.title_label.grid(row=0, column=1, sticky="w", padx=r.pad(6), pady=(r.pad(6), 0))
        
        self.value_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.value_frame.grid(row=1, column=1, sticky="w", padx=r.pad(6), pady=(0, r.pad(6)))
        
        self.value_label = ctk.CTkLabel(
            self.value_frame,
            text=value,
            font=r.font(base_size=14, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        self.value_label.pack(side="right")
        
        self.unit_label = ctk.CTkLabel(
            self.value_frame,
            text=unit,
            font=r.font_ar(base_size=9),
            text_color=COLORS["text_muted"]
        )
        self.unit_label.pack(side="right", padx=(0, r.pad(4)))
    
    def update_value(self, value: str, unit: str = ""):
        self.value_label.configure(text=value)
        if unit:
            self.unit_label.configure(text=unit)
