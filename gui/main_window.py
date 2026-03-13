"""
AI Robot Operating System - Main Window
نظام تشغيل الروبوت الطبي الذكي - النافذة الرئيسية

The main application window that contains all screens
and handles navigation between them.

النافذة الرئيسية للتطبيق التي تحتوي على جميع الشاشات
وتتعامل مع التنقل بينها.
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
from gui.styles.theme import COLORS, FONTS, RADIUS, configure_customtkinter
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


class MainWindow(ctk.CTk):
    """
    Main Application Window
    النافذة الرئيسية للتطبيق
    """
    
    def __init__(self):
        try:
            import ctypes
            myappid = 'mariam.ai.medical.robot.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
        
        super().__init__()
        
        configure_customtkinter()
        
        self.title("AI Medical Robot - نظام الروبوت الطبي الذكي")
        self.geometry(f"{config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT}")
        
        if config.APP_FULLSCREEN:
            self.attributes("-fullscreen", True)
        
        self.minsize(800, 480)
        
        self.configure(fg_color=COLORS["bg_primary"])
        
        self._set_icon()
        
        self.screens = {}
        self.current_screen = None
        self.voice_permission_granted = config.VOICE_ENABLED
        self.keyboard_window = None
        
        # Global binding for on-screen keyboard
        self.bind_all("<FocusIn>", self._handle_widget_focus)
        
        self.after(100, self._start_services_async)
        
        self.show_screen("home")
        
        self.after(1000, self._play_welcome)
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self.bind("<Escape>", lambda e: self._toggle_fullscreen())
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
    
    def _set_icon(self):
        try:
            import os
            
            ico_path = os.path.join(config.BASE_DIR, "assets", "icon.ico")
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
                print("✅ Application icon set")
            else:
                print(f"⚠️ Icon not found: {ico_path}")
        except Exception as e:
            print(f"⚠️ Could not set icon: {e}")
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=0
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
    def _handle_widget_focus(self, event):
        """Global handler to trigger keyboard on focus - معالج عالمي لتفعيل الكيبورد"""
        widget = event.widget
        
        # Check if the widget is an Entry or Textbox (or their internal components)
        try:
            # CustomTkinter widgets often have internal entry components
            widget_parent = self.nametowidget(widget.winfo_parent())
            
            is_input = isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)) or \
                       isinstance(widget_parent, (ctk.CTkEntry, ctk.CTkTextbox))
            
            if is_input:
                target = widget if isinstance(widget, (ctk.CTkEntry, ctk.CTkTextbox)) else widget_parent
                self._open_virtual_keyboard(target)
        except:
            pass

    def _open_virtual_keyboard(self, target):
        """Open the virtual keyboard for a target widget - فتح الكيبورد للعنصر المستهدف"""
        # Close existing if open
        if self.keyboard_window and self.keyboard_window.winfo_exists():
            if self.keyboard_window.target == target:
                return # Already open for this widget
            self.keyboard_window.destroy()
            
        self.keyboard_window = VirtualKeyboard(self, target_widget=target)
    
    def _create_sidebar(self):
        """Create sidebar navigation - إنشاء شريط التنقل الجانبي"""
        nav_items = [
            {"key": "home", "text": "الرئيسية", "icon": "🏠"},
            {"key": "food", "text": "تحليل الطعام", "icon": "📷"},
            {"key": "chat", "text": "المحادثة", "icon": "💬"},
            {"key": "meds", "text": "الأدوية", "icon": "💊"},
            {"key": "qr", "text": "بوابة المريض", "icon": "📱"},
        ]
        
        self.sidebar = SidebarNav(
            self,
            items=nav_items,
            on_select=self._on_nav_select,
            on_exit=self._on_close,
            width=160
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.sidebar.set_voice_callback(self.toggle_voice_permission)
    
    def _create_content_area(self):
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_primary"],
            corner_radius=0
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
    
    def _get_screen(self, key: str):
        if key in self.screens:
            return self.screens[key]
            
        print(f"⌛ Lazy loading screen: {key}")
        
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
        """
        Show a specific screen with lazy loading
        عرض شاشة معينة مع التحميل المتأخر
        """
        if self.current_screen:
            current = self.screens.get(self.current_screen)
            if current:
                current.grid_forget()
                if hasattr(current, 'on_hide'):
                    current.on_hide()
        
        new_screen = self._get_screen(screen_key)
        if not new_screen:
            print(f"❌ Screen not found: {screen_key}")
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
            print("🚀 Starting background services...")
            self._start_monitoring()
            self._start_medication_reminder()
            self._init_voice_assistant()
            print("✅ Background services started.")
            
        threading.Thread(target=run_init, daemon=True).start()
    
    def _start_monitoring(self):
        vital_signs_monitor.add_callback(self._on_vitals_update)
        vital_signs_monitor.start_monitoring()

    def _on_vitals_update(self, vitals):
        if "home" in self.screens:
            formatted = vital_signs_monitor.get_formatted_vitals()
            self.screens["home"].update_vitals(formatted)
            
    def _start_medication_reminder(self):
        medication_reminder.add_callback(self._on_medication_alert)
        medication_reminder.start_scheduler()
        
    def _on_medication_alert(self, alert):
        med = alert.medication
        display_message = alert.message if alert.message else f"حان وقت العلاج: {med.name}\nالجرعة: {med.dose}"
        voice_text = alert.voice_message if alert.voice_message else f"حان وقت العلاج، {med.name.split(' ')[0]}"
        
        self.after(500, lambda: voice_assistant.speak(voice_text, wait=False))
        
        def mark_taken():
            medication_reminder.mark_as_taken(med.name)
            if "meds" in self.screens and hasattr(self.screens["meds"], "_populate_medications"):
                self.screens["meds"]._populate_medications()
                
        self.after(0, lambda: self.show_alert(
            title="تنبيه دواء ⏰", 
            message=display_message, 
            alert_type="warning",
            action_text="تم تناول الدواء",
            action_callback=mark_taken
        ))
    
    def _toggle_fullscreen(self):
        current = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not current)
    
    def _init_voice_assistant(self):
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
    
    def _play_welcome(self):
        import threading
        
        def welcome_flow():
            voice_assistant.speak("أهلاً بيك يا غالي! أنا مساعدك الطبي. أنا موجود هنا عشانك وعشان صحتك.")
            voice_assistant.speak("تسمحلي أسمعك وأتكلم معاك؟")
        
        threading.Thread(target=welcome_flow, daemon=True).start()
    
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
        self.after(500, lambda: voice_assistant.speak("أنا أستمع إليك، تحدث معي", wait=False))
    
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
        except Exception as e:
            print(f"⚠️ Failed to set sugar value: {e}")
    
    def _set_sugar_value(self, value: str):
        try:
            vital_signs_monitor.set_manual_reading("sugar", float(value))
            qr_screen = self.screens.get("qr")
            if qr_screen and hasattr(qr_screen, "update_vitals_display"):
                self.after(500, qr_screen.update_vitals_display)
        except Exception as e:
            print(f"⚠️ _set_sugar_value failed: {e}")
    
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
        
        return enabled
    
    def _on_close(self):
        voice_assistant.stop_listening()
        vital_signs_monitor.stop_monitoring()
        medication_reminder.stop_scheduler()
        self.destroy()
    
    def show_alert(self, title: str, message: str, alert_type: str = "info", action_text: str = None, action_callback = None):
        colors = {
            "info": COLORS["info"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error": COLORS["danger"],
        }
        
        color = colors.get(alert_type, COLORS["info"])
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("400x250")
        dialog.configure(fg_color=COLORS["bg_secondary"])
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - 200
        y = (self.winfo_screenheight() // 2) - 125
        dialog.geometry(f"+{x}+{y}")
        
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        icon = icons.get(alert_type, "ℹ️")
        
        ctk.CTkLabel(
            dialog,
            text=icon,
            font=(FONTS["family"], 40),
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            dialog,
            text=message,
            font=(FONTS["family"], FONTS["size_md"]),
            text_color=COLORS["text_primary"],
            wraplength=350
        ).pack(pady=10)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=20)
        
        def close_dialog():
            dialog.destroy()
            
        if action_text and action_callback:
            def on_action():
                action_callback()
                close_dialog()
                
            ctk.CTkButton(
                btn_frame,
                text=action_text,
                font=(FONTS["family"], FONTS["size_md"]),
                fg_color=COLORS["success"],
                hover_color="#059669",
                command=on_action
            ).pack(side="right", expand=True, padx=5)
            
            dismiss_text = "تأجيل"
        else:
            dismiss_text = "حسناً"
        
        ctk.CTkButton(
            btn_frame,
            text=dismiss_text,
            font=(FONTS["family"], FONTS["size_md"]),
            fg_color=color if not action_text else "#6b7280",
            hover_color=color if not action_text else "#4b5563",
            command=close_dialog
        ).pack(side="left", expand=True, padx=5)


def run_app():
    if not config.validate():
        print("❌ Configuration validation failed")
        return
    
    if config.DEBUG_MODE:
        config.print_config()
    
    use_new = False
    try:
        import os
        if os.getenv("USE_NEW_UI") in ("1", "true", "True"):
            use_new = True
    except:
        pass
    if getattr(config, "NEW_UI", False):
        use_new = True
    
    if use_new:
        print("🔀 Launching new PySide6 GUI")
        try:
            from gui_new import main as new_gui_main
            new_gui_main.run()
            return
        except Exception as e:
            print(f"⚠️ Failed to launch new GUI: {e}")
    
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run_app()
