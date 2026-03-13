"""
AI Robot Operating System - Arabic Text Utilities
نظام تشغيل الروبوت الطبي الذكي - أدوات معالجة النصوص العربية

Utility to handle Arabic text shaping and BiDi reordering for non-RTL displays.
أداة لمعالجة تشكيل النصوص العربية وترتيبها (RTL) للشاشات التي لا تدعمها تلقائياً.
"""

import sys
import os

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False

def fix_arabic(text: str) -> str:
    """
    Fix Arabic text for display in Tkinter/CustomTkinter.
    يصلح النصوص العربية للعرض في Tkinter.
    """
    if not text or not ARABIC_SUPPORT:
        return text
    
    # Only process strings containing Arabic characters for better performance
    if not any('\u0600' <= char <= '\u06FF' for char in text):
        return text
    
    try:
        # 1. Reshape Arabic letters to connect properly (ligatures)
        reshaped_text = arabic_reshaper.reshape(text)
        
        # 2. Reorder for RTL display
        bidi_text = get_display(reshaped_text)
        
        return bidi_text
    except Exception as e:
        print(f"⚠️ Error fixing Arabic text: {e}")
        return text

# Backward compatibility or shorthand
fix = fix_arabic
