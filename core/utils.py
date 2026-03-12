"""
AI Robot Operating System - Utility Functions
نظام تشغيل الروبوت الطبي الذكي - الدوال المساعدة
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.append('..')
from config import config


def get_arabic_date() -> str:
    """
    Get current date in Arabic format
    الحصول على التاريخ الحالي بالتنسيق العربي
    """
    arabic_days = {
        'Monday': 'الإثنين',
        'Tuesday': 'الثلاثاء',
        'Wednesday': 'الأربعاء',
        'Thursday': 'الخميس',
        'Friday': 'الجمعة',
        'Saturday': 'السبت',
        'Sunday': 'الأحد'
    }
    
    arabic_months = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
        5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
        9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    
    now = datetime.now()
    day_name = arabic_days.get(now.strftime('%A'), now.strftime('%A'))
    month_name = arabic_months.get(now.month, str(now.month))
    
    return f"{day_name}، {now.day} {month_name} {now.year}"


def get_arabic_time() -> str:
    """
    Get current time in Arabic format (12-hour)
    الحصول على الوقت الحالي بالتنسيق العربي
    """
    now = datetime.now()
    hour = now.hour
    period = "صباحاً" if hour < 12 else "مساءً"
    
    if hour == 0:
        hour = 12
    elif hour > 12:
        hour -= 12
    
    return f"{hour}:{now.minute:02d} {period}"


def get_time_of_day() -> str:
    """
    Get time of day greeting
    الحصول على تحية حسب الوقت
    """
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "صباح الخير"
    elif 12 <= hour < 17:
        return "مساء الخير"
    elif 17 <= hour < 21:
        return "مساء الخير"
    else:
        return "مساء الخير"


def format_blood_pressure(systolic: int, diastolic: int) -> dict:
    """
    Format blood pressure with status
    تنسيق ضغط الدم مع الحالة
    """
    if systolic < 90 or diastolic < 60:
        status = "منخفض"
        color = config.COLORS['info']
        icon = "⬇️"
    elif systolic < 120 and diastolic < 80:
        status = "طبيعي"
        color = config.COLORS['success']
        icon = "✅"
    elif systolic < 130 and diastolic < 85:
        status = "مرتفع قليلاً"
        color = config.COLORS['warning']
        icon = "⚠️"
    elif systolic < 140 or diastolic < 90:
        status = "مرتفع"
        color = config.COLORS['warning']
        icon = "⚠️"
    else:
        status = "مرتفع جداً"
        color = config.COLORS['danger']
        icon = "🔴"
    
    return {
        "value": f"{systolic}/{diastolic}",
        "unit": "mmHg",
        "status": status,
        "color": color,
        "icon": icon
    }


def format_heart_rate(bpm: int) -> dict:
    """
    Format heart rate with status
    تنسيق نبضات القلب مع الحالة
    """
    if bpm < 60:
        status = "بطيء"
        color = config.COLORS['info']
        icon = "⬇️"
    elif bpm <= 100:
        status = "طبيعي"
        color = config.COLORS['success']
        icon = "✅"
    elif bpm <= 120:
        status = "مرتفع قليلاً"
        color = config.COLORS['warning']
        icon = "⚠️"
    else:
        status = "سريع جداً"
        color = config.COLORS['danger']
        icon = "🔴"
    
    return {
        "value": str(bpm),
        "unit": "نبضة/دقيقة",
        "status": status,
        "color": color,
        "icon": icon
    }


def format_temperature(temp: float) -> dict:
    """
    Format temperature with status
    تنسيق درجة الحرارة مع الحالة
    """
    if temp < 35.5:
        status = "منخفضة"
        color = config.COLORS['info']
        icon = "❄️"
    elif temp <= 37.5:
        status = "طبيعية"
        color = config.COLORS['success']
        icon = "✅"
    elif temp <= 38.5:
        status = "حمى خفيفة"
        color = config.COLORS['warning']
        icon = "🌡️"
    else:
        status = "حمى عالية"
        color = config.COLORS['danger']
        icon = "🔴"
    
    return {
        "value": f"{temp:.1f}",
        "unit": "°C",
        "status": status,
        "color": color,
        "icon": icon
    }


def calculate_insulin_dose(blood_sugar: int, target_sugar: int = 100, 
                           correction_factor: int = 50, 
                           base_dose: int = 20) -> dict:
    """
    Calculate insulin dose based on blood sugar level
    حساب جرعة الأنسولين بناءً على مستوى السكر
    
    Args:
        blood_sugar: Current blood sugar level (mg/dL)
        target_sugar: Target blood sugar level (default: 100 mg/dL)
        correction_factor: How much 1 unit of insulin lowers blood sugar
        base_dose: Base insulin dose (default: 20 units as per prescription)
    
    Returns:
        Dictionary with dose information
    """
    if blood_sugar <= target_sugar:
        correction_dose = 0
        recommendation = "مستوى السكر طبيعي، الجرعة الأساسية كافية"
    else:
        difference = blood_sugar - target_sugar
        correction_dose = round(difference / correction_factor)
        recommendation = f"يُنصح بإضافة {correction_dose} وحدة للجرعة الأساسية"
    
    total_dose = base_dose + correction_dose
    
    return {
        "base_dose": base_dose,
        "correction_dose": correction_dose,
        "total_dose": total_dose,
        "blood_sugar": blood_sugar,
        "recommendation": recommendation,
        "unit": "وحدة"
    }


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, create if it doesn't
    التأكد من وجود المجلد، وإنشاؤه إذا لم يكن موجوداً
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Failed to create directory {path}: {e}")
        return False


def log_message(message: str, level: str = "INFO"):
    """
    Log a message with timestamp
    تسجيل رسالة مع الوقت
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_icons = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "SUCCESS": "✅",
        "DEBUG": "🔍"
    }
    icon = level_icons.get(level, "📝")
    print(f"[{timestamp}] {icon} {level}: {message}")


def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert hex color to RGB tuple
    تحويل لون hex إلى RGB
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB to hex color
    تحويل RGB إلى لون hex
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """
    Darken a hex color
    تغميق لون hex
    """
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    return rgb_to_hex(r, g, b)


def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """
    Lighten a hex color
    تفتيح لون hex
    """
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)
