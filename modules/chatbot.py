"""
AI Robot Operating System - Chatbot Module
AI chatbot using Groq API for conversation with the patient in Arabic.
"""

import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import threading

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

sys.path.append('..')
from config import config


@dataclass
class Message:
    content: str
    is_user: bool
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PatientInfo:
    name: str = "المريض"
    conditions: list = field(default_factory=lambda: ["السكري", "ارتفاع ضغط الدم", "أمراض القلب"])
    medications: list = field(default_factory=lambda: [
        "Glucophage XR 1000mg - قرص واحد بعد العشاء",
        "Concor 5mg - قرص واحد صباحاً",
        "Zestril 10mg - قرص واحد مساءً",
        "Ator 20mg - قرص واحد قبل النوم",
        "Aspirin Protect 100mg - قرص واحد بعد الغداء",
        "Lantus SoloStar - 20 وحدة قبل النوم"
    ])
    age: int = 55


class Chatbot:
    def __init__(self, patient_info: Optional[PatientInfo] = None):
        self.api_key = config.GROQ_API_KEY
        self.model_name = config.GROQ_MODEL
        self.client = None
        self.conversation_history = []
        self.history: list[Message] = []
        self.patient_info = patient_info or PatientInfo()
        self._lock = threading.Lock()
        self._initialize()
    
    def _initialize(self):
        if not GROQ_AVAILABLE or not self.api_key:
            return
        try:
            self.client = Groq(api_key=self.api_key)
            self.conversation_history = [
                {"role": "system", "content": self._get_system_prompt()}
            ]
        except Exception:
            pass
    
    def _get_system_prompt(self) -> str:
        conditions_str = ", ".join(self.patient_info.conditions)
        medications_str = "\n".join([f"• {med}" for med in self.patient_info.medications])
        return f"""
You are an intelligent AI Medical Robot Assistant, speaking in a highly professional, polite, and formal academic manner suitable for a graduation project presentation.
The patient's name is {self.patient_info.name} and they are {self.patient_info.age} years old.

Patient's health conditions: {conditions_str}

Patient's current medications:
{medications_str}

Style instructions:
1. Speak in a highly professional, polite, respectful, and formal academic tone. Do not use personal names like "Dr. Maryam" or refer to yourself as a human doctor.
2. Be highly accurate and answer patient questions with detailed, clear, and scientifically sound medical explanations.
3. Maintain professional standards and professional empathy.
4. Keep your responses organized with lists or bullet points if needed.
5. Provide valuable, detailed, and accurate health information.
6. CRITICAL: You MUST write your response entirely in English. Do NOT output any Arabic text.
"""
    
    def translate_to_english(self, text: str) -> str:
        """Translate Arabic text to English using Groq."""
        if not self.client:
            return text
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Translate the following Arabic text to English. Output only the English translation. Do not write explanations or anything else."},
                    {"role": "user", "content": text}
                ],
                max_tokens=250,
                temperature=0.1
            )
            res = response.choices[0].message.content.strip().strip('"').strip()
            return res
        except Exception:
            return text

    def translate_to_arabic(self, text: str) -> str:
        """Translate English response to formal Arabic for speech."""
        if not self.client:
            return text
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Translate the following English medical explanation to highly formal, professional Arabic (Standard Arabic / Fusha) suitable for a professional academic presentation. Avoid any colloquial phrases, personal names, or calling the assistant a doctor. Output only the Arabic translation. Do not write English explanations or anything else."},
                    {"role": "user", "content": text}
                ],
                max_tokens=400,
                temperature=0.3
            )
            res = response.choices[0].message.content.strip().strip('"').strip()
            return res
        except Exception:
            return text

    def send_message(self, user_message: str) -> str:
        if not self.client:
            return "Sorry, the chatbot is currently unavailable. Please try again later."
        with self._lock:
            try:
                self.history.append(Message(content=user_message, is_user=True))
                self.conversation_history.append({"role": "user", "content": user_message})
                response = self.client.chat.completions.create(
                    model=self.model_name, messages=self.conversation_history, max_tokens=500, temperature=0.7)
                ai_response = response.choices[0].message.content
                self.conversation_history.append({"role": "assistant", "content": ai_response})
                self.history.append(Message(content=ai_response, is_user=False))
                return ai_response
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate" in error_msg.lower():
                    return "⚠️ Sorry, please wait a moment and try again."
                return "Sorry, a connection error occurred. Please try again."
    
    def send_message_async(self, user_message: str, callback):
        threading.Thread(target=lambda: callback(self.send_message(user_message)), daemon=True).start()
    
    def get_greeting(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12: time_greeting = "Good morning"
        elif 12 <= hour < 17: time_greeting = "Good afternoon"
        else: time_greeting = "Good evening"
        return f"""
{time_greeting}! 👋

I am your AI Medical Robot Assistant. How may I assist you today?

My capabilities include:
• 💊 Managing and reminding you of medication schedules
• 🥗 Providing detailed nutritional analysis and advice
• 💬 Answering health and medical inquiries with scientific accuracy

Please let me know how I can be of assistance.
"""
    
    def get_history(self) -> list[Message]: return self.history.copy()
    
    def clear_history(self):
        self.history.clear()
        if hasattr(self, 'model') and self.model:
            self.chat = self.model.start_chat(history=[])
    
    def update_patient_info(self, patient_info: PatientInfo):
        self.patient_info = patient_info
        self._initialize()
    
    def get_medication_reminder(self) -> str:
        hour = datetime.now().hour
        reminder_parts = ["💊 Medication Reminder:\n"]
        if 6 <= hour < 10: reminder_parts.append("• Concor 5mg - one tablet now (morning)")
        if 12 <= hour < 15: reminder_parts.append("• Aspirin Protect 100mg - one tablet after lunch")
        if 18 <= hour < 21:
            reminder_parts.append("• Zestril 10mg - one tablet now (evening)")
            reminder_parts.append("• Glucophage XR 1000mg - one tablet after dinner")
        if 21 <= hour or hour < 1:
            reminder_parts.append("• Ator 20mg - one tablet before bedtime")
            reminder_parts.append("• Lantus SoloStar - 20 units before bedtime")
        if len(reminder_parts) == 1:
            return "✅ No medications are due at this time. Keep up the good work with your schedule!"
        return "\n".join(reminder_parts)
    
    def test(self):
        if not self.client: return False
        return True


chatbot = Chatbot()

if __name__ == "__main__":
    chatbot.test()
