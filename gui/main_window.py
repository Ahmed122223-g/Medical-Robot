"""
AI Robot Operating System - Main Window
The main application window that contains all screens
and handles navigation between them.
"""

import customtkinter as ctk
import sys
from typing import Optional
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

sys.path.append('..')
from config import config
from gui.styles.theme import COLORS, FONTS, RADIUS, configure_customtkinter, responsive
from gui.widgets.nav_button import SidebarNav
from gui.screens.home_screen import HomeScreen
from gui.screens.food_screen import FoodScreen
from gui.screens.chat_screen import ChatScreen
from gui.screens.meds_screen import MedsScreen
from modules.vital_signs import vital_signs_monitor
from modules.voice_assistant import voice_assistant
from modules.voice_command_processor import voice_command_processor
from modules.medication_reminder import medication_reminder
from gui.widgets.keyboard import VirtualKeyboard
from core.arabic_utils import fix_arabic as _


class MainWindow(ctk.CTk):
    """Main Application Window"""
    
    def __init__(self):
        try:
            import ctypes
            myappid = 'mariam.ai.medical.robot.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
        
        super().__init__()
        
        configure_customtkinter()
        
        self.title("AI Medical Robot")
        self.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        if config.APP_FULLSCREEN:
            import sys
            if sys.platform == "win32":
                # Calculate screen dimensions and set it directly to avoid the 'zoomed' flash animation
                w = self.winfo_screenwidth()
                h = self.winfo_screenheight()
                self.geometry(f"{w}x{h}+0+0")
            else:
                self.attributes("-fullscreen", True)
        
        self.minsize(800, 480)
        
        self.configure(fg_color=COLORS["bg_primary"])
        
        self._set_icon()
        
        self.screens = {}
        self.current_screen = None
        self.voice_permission_granted = config.VOICE_ENABLED
        # Bind resize to update responsive manager
        self.bind("<Configure>", self._on_window_resize)
        self.minsize(800, 480)
        
        # Determine actual window size for scaling
        current_w = config.SCREEN_WIDTH
        current_h = config.SCREEN_HEIGHT
        if config.APP_FULLSCREEN:
            try:
                current_w = self.winfo_screenwidth()
                current_h = self.winfo_screenheight()
            except:
                pass
                
        # Initialize responsive manager BEFORE creating layout!
        responsive.update(current_w, current_h)
        
        self.screens = {}
        self.current_screen: Optional[str] = None
        self._resize_timer = None
        
        self.keyboard = None
        self._create_layout()
        
        self.voice_permission_granted = True  # Start enabled until user responds to permission question
        
        self.after(100, self._start_services_async)
        
        self.show_screen("home")
        
        self.after(1500, self._play_welcome)
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.bind("<Escape>", lambda e: self._toggle_fullscreen())
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
    
    def _init_responsive(self):
        """Initialize responsive manager with current content area size."""
        w = self.content_frame.winfo_width()
        h = self.content_frame.winfo_height()
        if w > 100 and h > 100:
            responsive.update(w, h)
    
    def _on_window_resize(self, event=None):
        """Debounced window resize handler to update responsive manager."""
        if event and event.widget != self:
            return
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(100, self._apply_resize)
    
    def _apply_resize(self):
        """Apply resize: update responsive manager with current content area dims."""
        try:
            w = self.content_frame.winfo_width()
            h = self.content_frame.winfo_height()
            if w > 100 and h > 100:
                responsive.update(w, h)
        except Exception:
            pass
    
    def _set_icon(self):
        try:
            import os
            ico_path = os.path.join(config.BASE_DIR, "assets", "icon.ico")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
        except Exception:
            pass
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=140)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        
        # Right side: content + keyboard container
        self.right_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(1, weight=0) # Keyboard row
        
        self.content_frame = ctk.CTkFrame(self.right_frame, fg_color=COLORS["bg_primary"], corner_radius=0)
        self.content_frame.grid(row=0, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Create the embedded keyboard (hidden initially)
        self.keyboard = VirtualKeyboard(self.right_frame)
        
        # Single unified click handler for keyboard show/hide
        self.bind_all("<Button-1>", self._handle_click_for_keyboard)
        
    def _find_input_widget(self, widget):
        """Check if widget or its parent is a CTkEntry/CTkTextbox. Returns the CTk widget or None."""
        import tkinter as tk
        
        # Direct check
        if isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)):
            return widget
        
        # Check if it's an internal tk widget of a CTk input
        if isinstance(widget, (tk.Entry, tk.Text)):
            if hasattr(widget, 'master') and isinstance(widget.master, (ctk.CTkEntry, ctk.CTkTextbox)):
                return widget.master
        
        # Walk up parents (for other internal widgets)
        parent = widget
        for _ in range(5):
            parent = parent.master if hasattr(parent, 'master') else None
            if parent is None:
                break
            if isinstance(parent, (ctk.CTkEntry, ctk.CTkTextbox)):
                return parent
        
        return None
    
    def _handle_click_for_keyboard(self, event):
        """Unified click handler: show keyboard on input tap, hide on outside tap."""
        try:
            clicked = event.widget
            
            # If clicked inside the keyboard itself, do nothing (let keyboard handle it)
            if self.keyboard and self._is_child_of(clicked, self.keyboard):
                return
            
            # Check if clicked on an input field
            input_widget = self._find_input_widget(clicked)
            
            if input_widget:
                # Clicked on input field -> show keyboard after a short delay
                # The delay ensures the click is fully processed first
                if self.keyboard:
                    self.after(150, lambda w=input_widget: self.keyboard.show(w))
            else:
                # Clicked outside input field and keyboard -> hide keyboard
                if self.keyboard and self.keyboard.is_visible:
                    self.keyboard.hide()
        except:
            pass
    
    def _is_child_of(self, widget, parent):
        """Check if widget is a child of parent."""
        try:
            w = widget
            while w:
                if w == parent:
                    return True
                w = w.master if hasattr(w, 'master') else None
            return False
        except:
            return False
    
    def _create_sidebar(self):
        """Create sidebar navigation"""
        nav_items = [
            {"key": "home", "text": "Home", "icon": "🏠"},
            {"key": "food", "text": "Food Analysis", "icon": "📷"},
            {"key": "chat", "text": "Chat", "icon": "💬"},
            {"key": "meds", "text": "Medications", "icon": "💊"},
            {"key": "qr", "text": "Patient Portal", "icon": "📱"},
        ]
        
        self.sidebar = SidebarNav(
            self,
            items=nav_items,
            on_select=self._on_nav_select,
            on_exit=self._on_close,
            width=140
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.sidebar.set_voice_callback(self.toggle_voice_permission)
    
    def _get_screen(self, key: str):
        if key in self.screens:
            return self.screens[key]
        
        if key == "home":
            from gui.screens.home_screen import HomeScreen
            self.screens["home"] = HomeScreen(self.content_frame, app_controller=self)
        elif key == "food":
            from gui.screens.food_screen import FoodScreen
            self.screens["food"] = FoodScreen(self.content_frame, app_controller=self)
        elif key == "chat":
            from gui.screens.chat_screen import ChatScreen
            self.screens["chat"] = ChatScreen(self.content_frame, app_controller=self)
        elif key == "meds":
            from gui.screens.meds_screen import MedsScreen
            self.screens["meds"] = MedsScreen(self.content_frame, app_controller=self)
        elif key == "qr":
            from gui.screens.qr_screen import QRCodeScreen
            self.screens["qr"] = QRCodeScreen(self.content_frame)
            
        if key in self.screens:
            self.screens[key].grid_forget()
            return self.screens[key]
        return None
    
    def _on_nav_select(self, key: str):
        self.show_screen(key)
    
    def show_screen(self, screen_key: str):
        """Show a specific screen with lazy loading"""
        if self.current_screen:
            current = self.screens.get(self.current_screen)
            if current:
                current.grid_forget()
                if hasattr(current, 'on_hide'):
                    current.on_hide()
        
        new_screen = self._get_screen(screen_key)
        if not new_screen:
            return
            
        new_screen.grid(row=0, column=0, sticky="nsew")
        
        if hasattr(new_screen, 'on_show'):
            new_screen.on_show()
        
        self.current_screen = screen_key
        
        voice_command_processor.set_current_screen(screen_key)
        
        self.sidebar.select(screen_key)
    
    def _start_services_async(self):
        import threading
        
        def run_init():
            self._start_monitoring()
            self._start_medication_reminder()
            self._init_voice_assistant(start_listening=False)  # Don't start listening yet
            
        threading.Thread(target=run_init, daemon=True).start()
    
    def _start_monitoring(self):
        vital_signs_monitor.add_callback(self._on_vitals_update)
        vital_signs_monitor.start_monitoring()

    def _on_vitals_update(self, vitals):
        if "home" in self.screens:
            formatted = vital_signs_monitor.get_formatted_vitals()
            self.after(0, lambda f=formatted: self.screens["home"].update_vitals(f))
            
    def _start_medication_reminder(self):
        medication_reminder.add_callback(self._on_medication_alert)
        medication_reminder.start_scheduler()
        
    def _on_medication_alert(self, alert):
        med = alert.medication
        display_message = alert.message if alert.message else f"Time for medication: {med.name}\nDose: {med.dose}"
        voice_text = alert.voice_message if alert.voice_message else f"حان وقت العلاج، {med.name.split(' ')[0]}"
        
        self.after(500, lambda: voice_assistant.speak(voice_text, wait=False))
        
        def mark_taken():
            medication_reminder.mark_as_taken(med.name)
            if "meds" in self.screens and hasattr(self.screens["meds"], "_populate_medications"):
                self.screens["meds"]._populate_medications()
                
        self.after(0, lambda: self.show_alert(
            title="Medication Alert ⏰", 
            message=display_message, 
            alert_type="warning",
            action_text="Taken",
            action_callback=mark_taken
        ))
    
    def _toggle_fullscreen(self):
        current = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not current)
    
    def _init_voice_assistant(self, start_listening=True):
        voice_assistant.set_command_callback(self._on_voice_command)
        voice_assistant.set_speech_callback(self._on_voice_speech)
        
        voice_command_processor.set_callback("open_food", self._cmd_open_food)
        voice_command_processor.set_callback("capture_food", self._cmd_capture_food)
        voice_command_processor.set_callback("close_food", self._cmd_close_food)
        voice_command_processor.set_callback("open_chat", self._cmd_open_chat)
        voice_command_processor.set_callback("close_current", self._cmd_close_current)
        voice_command_processor.set_callback("go_home", self._cmd_go_home)
        voice_command_processor.set_callback("exit_app", self._cmd_exit_app)
        voice_command_processor.set_callback("general_chat", self._cmd_general_chat)
        voice_command_processor.set_callback("speak", lambda text: voice_assistant.speak(text, wait=False))
        voice_command_processor.set_callback("open_qr", self._cmd_open_qr)
        voice_command_processor.set_callback("set_sugar", self._cmd_set_sugar)
        voice_command_processor.set_callback("generate_qr", self._cmd_generate_qr)
        voice_command_processor.set_callback("open_browser", self._cmd_open_browser)
        
        if start_listening and self.voice_permission_granted:
            voice_assistant.set_voice_permission(True)
            voice_assistant.start_listening()
    
    def _play_welcome(self):
        import threading
        
        # Show voice button as active from the start
        self.sidebar.set_voice_state(True)
        
        def welcome_flow():
            # Speak welcome, then ask permission (loops until clear yes/no)
            voice_assistant.speak("مرحباً بكم. أنا المساعد الطبي الذكي، مصمم لتقديم خدمات الرعاية والمتابعة الصحية.")
            
            # ask_permission loops internally until clear yes/no
            voice_assistant.ask_permission(
                callback=lambda approved: self.after(0, lambda: self._on_voice_permission(approved))
            )
        
        threading.Thread(target=welcome_flow, daemon=True).start()
    
    def _on_voice_permission(self, approved: bool):
        """Handle voice permission response from user."""
        self.voice_permission_granted = approved
        voice_assistant.set_voice_permission(approved)
        
        if approved:
            voice_assistant.start_listening()
            self.sidebar.set_voice_state(True)
        else:
            voice_assistant.stop_listening()
            self.sidebar.set_voice_state(False)
    
    def _on_voice_command(self, command: str, text: str):
        def process():
            response = voice_command_processor.process_command(text)
            if response:
                voice_assistant.speak(response, wait=False)
        
        self.after(0, process)
    
    def _on_voice_speech(self, text: str):
        def process():
            response = voice_command_processor.process_command(text)
            if response:
                voice_assistant.speak(response, wait=False)
        
        self.after(0, process)
    
    def _cmd_open_food(self):
        self.after(0, lambda: self.show_screen("food"))
        self.after(500, lambda: self.screens.get("food") and hasattr(self.screens["food"], "_start_camera") and self.screens["food"]._start_camera())
    
    def _cmd_capture_food(self):
        food_screen = self.screens.get("food")
        if food_screen and hasattr(food_screen, "_capture_and_analyze"):
            self.after(0, food_screen._capture_and_analyze)
    
    def _cmd_close_food(self):
        if self.screens.get("food") and hasattr(self.screens["food"], "_stop_camera"):
            self.after(0, self.screens["food"]._stop_camera)
    
    def _cmd_open_chat(self):
        self.after(0, lambda: self.show_screen("chat"))
        self.after(500, lambda: voice_assistant.speak("المساعد الذكي قيد الاستماع الآن. تفضل بطرح سؤالك.", wait=False))
    
    def _cmd_close_current(self):
        if self.current_screen == "food":
            self._cmd_close_food()
        self.after(0, lambda: self.show_screen("home"))
    
    def _cmd_go_home(self):
        if self.current_screen == "food":
            self._cmd_close_food()
        self.after(0, lambda: self.show_screen("home"))
    
    def _cmd_exit_app(self):
        self.after(2000, self._on_close)
    
    def _cmd_general_chat(self, text: str) -> str:
        if self.current_screen != "chat":
            self.after(0, lambda: self.show_screen("chat"))
            delay = 500
        else:
            delay = 100
        
        def send_to_chat():
            chat_screen = self.screens.get("chat")
            if chat_screen and hasattr(chat_screen, "process_voice_input"):
                speak = self.voice_permission_granted
                chat_screen.process_voice_input(text, auto_send=True, speak_response=speak)
        
        self.after(delay, send_to_chat)
        
        return None
    
    def _cmd_open_qr(self):
        self.after(0, lambda: self.show_screen("qr"))
        qr_screen = self.screens.get("qr")
        if qr_screen and hasattr(qr_screen, "update_vitals_display"):
            self.after(500, qr_screen.update_vitals_display)
    
    def _cmd_set_sugar(self, value: str):
        try:
            vital_signs_monitor.set_manual_reading("sugar", float(value))
            formatted = vital_signs_monitor.get_formatted_vitals()
            if "home" in self.screens:
                self.screens["home"].update_vitals(formatted)
        except Exception:
            pass
    
    def _set_sugar_value(self, value: str):
        try:
            vital_signs_monitor.set_manual_reading("sugar", float(value))
            qr_screen = self.screens.get("qr")
            if qr_screen and hasattr(qr_screen, "update_vitals_display"):
                self.after(500, qr_screen.update_vitals_display)
        except Exception:
            pass
    
    def _cmd_generate_qr(self):
        qr_screen = self.screens.get("qr")
        if qr_screen:
            if self.current_screen != "qr":
                self.after(0, lambda: self.show_screen("qr"))
                self.after(500, qr_screen.generate_qr)
            else:
                qr_screen.generate_qr()
    
    def _cmd_open_browser(self):
        import webbrowser
        qr_screen = self.screens.get("qr")
        if qr_screen and hasattr(qr_screen, "full_url"):
            webbrowser.open(qr_screen.full_url)
        else:
            webbrowser.open("https://medical-robot.netlify.app/")

    def toggle_voice_permission(self, enabled: bool = None):
        if enabled is None:
            enabled = not self.voice_permission_granted
        
        self.voice_permission_granted = enabled
        voice_assistant.set_voice_permission(enabled)
        
        if enabled:
            voice_assistant.start_listening()
        else:
            voice_assistant.stop_listening()
        
        # Sync sidebar button state
        self.sidebar.set_voice_state(enabled)
        
        return enabled
    
    def _on_close(self):
        voice_assistant.stop_listening()
        vital_signs_monitor.stop_monitoring()
        medication_reminder.stop_scheduler()
        self.destroy()
    
    def show_alert(self, title: str, message: str, alert_type: str = "info", action_text: str = None, action_callback = None):
        r = responsive
        colors = {
            "info": COLORS["info"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["danger"],
        }
        
        color = colors.get(alert_type, COLORS["info"])
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dw = r.size(380)
        dh = r.size(230)
        dialog.geometry(f"{dw}x{dh}")
        dialog.configure(fg_color=COLORS["bg_secondary"])
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (dw // 2)
        y = (self.winfo_screenheight() // 2) - (dh // 2)
        dialog.geometry(f"+{x}+{y}")
        
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        icon = icons.get(alert_type, "ℹ️")
        
        ctk.CTkLabel(
            dialog,
            text=icon,
            font=r.font_ar(base_size=32),
        ).pack(pady=(r.pad(12), r.pad(6)))
        
        ctk.CTkLabel(
            dialog,
            text=message,
            font=r.font(base_size=12),
            text_color=COLORS["text_primary"],
            wraplength=r.size(320)
        ).pack(pady=r.pad(6))
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=r.pad(12), fill="x", padx=r.pad(15))
        
        def close_dialog():
            dialog.destroy()
            
        if action_text and action_callback:
            def on_action():
                action_callback()
                close_dialog()
                
            ctk.CTkButton(
                btn_frame,
                text=action_text,
                font=r.font(base_size=12),
                fg_color=COLORS["success"],
                hover_color="#059669",
                command=on_action
            ).pack(side="right", expand=True, padx=r.pad(4))
            
            dismiss_text = "Postpone"
        else:
            dismiss_text = "OK"
        
        ctk.CTkButton(
            btn_frame,
            text=dismiss_text,
            font=r.font(base_size=12),
            fg_color=color if not action_text else "#6b7280",
            hover_color=color if not action_text else "#4b5563",
            command=close_dialog
        ).pack(side="left", expand=True, padx=r.pad(4))


def run_app():
    if not config.validate():
        return
    
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run_app()
