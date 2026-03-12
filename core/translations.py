"""
AI Robot Operating System - Translations Module
نظام تشغيل الروبوت الطبي الذكي - وحدة الترجمات

Egyptian Arabic to English translations for offline TTS fallback.
ترجمة العامية المصرية للإنجليزية عند عدم توفر صوت عربي.
"""

TRANSLATIONS = {
    "أهلاً بيك يا غالي! أنا مساعدك الطبي. أنا موجود هنا عشانك وعشان صحتك.":
        "Hey there! I'm your medical assistant. I'm here for you and your health.",
    
    "تسمحلي أسمعك وأتكلم معاك؟":
        "Can I listen to you and talk with you?",
    
    "أنا أستمع إليك، تحدث معي":
        "I'm listening, talk to me.",
    
    "شكراً لك! أنا مستعد لمساعدتك.":
        "Thank you! I'm ready to help you.",
    
    "حسناً، يمكنك تفعيل الصوت في أي وقت من الإعدادات.":
        "Okay, you can enable voice anytime from settings.",
    
    "هل تسمح لي بالاستماع إليك والتحدث معك؟":
        "Do you allow me to listen and talk to you?",
    
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
    "تمام، هنعمل القياسات دلوقتي": "Okay, let's take the measurements now",
    "قولي قيمة السكر": "Tell me the sugar value please",
    "تمام، سجلت قياس السكر": "Okay, I recorded the sugar reading",
    "تمام، بولد الكود": "Okay, generating the code",
    "بفتحلك الرابط": "Opening the link for you",
    "يلا بينا نحلل الأكل": "Let's analyze the food",
    "أنا سامعك يا غالي، اتفضل": "I'm listening, go ahead",
    "تمام، وقفت": "Okay, stopped",
    "راجعين للبداية": "Going back to home",
    "نشوفك على خير": "See you later, take care",
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
