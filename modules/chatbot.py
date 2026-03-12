"""
AI Robot Operating System - Chatbot Module
نظام تشغيل الروبوت الطبي الذكي - وحدة الشات بوت

This module provides an AI chatbot using Groq API
for natural conversation with the patient in Arabic.

هذه الوحدة توفر شات بوت ذكي باستخدام Groq API
للمحادثة الطبيعية مع المريض باللغة العربية.
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
    print("⚠️ Groq not installed. pip install groq")

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
    """
    AI Chatbot using Groq
    شات بوت ذكي باستخدام Groق
    """
    
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
        if not GROQ_AVAILABLE:
            print("❌ Groq library not available")
            return
        
        if not self.api_key:
            print("❌ Groq API key not set")
            return
        
        try:
            self.client = Groq(api_key=self.api_key)
            self.conversation_history = [
                {"role": "system", "content": self._get_system_prompt()}
            ]
            print(f"✅ Chatbot initialized with model: {self.model_name}")
        except Exception as e:
            print(f"❌ Failed to initialize Groq: {e}")
    
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
1. تحدث بأسلوب شبه رسمي (Semi-Formal)، محترم، وودود في نفس الوقت. تجنب العامية المفرطة أو الألفاظ الشعبية المبتذلة.
2. كن دقيقاً جداً وأجب على أسئلة المريض الطبية أو العامة بتفاصيل وافية وشرح مبسط علمي وواضح.
3. تجنب الجفاف الآلي، أظهر تعاطفاً مع المريض ولكن بمهنية طبية عالية وموثوقة.
4. استخدم عبارات مثل "بالطبع"، "يسعدني توضيح ذلك"، "شفاك الله وعافاك"، بدلاً من "يا صاحبي" و"يا غالي".
5. احتفظ بردودك منظمة، مع إعطاء معلومات قيمة ودقيقة ومفصلة في نفس الوقت تناسب الاستماع الصوتي.
6. إذا سأل المريض عن الأدوية أو الجرعات، اشرح له التفاصيل بطريقة احترافية ومطمئنة وذكره بأهمية الالتزام بمواعيدها.

أمثلة لردودك:
- "أهلاً بك، كيف تشعر اليوم؟ أتمنى أن تكون بصحة جيدة."
- "بالطبع، يمكنني أن أشرح لك ذلك بالتفصيل. هذه الحالة تتطلب الانتباه لعدة جوانب أهمها..."
- "لا داعي للقلق، من المهم الالتزام بالجرعات المحددة في وقتها للحفاظ على استقرار مؤشراتك الحيوية."

تذكر: أنت واجهة طبية محترفة، هادئة، دقيقة، وتهتم بصحة المريض بشدة والتحدث معه بلباقة واحترام تام وتفصيل علمي مستفيض.
"""
    
    def send_message(self, user_message: str) -> str:
        if not self.client:
            return "عذراً، الشات بوت غير متاح حالياً. يرجى المحاولة لاحقاً."
        
        with self._lock:
            try:
                self.history.append(Message(content=user_message, is_user=True))
                
                self.conversation_history.append({
                    "role": "user",
                    "content": user_message
                })
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.conversation_history,
                    max_tokens=500,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                self.history.append(Message(content=ai_response, is_user=False))
                
                return ai_response
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate" in error_msg.lower():
                    return "⚠️ عذراً، يرجى الانتظار قليلاً ثم المحاولة مرة أخرى."
                
                print(f"❌ Chatbot error: {e}")
                return "عذراً، حدث خطأ في الاتصال. يرجى المحاولة مرة أخرى."
    
    def send_message_async(self, user_message: str, callback):
        def _send():
            response = self.send_message(user_message)
            callback(response)
        
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
    
    def get_greeting(self) -> str:
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            time_greeting = "صباح الخير"
        elif 12 <= hour < 17:
            time_greeting = "مساء الخير"
        else:
            time_greeting = "مساء الخير"
        
        return f"""
{time_greeting}! 👋

أنا مساعدك الطبي الذكي. كيف يمكنني مساعدتك اليوم؟

يمكنني:
• 💊 تذكيرك بمواعيد الأدوية
• 🥗 تقديم نصائح غذائية
• 💬 الإجابة على استفساراتك الصحية

ما الذي تريد أن نتحدث عنه؟
"""
    
    def get_history(self) -> list[Message]:
        return self.history.copy()
    
    def clear_history(self):
        self.history.clear()
        if hasattr(self, 'model') and self.model:
            self.chat = self.model.start_chat(history=[])
        print("🗑️ Chat history cleared")
    
    def update_patient_info(self, patient_info: PatientInfo):
        self.patient_info = patient_info
        self._initialize()
    
    def get_medication_reminder(self) -> str:
        hour = datetime.now().hour
        
        reminder_parts = ["💊 تذكير بالأدوية:\n"]
        
        if 6 <= hour < 10:
            reminder_parts.append("• Concor 5mg - قرص واحد الآن (صباحاً)")
        
        if 12 <= hour < 15:
            reminder_parts.append("• Aspirin Protect 100mg - قرص واحد بعد الغداء")
        
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
        print("🧪 Testing Chatbot...")
        
        if not self.client:
            print("❌ Client not initialized")
            return False
        
        print(f"✅ Client initialized: {self.model_name}")
        print(f"📝 Patient: {self.patient_info.name}")
        print(f"🏥 Conditions: {', '.join(self.patient_info.conditions)}")
        
        greeting = self.get_greeting()
        print(f"\n{greeting}")
        
        print("\n🧪 Testing message...")
        response = self.send_message("مرحباً، كيف حالك؟")
        print(f"🤖 Response: {response}")
        
        print("\n✅ Chatbot test completed")
        return True


chatbot = Chatbot()


if __name__ == "__main__":
    chatbot.test()
