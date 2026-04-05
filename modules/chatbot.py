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
        conditions_str = "، ".join(self.patient_info.conditions)
        medications_str = "\n".join([f"• {med}" for med in self.patient_info.medications])
        return f"""
أنت مساعد طبي ذكي باسم "الدكتورة مريم"، تتحدث بلغة بيضاء راقية (مزيج بين الفصحى المبسطة والعامية المهذبة).
اسم المريض للحالة الحالية هو {self.patient_info.name} وعمره {self.patient_info.age} عاماً.

الحالات الصحية للمريض: {conditions_str}

الأدوية الحالية للمريض:
{medications_str}

أسلوبك في الكلام:
1. تحدث بأسلوب شبه رسمي (Semi-Formal)، محترم، وودود في نفس الوقت.
2. كن دقيقاً جداً وأجب على أسئلة المريض الطبية أو العامة بتفاصيل وافية وشرح مبسط علمي وواضح.
3. أظهر تعاطفاً مع المريض ولكن بمهنية طبية عالية وموثوقة.
4. استخدم عبارات مثل "بالطبع"، "يسعدني توضيح ذلك"، "شفاك الله وعافاك".
5. احتفظ بردودك منظمة، مع إعطاء معلومات قيمة ودقيقة ومفصلة.
6. إذا سأل المريض عن الأدوية أو الجرعات، اشرح له التفاصيل بطريقة احترافية ومطمئنة.
"""
    
    def send_message(self, user_message: str) -> str:
        if not self.client:
            return "عذراً، الشات بوت غير متاح حالياً. يرجى المحاولة لاحقاً."
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
                    return "⚠️ عذراً، يرجى الانتظار قليلاً ثم المحاولة مرة أخرى."
                return "عذراً، حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى."
    
    def send_message_async(self, user_message: str, callback):
        threading.Thread(target=lambda: callback(self.send_message(user_message)), daemon=True).start()
    
    def get_greeting(self) -> str:
        hour = datetime.now().hour
        if 5 <= hour < 12: time_greeting = "صباح الخير"
        elif 12 <= hour < 17: time_greeting = "مساء الخير"
        else: time_greeting = "مساء الخير"
        return f"""
{time_greeting}! 👋

أنا مساعدك الطبي الذكي. كيف يمكنني مساعدتك اليوم؟

يمكنني:
• 💊 تذكيرك بمواعيد الأدوية
• 🥗 تقديم نصائح غذائية
• 💬 الإجابة على استفساراتك الصحية

ما الذي تريد أن نتحدث عنه؟
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
        reminder_parts = ["💊 تذكير بالأدوية:\n"]
        if 6 <= hour < 10: reminder_parts.append("• Concor 5mg - قرص واحد الآن (صباحاً)")
        if 12 <= hour < 15: reminder_parts.append("• Aspirin Protect 100mg - قرص واحد بعد الغداء")
        if 18 <= hour < 21:
            reminder_parts.append("• Zestril 10mg - قرص واحد الآن (مساءً)")
            reminder_parts.append("• Glucophage XR 1000mg - قرص واحد بعد العشاء")
        if 21 <= hour or hour < 1:
            reminder_parts.append("• Ator 20mg - قرص واحد قبل النوم")
            reminder_parts.append("• Lantus SoloStar - 20 وحدة قبل النوم")
        if len(reminder_parts) == 1:
            return "✅ لا توجد أدوية مستحقة في هذا الوقت. استمر في الالتزام بمواعيد أدويتك!"
        return "\n".join(reminder_parts)
    
    def test(self):
        if not self.client: return False
        return True


chatbot = Chatbot()

if __name__ == "__main__":
    chatbot.test()
