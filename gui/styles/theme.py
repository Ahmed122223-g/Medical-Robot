"""
AI Robot Operating System - Theme Configuration
"""

import customtkinter as ctk


COLORS = {
    "primary": "#4F46E5",
    "primary_hover": "#4338CA",
    "primary_light": "#EEF2FF",
    
    "secondary": "#7C3AED",
    "secondary_hover": "#6D28D9",
    "secondary_light": "#F5F3FF",
    
    "success": "#10B981",
    "success_hover": "#059669",
    "warning": "#F59E0B",
    "warning_hover": "#D97706",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "danger_light": "#FEE2E2",
    "info": "#06B6D4",
    
    "bg_primary": "#F8FAFC",
    "bg_secondary": "#F1F5F9",
    "bg_tertiary": "#E2E8F0",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F8FAFC",
    "bg_sidebar": "#FFFFFF",
    "bg_input": "#FFFFFF",
    
    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_muted": "#94A3B8",
    "text_white": "#FFFFFF",
    
    "border": "#E2E8F0",
    "border_light": "#F1F5F9",
    "border_focus": "#4F46E5",
    
    "glass": "rgba(255, 255, 255, 0.7)",
    "shadow_color": "rgba(0, 0, 0, 0.05)",
}

FONTS = {
    "family": "Cairo",
    "family_en": "Inter",
    "fallback": "system-ui",
    
    "size_xs": 10,
    "size_sm": 12,
    "size_md": 14,
    "size_lg": 16,
    "size_xl": 20,
    "size_2xl": 24,
    "size_3xl": 32,
    "size_4xl": 40,
    "size_title": 48,
    
    "weight_light": "normal",
    "weight_normal": "normal",
    "weight_medium": "bold",
    "weight_bold": "bold",
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "2xl": 48,
}

RADIUS = {
    "sm": 6,
    "md": 10,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
    "full": 9999,
}

SHADOWS = {
    "sm": "0 1px 2px rgba(0, 0, 0, 0.05)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "glow": "0 0 15px rgba(79, 70, 229, 0.2)",
}

ANIMATION = {
    "fast": 150,
    "normal": 300,
    "slow": 500,
}

ICON_SIZES = {
    "sm": 16,
    "md": 20,
    "lg": 24,
    "xl": 32,
    "2xl": 48,
}


class ResponsiveManager:
    """
    Calculates proportional sizes based on window dimensions.
    All sizes scale like SVG - no pixelation, proportional to screen.
    
    Reference resolution: 1200x800 (design baseline).
    """
    
    # Design baseline
    BASE_W = 1200
    BASE_H = 800
    
    def __init__(self):
        self._w = self.BASE_W
        self._h = self.BASE_H
        self._scale_x = 1.0
        self._scale_y = 1.0
        self._scale = 1.0  # min of x,y for uniform scaling
    
    def update(self, width: int, height: int):
        """Update dimensions and recalculate scale factors."""
        if width < 100 or height < 100:
            return
        self._w = width
        self._h = height
        self._scale_x = width / self.BASE_W
        self._scale_y = height / self.BASE_H
        
        raw_scale = min(self._scale_x, self._scale_y)
        
        import platform
        is_rpi = platform.system() == 'Linux' and ('arm' in platform.machine() or 'aarch' in platform.machine())
        
        if is_rpi:
            # Force a much larger minimum scale for small Raspberry Pi touchscreens
            self._scale = max(1.6, raw_scale)
        else:
            # Normal scale on Desktop, constrained so it doesn't get ridiculously huge or tiny
            self._scale = max(0.9, min(raw_scale, 1.4))
    
    @property
    def w(self) -> int:
        return self._w
    
    @property
    def h(self) -> int:
        return self._h
    
    @property
    def scale(self) -> float:
        return self._scale
    
    @property
    def scale_x(self) -> float:
        return self._scale_x
    
    @property
    def scale_y(self) -> float:
        return self._scale_y
    
    def font_size(self, base_size: int) -> int:
        """Scale a font size proportionally. Minimum 8."""
        return max(8, int(base_size * self._scale))
    
    def size(self, base_size: int) -> int:
        """Scale a pixel dimension proportionally. Minimum 1."""
        return max(1, int(base_size * self._scale))
    
    def size_x(self, base_size: int) -> int:
        """Scale horizontal dimension."""
        return max(1, int(base_size * self._scale_x))
    
    def size_y(self, base_size: int) -> int:
        """Scale vertical dimension."""
        return max(1, int(base_size * self._scale_y))
    
    def pad(self, base_pad: int) -> int:
        """Scale padding."""
        return max(1, int(base_pad * self._scale))
    
    def font(self, family: str = None, base_size: int = 14, weight: str = "normal") -> tuple:
        """Get a scaled font tuple."""
        fam = family or FONTS["family_en"]
        return (fam, self.font_size(base_size), weight)
    
    def font_ar(self, base_size: int = 14, weight: str = "normal") -> tuple:
        """Get a scaled Arabic font tuple."""
        return (FONTS["family"], self.font_size(base_size), weight)
    
    def height_pct(self, pct: float) -> int:
        """Get a height as percentage of window height."""
        return max(1, int(self._h * pct))
    
    def width_pct(self, pct: float) -> int:
        """Get a width as percentage of window width."""
        return max(1, int(self._w * pct))


# Global responsive manager instance
responsive = ResponsiveManager()


def configure_customtkinter():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    # Removed fixed widget/window scaling - we handle scaling dynamically now


def get_font(size: str = "md", weight: str = "normal") -> tuple:
    size_key = f"size_{size}"
    font_size = FONTS.get(size_key, FONTS["size_md"])
    
    weight_key = f"weight_{weight}"
    font_weight = FONTS.get(weight_key, FONTS["weight_normal"])
    
    return (FONTS["family"], font_size, font_weight)


def get_button_style(variant: str = "primary") -> dict:
    variants = {
        "primary": {
            "fg_color": COLORS["primary"],
            "hover_color": COLORS["primary_hover"],
            "text_color": COLORS["text_primary"],
        },
        "secondary": {
            "fg_color": COLORS["secondary"],
            "hover_color": COLORS["secondary_hover"],
            "text_color": COLORS["text_primary"],
        },
        "success": {
            "fg_color": COLORS["success"],
            "hover_color": COLORS["success_hover"],
            "text_color": COLORS["text_primary"],
        },
        "warning": {
            "fg_color": COLORS["warning"],
            "hover_color": COLORS["warning_hover"],
            "text_color": COLORS["text_primary"],
        },
        "danger": {
            "fg_color": COLORS["danger"],
            "hover_color": COLORS["danger_hover"],
            "text_color": COLORS["text_primary"],
        },
        "outline": {
            "fg_color": "transparent",
            "hover_color": COLORS["bg_tertiary"],
            "text_color": COLORS["text_primary"],
            "border_color": COLORS["border"],
            "border_width": 2,
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": COLORS["bg_tertiary"],
            "text_color": COLORS["text_secondary"],
        },
    }
    
    return variants.get(variant, variants["primary"])


def get_card_style() -> dict:
    return {
        "fg_color": COLORS["bg_card"],
        "corner_radius": RADIUS["lg"],
        "border_width": 1,
        "border_color": COLORS["border"],
    }


def get_input_style() -> dict:
    return {
        "fg_color": COLORS["bg_input"],
        "border_color": COLORS["border"],
        "border_width": 1,
        "corner_radius": RADIUS["md"],
        "text_color": COLORS["text_primary"],
        "placeholder_text_color": COLORS["text_muted"],
    }


STATUS_COLORS = {
    "normal": COLORS["success"],
    "warning": COLORS["warning"],
    "danger": COLORS["danger"],
    "info": COLORS["info"],
    "low": COLORS["info"],
    "high": COLORS["danger"],
    "medium": COLORS["warning"],
}


def get_status_color(status: str) -> str:
    status_lower = status.lower()
    
    if any(word in status_lower for word in ["طبيعي", "normal", "good", "جيد"]):
        return COLORS["success"]
    elif any(word in status_lower for word in ["مرتفع", "high", "خطر", "danger", "very high", "very fast", "fever"]):
        return COLORS["danger"]
    elif any(word in status_lower for word in ["منخفض", "low", "تحذير", "warning", "قليل", "slight", "slow", "mild"]):
        return COLORS["warning"]
    
    return STATUS_COLORS.get(status_lower, COLORS["text_primary"])
