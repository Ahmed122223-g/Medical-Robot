"""
AI Robot Operating System - Navigation Button Widget
"""

import customtkinter as ctk
from typing import Callable, Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS, responsive
from core.arabic_utils import fix_arabic as _


class NavButton(ctk.CTkButton):
    def __init__(self, master, text: str, icon: str = "", command: Optional[Callable] = None, is_active: bool = False, **kwargs):
        self.is_active = is_active
        self._icon = icon
        self._text = text
        r = responsive
        default_kwargs = {
            "text": f"{icon}  {text}" if icon else text,
            "font": r.font(base_size=13),
            "fg_color": COLORS["primary_light"] if is_active else "transparent",
            "hover_color": COLORS["primary_light"] if is_active else COLORS["bg_secondary"],
            "text_color": COLORS["primary"] if is_active else COLORS["text_secondary"],
            "anchor": "w",
            "corner_radius": RADIUS["md"],
            "height": r.size(42),
            "border_width": 2 if is_active else 0,
            "border_color": COLORS["primary"] if is_active else COLORS["bg_sidebar"],
            "command": command,
        }
        default_kwargs.update(kwargs)
        super().__init__(master, **default_kwargs)
    
    def set_active(self, active: bool):
        self.is_active = active
        if active:
            self.configure(fg_color=COLORS["primary_light"], hover_color=COLORS["primary_light"],
                           text_color=COLORS["primary"], border_width=2, border_color=COLORS["primary"])
        else:
            self.configure(fg_color="transparent", hover_color=COLORS["bg_secondary"],
                           text_color=COLORS["text_secondary"], border_width=0)
    
    def update_text(self, text: str, icon: str = None):
        if icon is not None: self._icon = icon
        self._text = text
        display_text = f"{self._icon}  {text}" if self._icon else text
        self.configure(text=display_text)


class SidebarNav(ctk.CTkFrame):
    def __init__(self, master, items: list[dict], on_select: Optional[Callable[[str], None]] = None,
                 on_exit: Optional[Callable] = None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_sidebar"], corner_radius=0,
                         border_width=1, border_color=COLORS["border"], **kwargs)
        self.items = items
        self.on_select = on_select
        self.on_exit = on_exit
        self.buttons: dict[str, NavButton] = {}
        self.current_key: Optional[str] = None
        self._create_layout()
    
    def _create_layout(self):
        r = responsive
        self.grid_columnconfigure(0, weight=1)
        self.logo_frame = ctk.CTkFrame(self, fg_color="transparent", height=r.size(50))
        self.logo_frame.grid(row=0, column=0, sticky="ew", padx=r.pad(8), pady=(r.pad(10), r.pad(6)))
        self.logo_frame.grid_propagate(False)
        ctk.CTkLabel(self.logo_frame, text="🤖", font=r.font_ar(base_size=24)).pack(side="left", padx=r.pad(4))
        ctk.CTkLabel(self.logo_frame, text="Medical Robot", font=r.font(base_size=14, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).grid(row=1, column=0, sticky="ew", padx=r.pad(10), pady=r.pad(6))
        
        for i, item in enumerate(self.items):
            key = item.get("key", f"item_{i}")
            btn = NavButton(self, text=item.get("text", ""), icon=item.get("icon", ""),
                           command=lambda k=key: self._on_button_click(k), is_active=(i == 0))
            btn.grid(row=i+2, column=0, sticky="ew", padx=r.pad(8), pady=r.pad(2))
            self.buttons[key] = btn
            if i == 0: self.current_key = key
        
        self.grid_rowconfigure(len(self.items) + 2, weight=1)
        self.voice_enabled = False
        self.voice_btn = ctk.CTkButton(self, text="🔇 Enable Voice", font=r.font(base_size=11),
            fg_color=COLORS["bg_tertiary"], hover_color=COLORS["primary"], text_color=COLORS["text_secondary"],
            corner_radius=RADIUS["md"], height=r.size(34), command=self._toggle_voice)
        self.voice_btn.grid(row=len(self.items)+3, column=0, sticky="ew", padx=r.pad(8), pady=(r.pad(4), r.pad(2)))
        
        self.exit_btn = ctk.CTkButton(self, text="🚪 Exit", font=r.font(base_size=11),
            fg_color="transparent", hover_color=COLORS["danger"], text_color=COLORS["text_secondary"],
            border_width=1, border_color=COLORS["border"], corner_radius=RADIUS["md"], height=r.size(34), command=self.on_exit)
        self.exit_btn.grid(row=len(self.items)+4, column=0, sticky="ew", padx=r.pad(8), pady=(r.pad(2), r.pad(4)))
        
        self.on_voice_toggle = None
        ctk.CTkLabel(self, text="v1.0.0", font=r.font(base_size=9),
                     text_color=COLORS["text_muted"]).grid(row=len(self.items)+5, column=0, pady=r.pad(6))
    
    def _toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        self._update_voice_button()
        if self.on_voice_toggle: self.on_voice_toggle(self.voice_enabled)
    
    def _update_voice_button(self):
        if self.voice_enabled:
            self.voice_btn.configure(text="🎤 Voice Active", fg_color=COLORS["success"],
                                     hover_color=COLORS["success_hover"], text_color=COLORS["text_primary"])
        else:
            self.voice_btn.configure(text="🔇 Enable Voice", fg_color=COLORS["bg_tertiary"],
                                     hover_color=COLORS["primary"], text_color=COLORS["text_secondary"])
    
    def set_voice_callback(self, callback): self.on_voice_toggle = callback
    def set_voice_state(self, enabled: bool):
        self.voice_enabled = enabled
        self._update_voice_button()
    
    def _on_button_click(self, key: str):
        if key == self.current_key: return
        if self.current_key and self.current_key in self.buttons: self.buttons[self.current_key].set_active(False)
        if key in self.buttons: self.buttons[key].set_active(True)
        self.current_key = key
        if self.on_select: self.on_select(key)
    
    def select(self, key: str): self._on_button_click(key)
    def get_current(self) -> Optional[str]: return self.current_key


class QuickActionButton(ctk.CTkButton):
    def __init__(self, master, text: str, icon: str, color: str = None, command: Optional[Callable] = None, **kwargs):
        self.color = color or COLORS["primary"]
        r = responsive
        super().__init__(master, text=f"{icon}\n{text}", font=r.font(base_size=12, weight="bold"),
            fg_color=COLORS["bg_card"], hover_color=COLORS["bg_secondary"], text_color=self.color,
            border_width=2, border_color=self.color, corner_radius=RADIUS["lg"],
            command=command, **kwargs)
