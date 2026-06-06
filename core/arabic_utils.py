"""
AI Robot Operating System - Arabic Text Utilities
Utility to handle Arabic text shaping and BiDi reordering for non-RTL displays.
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
    """Fix Arabic text for display in Tkinter/CustomTkinter."""
    if not text or not ARABIC_SUPPORT:
        return text
    
    if not any('\u0600' <= char <= '\u06FF' for char in text):
        return text
    
    try:
        lines = str(text).split('\n')
        fixed_lines = []
        for line in lines:
            if not line.strip():
                fixed_lines.append(line)
                continue
            reshaped_text = arabic_reshaper.reshape(line)
            bidi_text = get_display(reshaped_text)
            fixed_lines.append(bidi_text)
        return '\n'.join(fixed_lines)
    except Exception:
        return text

fix = fix_arabic
