"""
AI Robot Operating System - Chat Screen
Chat interface for conversing with the AI chatbot.
Fully responsive - text scales with window size.
"""

import customtkinter as ctk
from datetime import datetime
import threading
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS, responsive
from core.arabic_utils import fix_arabic as _
from modules.chatbot import chatbot, Message


class ChatBubble(ctk.CTkFrame):
    """Chat message bubble - responsive"""
    
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
        r = responsive
        
        # Dynamic wraplength based on window width
        wrap_pixels = max(200, int(r.w * 0.35))
        # Estimate characters that fit in the wrap_pixels (assuming ~8px per char)
        char_wrap = max(30, int(wrap_pixels / 8))
        
        self.message_label = ctk.CTkLabel(
            self,
            text=_(message, wrap_length=char_wrap),
            font=r.font_ar(base_size=12),
            text_color=COLORS["text_white"] if is_user else COLORS["text_primary"],
            anchor="e",
            justify="right"
            # Do NOT use native wraplength as it breaks BiDi text lines
        )
        self.message_label.pack(padx=r.pad(14), pady=r.pad(8), fill="both", expand=True)
        
        if timestamp:
            time_str = timestamp.strftime("%H:%M")
            self.time_label = ctk.CTkLabel(
                self,
                text=time_str,
                font=r.font(base_size=8),
                text_color=COLORS["text_muted"],
                anchor="w"
            )
            self.time_label.pack(padx=r.pad(10), pady=(0, r.pad(3)))


class ChatScreen(ctk.CTkFrame):
    """Chat Screen - Responsive"""
    
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        
        self.app = app_controller
        self.is_waiting_response = False
        self._last_w = 0
        self._last_h = 0
        
        self._create_layout()
        self._show_greeting()
        
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
        r = responsive
        self.title_label.configure(font=r.font(base_size=18, weight="bold"))
        self.clear_btn.configure(font=r.font(base_size=10), height=r.size(28), width=r.size(100))
        self.send_btn.configure(font=r.font_ar(base_size=16), width=r.size(50), height=r.size(38))
        self.message_entry.configure(font=r.font(base_size=12), height=r.size(38))
        self.med_btn.configure(font=r.font_ar(base_size=14), width=r.size(35), height=r.size(35))
    
    def _create_layout(self):
        r = responsive
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title ~6%
        self.grid_rowconfigure(1, weight=1)  # Chat area ~82%
        self.grid_rowconfigure(2, weight=0)  # Input ~12%
        
        # Title bar
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="ew", padx=r.pad(15), pady=(r.pad(8), r.pad(4)))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="💬 AI Chat",
            font=r.font(base_size=18, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.title_label.pack(side="left")
        
        self.clear_btn = ctk.CTkButton(
            self.title_frame,
            text="🗑️ Clear Chat",
            font=r.font(base_size=10),
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["danger"],
            width=r.size(100),
            height=r.size(28),
            command=self._clear_chat
        )
        self.clear_btn.pack(side="right")
        
        self._create_chat_area()
        self._create_input_area()
    
    def _create_chat_area(self):
        r = responsive
        self.chat_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=r.pad(15), pady=r.pad(4))
        
        self.messages_frame = ctk.CTkScrollableFrame(
            self.chat_frame,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.messages_frame.pack(fill="both", expand=True, padx=r.pad(6), pady=r.pad(6))
    
    def _create_input_area(self):
        r = responsive
        self.input_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"],
        )
        self.input_frame.grid(row=2, column=0, sticky="ew", padx=r.pad(15), pady=(0, r.pad(10)))
        
        self.input_container = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.input_container.pack(fill="both", expand=True, padx=r.pad(10), pady=r.pad(8))
        
        self.send_btn = ctk.CTkButton(
            self.input_container,
            text="📤",
            font=r.font_ar(base_size=16),
            width=r.size(50),
            height=r.size(38),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            corner_radius=RADIUS["md"],
            command=self._send_message
        )
        self.send_btn.pack(side="right", padx=(r.pad(4), 0))
        
        self.med_btn = ctk.CTkButton(
            self.input_container,
            text="💊",
            font=r.font_ar(base_size=14),
            width=r.size(35),
            height=r.size(35),
            fg_color=COLORS["bg_tertiary"],
            hover_color=COLORS["warning"],
            corner_radius=RADIUS["md"],
            command=self._request_medication_reminder
        )
        self.med_btn.pack(side="right", padx=r.pad(2))
        
        self.message_entry = ctk.CTkEntry(
            self.input_container,
            placeholder_text="Type your message here...",
            font=r.font(base_size=12),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            height=r.size(38)
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, r.pad(6)))
        self.message_entry.bind("<Return>", lambda e: self._send_message())
    
    def _show_greeting(self):
        greeting = chatbot.get_greeting()
        self._add_message(greeting, is_user=False)
    
    def _add_message(self, text: str, is_user: bool = True):
        r = responsive
        container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        container.pack(fill="x", pady=r.pad(3))
        
        bubble = ChatBubble(
            container,
            message=text,
            is_user=is_user,
            timestamp=datetime.now()
        )
        
        if is_user:
            bubble.pack(anchor="e", padx=(r.pad(40), 0))
        else:
            bubble.pack(anchor="w", padx=(0, r.pad(40)))
        
        self.messages_frame._parent_canvas.yview_moveto(1.0)
    
    def _add_typing_indicator(self):
        r = responsive
        self.typing_container = ctk.CTkFrame(self.messages_frame, fg_color="transparent")
        self.typing_container.pack(fill="x", pady=r.pad(3))
        
        self.typing_bubble = ctk.CTkFrame(
            self.typing_container,
            fg_color=COLORS["bg_tertiary"],
            corner_radius=RADIUS["lg"]
        )
        self.typing_bubble.pack(anchor="w", padx=(0, r.pad(40)))
        
        self.typing_label = ctk.CTkLabel(
            self.typing_bubble,
            text="🤖 Typing...",
            font=r.font(base_size=12),
            text_color=COLORS["text_muted"]
        )
        self.typing_label.pack(padx=r.pad(10), pady=r.pad(6))
    
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
        self.send_btn.configure(state="disabled")
        self._add_typing_indicator()
        self.is_waiting_response = True
        
        def get_response():
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in message)
            english_message = chatbot.translate_to_english(message) if has_arabic else message
            
            # Display user message in English
            self.after(0, lambda: self._add_message(english_message, is_user=True))
            
            response = chatbot.send_message(english_message)
            self.after(0, lambda: self._handle_response(response))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def _handle_response(self, response: str):
        self._remove_typing_indicator()
        self.is_waiting_response = False
        self.send_btn.configure(state="normal")
        
        self._add_message(response, is_user=False)
        
        # Translate response to Arabic and speak it
        def speak_async():
            arabic_response = chatbot.translate_to_arabic(response)
            from modules.voice_assistant import voice_assistant
            voice_assistant.speak(arabic_response, wait=False)
            
        threading.Thread(target=speak_async, daemon=True).start()
    
    def _request_medication_reminder(self):
        reminder = chatbot.get_medication_reminder()
        self._add_message(reminder, is_user=False)
        
        def speak_async():
            arabic_reminder = chatbot.translate_to_arabic(reminder)
            from modules.voice_assistant import voice_assistant
            voice_assistant.speak(arabic_reminder, wait=False)
            
        threading.Thread(target=speak_async, daemon=True).start()
    
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
        """Process voice input from microphone"""
        if self.is_waiting_response:
            return
        
        if not text or not text.strip():
            return
        
        # Translate Arabic voice input to English text
        def process_async():
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
            english_text = chatbot.translate_to_english(text) if has_arabic else text
            self.after(0, lambda: self._update_entry_and_send(english_text, auto_send, speak_response))
            
        threading.Thread(target=process_async, daemon=True).start()

    def _update_entry_and_send(self, english_text: str, auto_send: bool, speak_response: bool):
        self.message_entry.delete(0, 'end')
        self.message_entry.insert(0, english_text)
        self.message_entry.update()
        
        if auto_send:
            self.after(300, lambda: self._send_voice_message(english_text, speak_response))
    
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
            def speak_async():
                arabic_response = chatbot.translate_to_arabic(response)
                from modules.voice_assistant import voice_assistant
                voice_assistant.speak(arabic_response, wait=False)
            threading.Thread(target=speak_async, daemon=True).start()
