"""
AI Robot Operating System - Chat Screen
نظام تشغيل الروبوت الطبي الذكي - شاشة المحادثة

Chat interface for conversing with the AI chatbot.
واجهة المحادثة للتحدث مع الشات بوت الذكي.
"""

import customtkinter as ctk
from datetime import datetime
import threading
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS
from modules.chatbot import chatbot, Message


class ChatBubble(ctk.CTkFrame):
    """
    Chat message bubble
    فقاعة رسالة المحادثة
    """
    
    def __init__(self, master, message: str, is_user: bool, timestamp: datetime = None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["primary"] if is_user else COLORS["bg_secondary"],
            corner_radius=RADIUS["lg"],
            border_width=1 if not is_user else 0,
            border_color=COLORS["border_light"] if not is_user else COLORS["primary"],
            **kwargs
        )
        
        self.is_user = is_user
        
        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            font=(FONTS["family"], FONTS["size_md"]),
            text_color=COLORS["text_white"] if is_user else COLORS["text_primary"],
            anchor="e" if is_user else "w",
            justify="right" if is_user else "left",
            wraplength=320
        )
        self.message_label.pack(padx=20, pady=12)
        
        if timestamp:
            time_str = timestamp.strftime("%H:%M")
            self.time_label = ctk.CTkLabel(
                self,
                text=time_str,
                font=(FONTS["family_en"], FONTS["size_xs"]),
                text_color=COLORS["text_muted"],
                anchor="e" if is_user else "w"
            )
            self.time_label.pack(padx=15, pady=(0, 5))


class ChatScreen(ctk.CTkFrame):
    """
    Chat Screen
    شاشة المحادثة
    """
    
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        
        self.app = app_controller
        self.is_waiting_response = False
        
        self._create_layout()
        self._show_greeting()
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="💬 المحادثة الذكية",
            font=(FONTS["family"], FONTS["size_2xl"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="e"
        )
        self.title_label.pack(side="right")
        
        self.clear_btn = ctk.CTkButton(
            self.title_frame,
            text="🗑️ مسح المحادثة",
            font=(FONTS["family"], FONTS["size_sm"]),
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["danger"],
            width=120,
            height=30,
            command=self._clear_chat
        )
        self.clear_btn.pack(side="left")
        
        self._create_chat_area()
        
        self._create_input_area()
    
    def _create_chat_area(self):
        self.chat_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.messages_frame = ctk.CTkScrollableFrame(
            self.chat_frame,
            fg_color="transparent"
        )
        self.messages_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_input_area(self):
        self.input_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
            height=80
        )
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.input_frame.grid_propagate(False)
        
        self.input_container = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.input_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.message_entry = ctk.CTkEntry(
            self.input_container,
            placeholder_text="اكتب رسالتك هنا...",
            font=(FONTS["family"], FONTS["size_md"]),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            height=45
        )
        self.message_entry.pack(side="right", fill="x", expand=True, padx=(10, 0))
        self.message_entry.bind("<Return>", lambda e: self._send_message())
        
        self.send_btn = ctk.CTkButton(
            self.input_container,
            text="📤",
            font=(FONTS["family"], 20),
            width=50,
            height=45,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=RADIUS["md"],
            command=self._send_message
        )
        self.send_btn.pack(side="right")
        
        self.quick_frame = ctk.CTkFrame(self.input_container, fg_color="transparent")
        self.quick_frame.pack(side="left", fill="y")
        
        self.med_btn = ctk.CTkButton(
            self.quick_frame,
            text="💊",
            font=(FONTS["family"], 18),
            width=40,
            height=40,
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["warning"],
            corner_radius=RADIUS["md"],
            command=self._request_medication_reminder
        )
        self.med_btn.pack(side="left", padx=2)
    
    def _show_greeting(self):
        greeting = chatbot.get_greeting()
        self._add_message(greeting, is_user=False)
    
    def _add_message(self, text: str, is_user: bool = True):
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        container.pack(fill="x", pady=5)
        
        bubble = ChatBubble(
            container,
            message=text,
            is_user=is_user,
            timestamp=datetime.now()
        )
        
        if is_user:
            bubble.pack(anchor="e", padx=(50, 0))
        else:
            bubble.pack(anchor="w", padx=(0, 50))
        
        self.messages_frame._parent_canvas.yview_moveto(1.0)
    
    def _add_typing_indicator(self):
        self.typing_container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        self.typing_container.pack(fill="x", pady=5)
        
        self.typing_bubble = ctk.CTkFrame(
            self.typing_container,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=RADIUS["lg"]
        )
        self.typing_bubble.pack(anchor="w", padx=(0, 50))
        
        self.typing_label = ctk.CTkLabel(
            self.typing_bubble,
            text="🤖 جاري الكتابة...",
            font=(FONTS["family"], FONTS["size_md"]),
            text_color=COLORS["text_muted"]
        )
        self.typing_label.pack(padx=15, pady=10)
    
    def _remove_typing_indicator(self):
        if hasattr(self, 'typing_container'):
            self.typing_container.destroy()
    
    def _send_message(self):
        if self.is_waiting_response:
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        self.message_entry.delete(0, 'end')
        
        self._add_message(message, is_user=True)
        
        self._add_typing_indicator()
        self.is_waiting_response = True
        
        self.send_btn.configure(state="disabled")
        
        def get_response():
            response = chatbot.send_message(message)
            self.after(0, lambda: self._handle_response(response))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def _handle_response(self, response: str):
        self._remove_typing_indicator()
        self.is_waiting_response = False
        self.send_btn.configure(state="normal")
        
        self._add_message(response, is_user=False)
    
    def _request_medication_reminder(self):
        reminder = chatbot.get_medication_reminder()
        self._add_message(reminder, is_user=False)
    
    def _clear_chat(self):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        chatbot.clear_history()
        
        self._show_greeting()
    
    def on_hide(self):
        pass
    
    def on_show(self):
        self.message_entry.focus()
    
    def process_voice_input(self, text: str, auto_send: bool = True, speak_response: bool = True):
        """
        Process voice input from microphone
        معالجة الإدخال الصوتي من المايكروفون
        
        Args:
            text: The spoken text
            auto_send: If True, automatically send the message
            speak_response: If True, speak the AI response
        """
        if self.is_waiting_response:
            return
        
        if not text or not text.strip():
            return
        
        self.message_entry.delete(0, 'end')
        self.message_entry.insert(0, text)
        self.message_entry.update()
        
        if not auto_send:
            return
        
        self.after(300, lambda: self._send_voice_message(text, speak_response))
    
    def _send_voice_message(self, text: str, speak_response: bool = True):
        if self.is_waiting_response:
            return
        
        self.message_entry.delete(0, 'end')
        
        self._add_message(text, is_user=True)
        
        self._add_typing_indicator()
        self.is_waiting_response = True
        self.send_btn.configure(state="disabled")
        
        def get_response():
            response = chatbot.send_message(text)
            self.after(0, lambda: self._handle_voice_response(response, speak_response))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def _handle_voice_response(self, response: str, speak_response: bool = True):
        self._remove_typing_indicator()
        self.is_waiting_response = False
        self.send_btn.configure(state="normal")
        
        self._add_message(response, is_user=False)
        
        if speak_response:
            try:
                from modules.voice_assistant import voice_assistant
                voice_assistant.speak(response, wait=False)
            except Exception as e:
                print(f"⚠️ Could not speak response: {e}")
