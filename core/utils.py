"""
AI Robot Operating System - Utility Functions
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.append('..')
from config import config


def get_arabic_date() -> str:
    """Get current date in English format."""
    now = datetime.now()
    return now.strftime("%A, %d %B %Y")


def get_arabic_time() -> str:
    """Get current time in 12-hour format."""
    now = datetime.now()
    return now.strftime("%I:%M %p")


def get_time_of_day() -> str:
    """Get time of day greeting in English."""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"


def format_blood_pressure(systolic: int, diastolic: int) -> dict:
    """Format blood pressure with status."""
    if systolic < 90 or diastolic < 60:
        status = "Low"
        color = config.COLORS['info']
        icon = "⬇️"
    elif systolic < 120 and diastolic < 80:
        status = "Normal"
        color = config.COLORS['success']
        icon = "✅"
    elif systolic < 130 and diastolic < 85:
        status = "Slightly High"
        color = config.COLORS['warning']
        icon = "⚠️"
    elif systolic < 140 or diastolic < 90:
        status = "High"
        color = config.COLORS['warning']
        icon = "⚠️"
    else:
        status = "Very High"
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
    """Format heart rate with status."""
    if bpm < 60:
        status = "Slow"
        color = config.COLORS['info']
        icon = "⬇️"
    elif bpm <= 100:
        status = "Normal"
        color = config.COLORS['success']
        icon = "✅"
    elif bpm <= 120:
        status = "Slightly High"
        color = config.COLORS['warning']
        icon = "⚠️"
    else:
        status = "Very Fast"
        color = config.COLORS['danger']
        icon = "🔴"
    
    return {
        "value": str(bpm),
        "unit": "bpm",
        "status": status,
        "color": color,
        "icon": icon
    }


def format_temperature(temp: float) -> dict:
    """Format temperature with status."""
    if temp < 35.5:
        status = "Low"
        color = config.COLORS['info']
        icon = "❄️"
    elif temp <= 37.5:
        status = "Normal"
        color = config.COLORS['success']
        icon = "✅"
    elif temp <= 38.5:
        status = "Mild Fever"
        color = config.COLORS['warning']
        icon = "🌡️"
    else:
        status = "High Fever"
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
    """Calculate insulin dose based on blood sugar level."""
    if blood_sugar <= target_sugar:
        correction_dose = 0
        recommendation = "Blood sugar is normal, base dose is sufficient"
    else:
        difference = blood_sugar - target_sugar
        correction_dose = round(difference / correction_factor)
        recommendation = f"Add {correction_dose} units to the base dose"
    
    total_dose = base_dose + correction_dose
    
    return {
        "base_dose": base_dose,
        "correction_dose": correction_dose,
        "total_dose": total_dose,
        "blood_sugar": blood_sugar,
        "recommendation": recommendation,
        "unit": "units"
    }


def ensure_directory(path: Path) -> bool:
    """Ensure a directory exists, create if it doesn't."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def log_message(message: str, level: str = "INFO"):
    """Log a message with timestamp (silent)."""
    pass


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color."""
    return f"#{r:02x}{g:02x}{b:02x}"


def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """Darken a hex color."""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))
    return rgb_to_hex(r, g, b)


def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """Lighten a hex color."""
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)
