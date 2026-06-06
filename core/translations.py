"""
AI Robot Operating System - Translations Module
نظام تشغيل الروبوت الطبي الذكي - وحدة الترجمات

Egyptian Arabic to English translations for offline TTS fallback.
ترجمة العامية المصرية للإنجليزية عند عدم توفر صوت عربي.
"""

TRANSLATIONS = {
    "مرحباً بكم. أنا المساعد الطبي الذكي، مصمم لتقديم خدمات الرعاية والمتابعة الصحية.":
        "Welcome. I am the intelligent medical assistant, designed to provide health care and monitoring services.",
    
    "هل تأذن لي بتفعيل المساعد الصوتي للتفاعل معكم؟":
        "Would you allow me to enable the voice assistant to interact with you?",
    
    "المساعد الذكي قيد الاستماع الآن. تفضل بطرح سؤالك.":
        "The intelligent assistant is now listening. Please proceed with your question.",
    
    "شكراً لكم. المساعد الصوتي نشط الآن وجاهز للاستخدام.":
        "Thank you. The voice assistant is now active and ready for use.",
    
    "تم التعطيل. يمكنك تفعيل المساعد الصوتي في أي وقت عبر الإعدادات.":
        "Disabled. You can enable the voice assistant at any time via settings.",
    
    "كيف حالك اليوم؟": "How are you today?",
    "شكراً لك": "Thank you",
    "حسناً": "Okay",
    "تم": "Done",
    "جاري التحميل": "Loading",
    "خطأ": "Error",
    "تحذير": "Warning",
    "نجاح": "Success",
    "لحظة واحدة": "Just a moment",
    "جاري المعالجة": "Processing",
    "جاري تحليل الصورة": "Analyzing the image",
    "تم التحليل بنجاح": "Analysis completed successfully",
    "لم أتمكن من تحليل الصورة": "I couldn't analyze the image",
    "حان وقت الدواء": "It's time for your medicine",
    "لا تنسى دواءك": "Don't forget your medicine",
    "حدث خطأ، حاول مرة أخرى": "An error occurred, try again",
    "لا يوجد اتصال": "No connection",   
    "جاري فتح صفحة القياسات الحيوية للفحص.": "Opening the vital measurements page for checkup.",
    "يرجى تزويدي بقيمة مستوى السكر لتسجيلها.": "Please provide me with the blood sugar level to record it.",
    "تم تسجيل مستوى السكر بنجاح بقيمة": "Blood sugar reading has been recorded successfully with value",
    "جاري إنشاء رمز الاستجابة السريعة للبيانات الحيوية.": "Generating the QR code for vital signs data.",
    "جاري فتح الرابط في متصفح الويب.": "Opening the link in the web browser.",
    "جاري فتح كاميرا تحليل المكونات الغذائية.": "Opening the nutritional analysis camera.",
    "المساعد الذكي جاهز للاستماع، تفضل بطرح سؤالك.": "The intelligent assistant is ready to listen, please go ahead.",
    "تم إيقاف العملية الحالية.": "The current operation has been stopped.",
    "جاري العودة إلى الشاشة الرئيسية.": "Returning to the main screen.",
    "إلى اللقاء، أتمنى لكم السلامة.": "Goodbye, I wish you health and safety.",
    "تم إغلاق المحادثة. يمكنك استدعائي في أي وقت.": "The conversation is closed. You can call me at any time.",
    "المساعد الذكي قيد الاستماع.": "The intelligent assistant is listening.",
}


def translate(text: str) -> str:
    """
    Translate Arabic text to English if available.
    Returns original text if no translation found.
    """
    return TRANSLATIONS.get(text, text)


def get_all_translations() -> dict:
    """Get all translations dictionary."""
    return TRANSLATIONS.copy()
