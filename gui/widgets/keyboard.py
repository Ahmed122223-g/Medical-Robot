"""
AI Robot Operating System - Virtual Keyboard Widget
نظام تشغيل الروبوت الطبي الذكي - لوحة المفاتيح الافتراضية

A professional on-screen keyboard for touchscreens.
لوحة مفاتيح افتراضية مخصصة واحترافية لشاشات اللمس.
"""

import customtkinter as ctk
from typing import Optional, Union
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.styles.theme import COLORS, FONTS, RADIUS
from core.arabic_utils import fix_arabic as _

class VirtualKeyboard(ctk.CTkToplevel):
    """
    On-screen virtual keyboard
    لوحة مفاتيح افتراضية
    """
    
    def __init__(self, master, target_widget: Optional[Union[ctk.CTkEntry, ctk.CTkTextbox]] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.target = target_widget
        self.language = "ar" 
        self.is_shift = False
        
        # Window configuration
        self.title("Keyboard")
        self.attributes("-topmost", True)
        self.overrideredirect(True) 
        
        # Styling
        self.configure(fg_color=COLORS["bg_secondary"])
        
        # Optimized size for 800x480 screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        width = 790
        height = 220 # Reduced height for more screen visibility
        x = (screen_width - width) // 2
        y = screen_height - height - 5
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self._create_layout()
        
    def _create_layout(self):
        # Container with subtle border
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=COLORS["border"]
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Top handle/bar
        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=30)
        self.top_bar.pack(fill="x", padx=10, pady=(2, 0))
        
        # Drag handle (aesthetic)
        handle = ctk.CTkFrame(self.top_bar, fg_color=COLORS["border"], width=40, height=4, corner_radius=2)
        handle.place(relx=0.5, rely=0.5, anchor="center")
        
        self.lang_btn = ctk.CTkButton(
            self.top_bar,
            text=_("English") if self.language == "ar" else "العربية",
            width=70,
            height=24,
            font=(FONTS["family"], 11),
            fg_color=COLORS["bg_tertiary"],
            text_color=COLORS["text_secondary"],
            command=self._toggle_language
        )
        self.lang_btn.pack(side="left")
        
        self.close_btn = ctk.CTkButton(
            self.top_bar,
            text="✕",
            width=30,
            height=24,
            fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color=COLORS["danger"],
            command=self.destroy
        )
        self.close_btn.pack(side="right")
        
        # Keyboard grid
        self.keys_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.keys_frame.pack(fill="both", expand=True, padx=5, pady=(2, 5))
        
        self._draw_keys()
        
    def _toggle_language(self):
        self.language = "en" if self.language == "ar" else "ar"
        self.lang_btn.configure(text=_("English") if self.language == "ar" else "العربية")
        self._draw_keys()
        
    def _draw_keys(self):
        # Clear existing keys
        for widget in self.keys_frame.winfo_children():
            widget.destroy()
            
        layouts = {
            "ar": [
                ["١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩", "٠"],
                ["ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د"],
                ["ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط"],
                ["ئ", "ء", "ؤ", "ر", "لا", "ى", "ة", "و", "ز", "ظ", "⌫"],
                ["١٢٣", "مسافة", "إدخال"]
            ],
            "en": [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
                ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
                ["⇧", "z", "x", "c", "v", "b", "n", "m", ",", ".", "⌫"],
                ["?123", "Space", "Enter"]
            ]
        }
        
        rows = layouts[self.language]
        
        for r_idx, row in enumerate(rows):
            row_frame = ctk.CTkFrame(self.keys_frame, fg_color="transparent")
            row_frame.pack(fill="x", expand=True)
            
            for key in row:
                self._create_key(row_frame, key)
                
    def _create_key(self, parent, text):
        is_action = text in ["⌫", "إدخال", "Enter", "مسافة", "Space", "⇧", "١٢٣", "?123"]
        
        width = 35
        if text in ["مسافة", "Space"]:
            width = 300
        elif text in ["إدخال", "Enter"]:
            width = 120
        elif text in ["⌫", "⇧"]:
            width = 70
            
        # Use fix_arabic only for Arabic key labels
        display_text = _(text) if self.language == "ar" else text
            
        btn = ctk.CTkButton(
            parent,
            text=display_text,
            width=width,
            height=32, # Reduced button height
            font=(FONTS["family"] if self.language == "ar" else FONTS["family_en"], 14, "bold"),
            fg_color=COLORS["bg_tertiary"] if is_action else COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["primary"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=4,
            command=lambda k=text: self._on_key_press(k)
        )
        btn.pack(side="left" if self.language == "en" else "right", padx=1, pady=1, expand=True if not is_action else False)
        
    def _on_key_press(self, key):
        if not self.target:
            return
            
        if key in ["⌫"]:
            if isinstance(self.target, ctk.CTkEntry):
                curr = self.target.get()
                self.target.delete(0, 'end')
                self.target.insert(0, curr[:-1])
            else:
                curr = self.target.get("1.0", "end-1c")
                self.target.delete("1.0", "end")
                self.target.insert("1.0", curr[:-1])
        elif key in ["مسافة", "Space"]:
            self.target.insert("insert", " ")
        elif key in ["إدخال", "Enter"]:
            self.target.event_generate("<Return>")
            self.destroy()
        elif key == "⇧":
            self.is_shift = not self.is_shift
            self._draw_keys()
        else:
            char = key
            if self.is_shift and self.language == "en":
                char = char.upper()
            self.target.insert("insert", char)

def show_keyboard(master, target):
    return VirtualKeyboard(master, target)
