import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(ENV_PATH)


class Config:
    
    GROQ_API_KEY: str = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL: str = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    GEMINI_VISION_MODEL: str = os.getenv('GEMINI_VISION_MODEL', 'gemini-2.0-flash')
    
    CLOUDFLARE_ACCOUNT_ID: str = os.getenv('CLOUDFLARE_ACCOUNT_ID', '')
    CLOUDFLARE_API_TOKEN: str = os.getenv('CLOUDFLARE_API_TOKEN', '')
    
    import platform
    
    DEFAULT_PORT = 'COM3'
    if platform.system() == 'Linux':
        DEFAULT_PORT = '/dev/ttyUSB0' 
        
    ARDUINO_PORT: str = os.getenv('ARDUINO_PORT', DEFAULT_PORT)
    ARDUINO_BAUD_RATE: int = int(os.getenv('ARDUINO_BAUD_RATE', '9600'))
    
    APP_LANGUAGE: str = os.getenv('APP_LANGUAGE', 'en')
    APP_FULLSCREEN: bool = os.getenv('APP_FULLSCREEN', 'true').lower() == 'true'
    
    _default_width = '1200' if platform.system() == 'Windows' else '800'
    _default_height = '800' if platform.system() == 'Windows' else '480'
    SCREEN_WIDTH: int = int(os.getenv('SCREEN_WIDTH', _default_width))
    SCREEN_HEIGHT: int = int(os.getenv('SCREEN_HEIGHT', _default_height))
    
    DEBUG_MODE: bool = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    ELEVENLABS_API_KEY: str = os.getenv('ELEVENLABS_API_KEY', '')
    VOICE_ENABLED: bool = os.getenv('VOICE_ENABLED', 'true').lower() == 'true'
    
    BASE_DIR: Path = BASE_DIR
    ASSETS_DIR: Path = BASE_DIR / 'assets'
    ICONS_DIR: Path = ASSETS_DIR / 'icons'
    SOUNDS_DIR: Path = ASSETS_DIR / 'sounds'
    DATA_DIR: Path = BASE_DIR / 'data'
    
    COLORS = {
        "primary": "#2563eb",
        "primary_hover": "#1d4ed8",
        "secondary": "#8b5cf6",
        "secondary_hover": "#7c3aed",
        "success": "#10b981",
        "success_hover": "#059669",
        "warning": "#f59e0b",
        "warning_hover": "#d97706",
        "danger": "#ef4444",
        "danger_hover": "#dc2626",
        "info": "#06b6d4",
        "info_hover": "#0891b2",
        "dark": "#1e293b",
        "darker": "#0f172a",
        "light": "#f8fafc",
        "gray": "#64748b",
        "bg_primary": "#0f172a",
        "bg_secondary": "#1e293b",
        "bg_card": "#1e293b",
        "text_primary": "#f8fafc",
        "text_secondary": "#94a3b8",
        "border": "#334155",
    }
    
    FONTS = {
        "family": "Cairo",
        "family_fallback": "Arial",
        "size_xs": 10,
        "size_sm": 12,
        "size_md": 14,
        "size_lg": 18,
        "size_xl": 24,
        "size_xxl": 32,
        "size_title": 48,
    }
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.GEMINI_API_KEY:
            return False
        return True
    
    @classmethod
    def print_config(cls):
        pass


config = Config()
