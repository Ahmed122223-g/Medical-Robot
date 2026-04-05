import sys
import json
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

sys.path.append('..')
from config import config


class CommandState(Enum):
    IDLE = "idle"
    CHAT_MODE = "chat_mode"
    FOOD_SCREEN = "food_screen"


@dataclass
class CommandContext:
    state: CommandState = CommandState.IDLE
    data: dict = None
    def __post_init__(self):
        if self.data is None: self.data = {}
    def reset(self):
        self.state = CommandState.IDLE
        self.data = {}


class VoiceCommandProcessor:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model = None
        self.context = CommandContext()
        self.callbacks = {
            "open_food": None, "capture_food": None, "close_food": None,
            "open_chat": None, "close_current": None, "go_home": None,
            "general_chat": None, "speak": None, "exit_app": None,
            "open_qr": None, "set_sugar": None, "generate_qr": None, "open_browser": None,
        }
        self.current_screen = "home"
    
    def set_callback(self, command: str, callback: Callable):
        if command in self.callbacks: self.callbacks[command] = callback
    
    def set_current_screen(self, screen: str):
        self.current_screen = screen
        if screen == "food": self.context.state = CommandState.FOOD_SCREEN
        elif screen == "chat": self.context.state = CommandState.CHAT_MODE
        elif self.context.state in [CommandState.FOOD_SCREEN, CommandState.CHAT_MODE]:
            self.context.state = CommandState.IDLE
    
    def process_command(self, text: str) -> Optional[str]:
        if not text or not text.strip(): return None
        if self.context.state == CommandState.CHAT_MODE: return self._handle_chat(text)
        elif self.context.state == CommandState.FOOD_SCREEN: return self._handle_food_screen(text)
        else: return self._handle_new_command(text)
    
    def _handle_food_screen(self, text: str) -> str:
        text_lower = text.strip()
        if any(k in text_lower for k in ["حلل", "صور", "التقط", "تحليل", "خد صوره"]):
            if self.callbacks.get("capture_food"): self.callbacks["capture_food"]()
            return "جاري التقاط الصورة وتحليل الطعام"
        if any(k in text_lower for k in ["اقفل التصوير", "اغلق الكاميرا", "اقفل الكاميرا", "اغلاق", "أغلق", "توقف", "كفاية", "رجوع"]):
            if self.callbacks.get("close_current"): self.callbacks["close_current"]()
            self.context.state = CommandState.IDLE
            return "تم إغلاق الكاميرا"
        return None
    
    def _handle_new_command(self, text: str) -> str:
        return self._parse_keywords(text)
    
    def _parse_keywords(self, text: str) -> str:
        text_lower = text.strip()
        if any(k in text_lower for k in ["حلل الطعام", "صور", "كاميرا", "الأكل"]):
            return self._execute_command({"command": "open_food", "response": "يلا بينا نحلل الأكل"})
        if any(k in text_lower for k in ["تحدث معي", "كلمني", "أريد التحدث"]):
            return self._execute_command({"command": "open_chat", "response": "أنا سامعك يا غالي، اتفضل"})
        if any(k in text_lower for k in ["اغلاق", "أغلق", "توقف", "كفاية"]):
            return self._execute_command({"command": "close_current", "response": "تمام، وقفت"})
        if any(k in text_lower for k in ["ارجع للبداية", "ارجع ل البداية", "الصفحة الرئيسية", "الرئيسية", "البداية"]):
            return self._execute_command({"command": "go_home", "response": "راجعين للبداية"})
        if any(k in text_lower for k in ["اغلق البرنامج", "خروج"]):
            return self._execute_command({"command": "exit_app", "response": "نشوفك على خير"})
        if any(k in text_lower for k in ["القياسات", "بوابة المريض", "قياس", "الفحوصات", "اعمل قياس"]):
            return self._execute_command({"command": "open_qr", "response": "تمام، هنعمل القياسات دلوقتي"})
        if any(k in text_lower for k in ["السكر", "قياس السكر", "مستوى السكر"]):
            import re
            numbers = re.findall(r'\d+', text_lower)
            if numbers:
                return self._execute_command({"command": "set_sugar", "parameters": {"value": numbers[0]}, "response": f"تمام، سجلت قياس السكر {numbers[0]}"})
            else:
                return self._execute_command({"command": "speak", "parameters": {"text": "قولي قيمة السكر"}, "response": "قولي قيمة السكر"})
        if self.current_screen == "qr":
            import re
            numbers = re.findall(r'\d+', text_lower)
            if numbers:
                return self._execute_command({"command": "set_sugar", "parameters": {"value": numbers[0]}, "response": f"تمام، سجلت {numbers[0]}"})
        if any(k in text_lower for k in ["ولد الكود", "حدث الكود", "تحديث", "اعمل qr", "كيوار"]):
            return self._execute_command({"command": "generate_qr", "response": "تمام، بولد الكود"})
        if any(k in text_lower for k in ["افتح الرابط", "افتح اللينك", "افتح الموقع", "المتصفح"]):
            return self._execute_command({"command": "open_browser", "response": "بفتحلك الرابط"})
        return self._execute_command({"command": "general_chat", "parameters": {"text": text}, "response": None})
    
    def _execute_command(self, result: dict) -> str:
        command = result.get("command", "")
        params = result.get("parameters", {})
        response = result.get("response", "")
        
        if command == "open_food":
            if self.callbacks.get("open_food"): self.callbacks["open_food"]()
            return response or "سأفتح كاميرا تحليل الطعام"
        elif command == "close_food":
            if self.callbacks.get("close_food"): self.callbacks["close_food"]()
            return response or "تم إغلاق الكاميرا"
        elif command == "open_chat":
            if self.callbacks.get("open_chat"): self.callbacks["open_chat"]()
            self.context.state = CommandState.CHAT_MODE
            return response or "أنا مستعد للتحدث معك"
        elif command == "close_current":
            if self.callbacks.get("close_current"): self.callbacks["close_current"]()
            self.context.reset()
            return response or "حسناً"
        elif command == "exit_app":
            if self.callbacks.get("exit_app"): self.callbacks["exit_app"]()
            return response or "إلى اللقاء، أتمنى لك السلامة"
        elif command == "general_chat":
            text = params.get("text", "")
            if self.callbacks.get("general_chat"): return self.callbacks["general_chat"](text)
            return response
        elif command == "open_qr":
            if self.callbacks.get("open_qr"): self.callbacks["open_qr"]()
            return response
        elif command == "set_sugar":
            if self.callbacks.get("set_sugar"): self.callbacks["set_sugar"](params.get("value"))
            return response
        elif command == "generate_qr":
            if self.callbacks.get("generate_qr"): self.callbacks["generate_qr"]()
            return response
        elif command == "open_browser":
            if self.callbacks.get("open_browser"): self.callbacks["open_browser"]()
            return response
        elif command == "speak":
            if self.callbacks.get("speak"): self.callbacks["speak"](params.get("text"))
            return response
        return response or "لم أفهم الأمر"
    
    def _handle_chat(self, text: str) -> str:
        if any(k in text for k in ["اغلاق", "كفاية", "خروج", "انتهيت"]):
            self.context.reset()
            return "تمام، لو عوزتني تاني اندهلي"
        if self.callbacks.get("general_chat"): return self.callbacks["general_chat"](text)
        return "أنا أستمع"
    
    def reset(self): self.context.reset()


voice_command_processor = VoiceCommandProcessor()

if __name__ == "__main__":
    pass
