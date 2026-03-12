"""
AI Robot Operating System - Vital Card Widget
نظام تشغيل الروبوت الطبي الذكي - عنصر بطاقة العلامات الحيوية

A custom widget for displaying vital signs with status indicators.
عنصر مخصص لعرض العلامات الحيوية مع مؤشرات الحالة.
"""

import customtkinter as ctk
from typing import Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS, get_status_color


class VitalCard(ctk.CTkFrame):
    """
    Vital Signs Card Widget
    بطاقة العلامات الحيوية
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
    
    def _create_layout(self):
        """Create the card layout - إنشاء تخطيط البطاقة"""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        
        self.header_frame = ctk.CTkFrame(
            self, 
            fg_color="transparent"
        )
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        self.icon_label = ctk.CTkLabel(
            self.header_frame,
            text=self.icon,
            font=(FONTS["family"], FONTS["size_2xl"]),
            text_color=self.color
        )
        self.icon_label.pack(side="right", padx=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=self.title,
            font=(FONTS["family"], FONTS["size_md"], "bold"),
            text_color=COLORS["text_secondary"],
            anchor="e"
        )
        self.title_label.pack(side="right", fill="x", expand=True)
        
        self.value_frame = ctk.CTkFrame(
            self, 
            fg_color="transparent"
        )
        self.value_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        self.value_label = ctk.CTkLabel(
            self.value_frame,
            text="--",
            font=(FONTS["family_en"], FONTS["size_4xl"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="center"
        )
        self.value_label.pack(expand=True)
        
        self.unit_label = ctk.CTkLabel(
            self.value_frame,
            text="",
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_muted"],
            anchor="center"
        )
        self.unit_label.pack()
        
        self.status_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_secondary"],
            corner_radius=RADIUS["full"],
            height=28
        )
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 20))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_secondary"],
            anchor="center"
        )
        self.status_label.pack(expand=True, fill="both", padx=10, pady=5)
    
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
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=(FONTS["family"], FONTS["size_xl"]),
            text_color=self.color,
            width=40
        )
        self.icon_label.grid(row=0, column=0, rowspan=2, padx=(10, 5), pady=10)
        
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=(FONTS["family"], FONTS["size_sm"]),
            text_color=COLORS["text_muted"],
            anchor="e"
        )
        self.title_label.grid(row=0, column=1, sticky="e", padx=10, pady=(10, 0))
        
        self.value_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.value_frame.grid(row=1, column=1, sticky="e", padx=10, pady=(0, 10))
        
        self.value_label = ctk.CTkLabel(
            self.value_frame,
            text=value,
            font=(FONTS["family_en"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"]
        )
        self.value_label.pack(side="right")
        
        self.unit_label = ctk.CTkLabel(
            self.value_frame,
            text=unit,
            font=(FONTS["family"], FONTS["size_xs"]),
            text_color=COLORS["text_muted"]
        )
        self.unit_label.pack(side="right", padx=(0, 5))
    
    def update_value(self, value: str, unit: str = ""):
        self.value_label.configure(text=value)
        if unit:
            self.unit_label.configure(text=unit)
