"""
AI Robot Operating System - Virtual Keyboard V3
نظام تشغيل الروبوت الطبي الذكي - لوحة المفاتيح الافتراضية الإصدار الثالث

High-performance, premium virtual keyboard with pre-rendered layers.
لوحة مفاتيح افتراضية فائقة الأداء بتصميم احترافي وطبقات مسبقة التحميل.
"""

import customtkinter as ctk
from typing import Optional, Union, Dict
import sys
import os

# Ensure we can import from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from gui.styles.theme import COLORS, FONTS, RADIUS
from core.arabic_utils import fix_arabic as _

class VirtualKeyboard(ctk.CTkToplevel):
    """
    Advanced Virtual Keyboard with instant layer switching.
    لوحة مفاتيح افتراضية متقدمة مع تبديل فوري للطبقات.
    """
    
    def __init__(self, master, target_widget: Optional[Union[ctk.CTkEntry, ctk.CTkTextbox]] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.target = target_widget
        self.current_layer = "ar" # Default layer
        self.shift_active = False
        
        # Window properties
        self.title("Keyboard")
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.resizable(False, False)
        
        # Size and Position (Optimized for 800x480)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # We use a slightly more compact width but full screen width on Pi
        width = min(screen_width - 10, 790)
        height = 230
        x = (screen_width - width) // 2
        y = screen_height - height - 2
        
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.configure(fg_color=COLORS["bg_sidebar"])
        
        self.layers: Dict[str, ctk.CTkFrame] = {}
        self._create_ui()
        
    def _create_ui(self):
        # Background container with premium border
        self.main_container = ctk.CTkFrame(
            self, 
            fg_color=COLORS["bg_sidebar"],
            corner_radius=RADIUS["md"],
            border_width=1,
            border_color=COLORS["border_light"]
        )
        self.main_container.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Handle & Title Bar
        self.title_bar = ctk.CTkFrame(self.main_container, fg_color="transparent", height=28)
        self.title_bar.pack(fill="x", padx=10, pady=(2, 0))
        
        # Visual handle
        ctk.CTkFrame(self.title_bar, fg_color=COLORS["border"], width=40, height=3, corner_radius=2).place(relx=0.5, rely=0.5, anchor="center")
        
        # Close button
        self.close_btn = ctk.CTkButton(
            self.title_bar, text="✕", width=24, height=22, 
            fg_color="transparent", text_color=COLORS["text_muted"],
            hover_color=COLORS["danger"], command=self.destroy
        )
        self.close_btn.pack(side="right")
        
        # Layers container
        self.layers_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.layers_container.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        # PRE-RENDER ALL LAYERS FOR SPEED
        self._init_layers()
        self._switch_layer("ar") # Start with Arabic
        
    def _init_layers(self):
        """Create and hide all keyboard layers."""
        layer_configs = {
            "ar": [
                ["١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩", "٠"],
                ["ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د"],
                ["ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك", "ط"],
                ["ئ", "ء", "ؤ", "ر", "لا", "ى", "ة", "و", "ز", "ظ", "⌫"],
                ["en", "sym", "مسافة", "إدخال"]
            ],
            "en_low": [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
                ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
                ["⇧", "z", "x", "c", "v", "b", "n", "m", ",", ".", "⌫"],
                ["ar", "sym", "Space", "Enter"]
            ],
            "en_up": [
                ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
                ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
                ["⬆", "Z", "X", "C", "V", "B", "N", "M", "!", "?", "⌫"],
                ["ar", "sym", "Space", "Enter"]
            ],
            "sym": [
                ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")"],
                ["+", "-", "=", "[", "]", "{", "}", "\\", "|", ";"],
                ["'", "\"", ":", "<", ">", "/", "?", "_", "`", "~"],
                [".", ",", "€", "£", "¥", "©", "®", "™", "°", "⌫"],
                ["ar", "en", "Space", "Enter"]
            ]
        }
        
        for name, config in layer_configs.items():
            frame = ctk.CTkFrame(self.layers_container, fg_color="transparent")
            self.layers[name] = frame
            self._build_layer_grid(frame, config, "ar" if "ar" in name else "en")
            
    def _build_layer_grid(self, parent_frame, rows, lang_hint):
        for r_idx, keys in enumerate(rows):
            row_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
            row_frame.pack(fill="x", expand=True, pady=1)
            
            for key in keys:
                self._create_key(row_frame, key, lang_hint)
                
    def _create_key(self, parent, key, lang_hint):
        # Style logic
        is_action = key in ["⌫", "إدخال", "Enter", "مسافة", "Space", "⇧", "⬆", "ar", "en", "sym", "١٢٣", "?123"]
        
        # Calculate dynamic width
        width = 40
        if key in ["مسافة", "Space"]: width = 320
        elif key in ["إدخال", "Enter"]: width = 110
        elif key in ["⌫", "⇧", "⬆"]: width = 70
        elif key in ["ar", "en", "sym"]: width = 60
        
        # Display text mapping
        disp = key
        if key == "ar": disp = "عربي"
        elif key == "en": disp = "ENG"
        elif key == "sym": disp = "?123"
        
        # Font logic (Arabic vs English font)
        font_family = FONTS["family"] if lang_hint == "ar" and not is_action else FONTS["family_en"]
        
        # Shape Arabic if needed (though single letters usually don't need it, but for safety)
        final_text = _(disp) if lang_hint == "ar" else disp
        
        btn = ctk.CTkButton(
            parent, text=final_text, width=width, height=36,
            font=(font_family, 15, "bold"),
            fg_color=COLORS["bg_tertiary"] if is_action else COLORS["bg_card"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["primary"],
            border_width=1, border_color=COLORS["border"],
            corner_radius=4,
            command=lambda k=key: self._handle_press(k)
        )
        # Pack right-to-left for Arabic hint
        btn.pack(side="right" if lang_hint == "ar" else "left", padx=1, pady=1, expand=True if not is_action else False)

    def _switch_layer(self, layer_name):
        """Hide all and show targeted layer instantly."""
        for frame in self.layers.values():
            frame.pack_forget()
        
        self.layers[layer_name].pack(fill="both", expand=True)
        self.current_layer = layer_name

    def _handle_press(self, key):
        if key == "⌫":
            self._backspace()
        elif key == "Space" or key == "مسافة":
            self._insert(" ")
        elif key == "Enter" or key == "إدخال":
            self._enter()
        elif key == "ar":
            self._switch_layer("ar")
        elif key == "en":
            self._switch_layer("en_low")
        elif key == "sym":
            self._switch_layer("sym")
        elif key in ["⇧", "⬆"]:
            target = "en_up" if self.current_layer == "en_low" else "en_low"
            self._switch_layer(target)
        else:
            self._insert(key)
            # Auto-revert shift after one press if it was active
            if self.current_layer == "en_up":
                self._switch_layer("en_low")

    def _insert(self, char):
        if not self.target: return
        self.target.insert("insert", char)
        self.target.focus_set()

    def _backspace(self):
        if not self.target: return
        try:
            if isinstance(self.target, ctk.CTkEntry):
                pos = self.target.index("insert")
                if pos > 0:
                    self.target.delete(pos-1, pos)
            else:
                curr = self.target.index("insert")
                self.target.delete(f"{curr}-1c", curr)
        except:
            pass
        self.target.focus_set()

    def _enter(self):
        if self.target:
            self.target.event_generate("<Return>")
        self.destroy()

def show_keyboard(master, target):
    return VirtualKeyboard(master, target)
