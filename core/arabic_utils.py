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

import textwrap

def fix_arabic(text: str, wrap_length: int = None) -> str:
    """Fix Arabic text for display in Tkinter/CustomTkinter. Supports manual wrapping."""
    if not text or not ARABIC_SUPPORT:
        return text
    
    if not any('\u0600' <= char <= '\u06FF' for char in text):
        if wrap_length:
            return '\n'.join(textwrap.wrap(text, width=wrap_length))
        return text
    
    try:
        if wrap_length:
            # Wrap text BEFORE bidi processing to preserve logical sentence flow
            lines = []
            for paragraph in str(text).split('\n'):
                if not paragraph.strip():
                    lines.append('')
                else:
                    lines.extend(textwrap.wrap(paragraph, width=wrap_length))
        else:
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
