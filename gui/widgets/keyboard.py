"""
AI Robot Operating System - Virtual Keyboard
Responsive on-screen keyboard with Arabic, English, and number layouts.
Auto-shows on input focus, hides on outside click or close button.
Uses grid layout for full responsiveness.
"""

import customtkinter as ctk
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from gui.styles.theme import COLORS, FONTS, RADIUS
from core.arabic_utils import fix_arabic as _

# Key layouts
LAYOUTS = {
    "en": [
        list("1234567890"),
        list("qwertyuiop"),
        list("asdfghjkl"),
        ["⇧"] + list("zxcvbnm") + ["⌫"],
        ["عربي", "123", " ", ".", "⏎", "✕"],
    ],
    "en_shift": [
        list("1234567890"),
        list("QWERTYUIOP"),
        list("ASDFGHJKL"),
        ["⇧"] + list("ZXCVBNM") + ["⌫"],
        ["عربي", "123", " ", ",", "⏎", "✕"],
    ],
    "ar": [
        list("١٢٣٤٥٦٧٨٩٠"),
        list("ضصثقفغعهخحج"),
        list("شسيبلاتنمكط"),
        list("ئءؤرىةوزظ") + ["⌫"],
        ["ENG", "123", " ", ".", "⏎", "✕"],
    ],
    "num": [
        list("789"),
        list("456"),
        list("123"),
        [".", "0", "⌫"],
        ["ENG", "عربي", " ", "⏎", "✕"],
    ],
}

# Special weights for keys (standard key = 1)
KEY_WEIGHTS = {" ": 5, "⏎": 2, "✕": 1.5, "⇧": 2, "⌫": 2, "ENG": 2, "عربي": 2, "123": 2}


class VirtualKeyboard(ctk.CTkFrame):
    """Embedded virtual keyboard widget - appears at bottom of window."""

    def __init__(self, master_window, **kwargs):
        super().__init__(master_window, fg_color=COLORS["bg_sidebar"], corner_radius=0,
                         border_width=1, border_color=COLORS["border"], height=230, **kwargs)
        
        self.master_window = master_window
        self.target = None
        self.current_layout = "en"
        self.shift_on = False
        self._visible = False
        
        # Pre-calculate row counts for weights
        self._build_ui()
    
    def _build_ui(self):
        """Build the keyboard UI with all layers pre-rendered."""
        # Top bar with drag handle and close
        top = ctk.CTkFrame(self, fg_color="transparent", height=24)
        top.pack(fill="x", padx=8, pady=(4, 0))
        top.pack_propagate(False)
        
        # Handle bar
        ctk.CTkFrame(top, fg_color=COLORS["border"], width=50, height=3,
                      corner_radius=2).place(relx=0.5, rely=0.5, anchor="center")
        
        # Close button
        ctk.CTkButton(top, text="✕", width=28, height=22, font=("Arial", 14),
                      fg_color="transparent", text_color=COLORS["text_muted"],
                      hover_color=COLORS["danger"], corner_radius=4,
                      command=self.hide).pack(side="right")
        
        # Container for keyboard layers
        self.layers_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.layers_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        
        # Pre-render all layers
        self.layer_frames = {}
        for name, rows in LAYOUTS.items():
            frame = ctk.CTkFrame(self.layers_frame, fg_color="transparent")
            self._build_rows(frame, rows, name)
            self.layer_frames[name] = frame
        
        # Show default
        self._show_layout("en")
    
    def _build_rows(self, parent, rows, layout_name):
        """Build key rows for a layout using grid."""
        for r_idx, row in enumerate(rows):
            rf = ctk.CTkFrame(parent, fg_color="transparent")
            rf.pack(fill="x", expand=True, pady=1)
            
            # Configure grid columns for the row to be proportional
            for c_idx, key in enumerate(row):
                # Proportional weights for different key types
                if key == " ":
                    weight = 4
                elif key in ["⏎", "⇧", "⌫", "✕", "ENG", "عربي", "123"]:
                    weight = 2
                else:
                    weight = 1
                rf.grid_columnconfigure(c_idx, weight=weight)
                self._make_key(rf, key, layout_name, c_idx)
    
    def _make_key(self, parent, key, layout_name, col_idx):
        """Create a single key button in the grid."""
        is_special = key in ("⌫", "⏎", "⇧", "✕", "ENG", "عربي", "123", " ")
        
        # Display text mapping
        if key == " ":
            disp = "Space" if "en" in layout_name else _("مسافة")
        elif key == "⏎":
            disp = "Enter" if "en" in layout_name else _("إدخال")
        elif key == "عربي":
            disp = _("عربي")
        else:
            disp = _(key) if layout_name == "ar" and len(key) == 1 and '\u0600' <= key <= '\u06FF' else key
        
        # Colors
        if key == "✕":
            fg = COLORS["danger"]
            hover = "#dc2626"
            tc = "#ffffff"
        elif is_special:
            fg = COLORS["bg_tertiary"]
            hover = COLORS["primary"]
            tc = COLORS["text_primary"]
        else:
            fg = COLORS["bg_card"]
            hover = COLORS["primary_light"]
            tc = COLORS["text_primary"]
        
        font_family = FONTS["family"] if (layout_name == "ar" and not is_special) else FONTS.get("family_en", "Arial")
        
        btn = ctk.CTkButton(
            parent, text=disp, height=44,
            font=(font_family, 14, "bold"),
            fg_color=fg, text_color=tc, hover_color=hover,
            border_width=1, border_color=COLORS["border"],
            corner_radius=5,
            command=lambda k=key, ln=layout_name: self._on_key(k, ln)
        )
        # Use grid with sticky="nsew" for full responsiveness
        btn.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
    
    def _show_layout(self, name):
        """Switch to a layout."""
        for f in self.layer_frames.values():
            f.pack_forget()
        if name in self.layer_frames:
            self.layer_frames[name].pack(fill="both", expand=True)
            self.current_layout = name
    
    def _on_key(self, key, layout_name):
        """Handle key press."""
        if key == "⌫":
            self._backspace()
        elif key == " ":
            self._insert(" ")
        elif key == "⏎":
            self._enter()
        elif key == "✕":
            self.hide()
        elif key == "⇧":
            if self.current_layout == "en":
                self._show_layout("en_shift")
            else:
                self._show_layout("en")
        elif key == "ENG":
            self._show_layout("en")
        elif key == "عربي":
            self._show_layout("ar")
        elif key == "123":
            self._show_layout("num")
        else:
            self._insert(key)
            # Auto-unshift after one character
            if self.current_layout == "en_shift":
                self._show_layout("en")
    
    def _insert(self, char):
        if not self.target:
            return
        try:
            if isinstance(self.target, ctk.CTkEntry):
                pos = self.target.index("insert")
                self.target.insert(pos, char)
            elif isinstance(self.target, ctk.CTkTextbox):
                self.target.insert("insert", char)
            self.target.focus_set()
        except:
            pass
    
    def _backspace(self):
        if not self.target:
            return
        try:
            if isinstance(self.target, ctk.CTkEntry):
                pos = self.target.index("insert")
                if pos > 0:
                    self.target.delete(pos - 1, pos)
            elif isinstance(self.target, ctk.CTkTextbox):
                self.target.delete("insert-1c", "insert")
            self.target.focus_set()
        except:
            pass
    
    def _enter(self):
        if self.target:
            self.target.event_generate("<Return>")
        self.hide()
    
    def show(self, target_widget):
        """Show keyboard for a specific input widget."""
        self.target = target_widget
        if not self._visible:
            self._visible = True
            # Use grid for better alignment with the parent frame's layout
            self.grid(row=1, column=0, sticky="ew")
            self.lift()
    
    def hide(self):
        """Hide the keyboard."""
        if self._visible:
            self._visible = False
            self.grid_forget()
            self.target = None
    
    @property
    def is_visible(self):
        return self._visible


def show_keyboard(master, target):
    """Compatibility function - returns keyboard instance."""
    return None
