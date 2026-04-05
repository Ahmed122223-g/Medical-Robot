import base64
import io
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from PIL import Image

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

sys.path.append('..')
from config import config


@dataclass
class NutritionalInfo:
    calories: int = 0
    protein: float = 0.0
    carbohydrates: float = 0.0
    sugar: float = 0.0
    fat: float = 0.0
    saturated_fat: float = 0.0
    fiber: float = 0.0
    sodium: float = 0.0
    cholesterol: float = 0.0

@dataclass
class HealthSuitability:
    is_suitable: bool = True
    risk_level: str = "low"
    warnings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)

@dataclass
class FoodAnalysisResult:
    food_name: str = ""
    food_name_ar: str = ""
    description: str = ""
    ingredients: list = field(default_factory=list)
    nutrition: NutritionalInfo = field(default_factory=NutritionalInfo)
    diabetes_suitability: HealthSuitability = field(default_factory=HealthSuitability)
    hypertension_suitability: HealthSuitability = field(default_factory=HealthSuitability)
    heart_suitability: HealthSuitability = field(default_factory=HealthSuitability)
    overall_recommendation: str = ""
    analysis_successful: bool = False
    error_message: str = ""


class FoodAnalyzer:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_VISION_MODEL
        self.model = None
        self.cf_account_id = config.CLOUDFLARE_ACCOUNT_ID
        self.cf_api_token = config.CLOUDFLARE_API_TOKEN
        self._initialize()
    
    def _initialize(self):
        if not GENAI_AVAILABLE or not self.api_key:
            return
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        except:
            pass
    
    def _analyze_with_cloudflare(self, image_path: str) -> Optional[FoodAnalysisResult]:
        if not self.cf_account_id or not self.cf_api_token:
            return None
        try:
            import requests
            with open(image_path, "rb") as f:
                image_data = list(f.read())
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/run/@cf/meta/llama-3.2-11b-vision-instruct"
            headers = {"Authorization": f"Bearer {self.cf_api_token}"}
            prompt = """Analyze this food image as a medical nutritionist. Respond ONLY in this exact format:
            اسم الطعام: [Arabic Name]
            Food Name: [English Name]
            الوصف: [Short description in Arabic]
            المكونات: [Ingredients in Arabic, comma separated]
            السعرات الحرارية: [Number]
            الكربوهيدرات: [Number]g
            السكريات: [Number]g
            الدهون: [Number]g
            البروتين: [Number]g
            الصوديوم: [Number]mg
            تقييم لمرضى السكري: [مناسب / بحذر / غير مناسب]
            تقييم لمرضى الضغط: [مناسب / بحذر / غير مناسب]
            تقييم لمرضى القلب: [مناسب / بحذر / غير مناسب]
            التوصية العامة: [Recommendation in Arabic]"""
            payload = {"image": image_data, "prompt": prompt, "max_tokens": 1024}
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    if "errors" in error_data:
                        for error in error_data["errors"]:
                            if error.get("code") == 5016:
                                agree_payload = {"image": image_data, "prompt": "agree", "max_tokens": 10}
                                requests.post(url, headers=headers, json=agree_payload)
                                response = requests.post(url, headers=headers, json=payload)
                                break
                except:
                    pass
            if response.status_code != 200:
                return None
            result_json = response.json()
            if not result_json.get("success"):
                return None
            return self._parse_response(result_json["result"]["response"])
        except:
            return None

    def _encode_image(self, image_path: str) -> Optional[dict]:
        try:
            img = Image.open(image_path)
            max_size = 1024
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
        except:
            return None
    
    def _parse_response(self, response_text: str) -> FoodAnalysisResult:
        result = FoodAnalysisResult(analysis_successful=True)
        try:
            lines = response_text.strip().split('\n')
            current_section = ""
            for line in lines:
                line = line.strip()
                if not line: continue
                if line.startswith("اسم الطعام:"): result.food_name_ar = line.replace("اسم الطعام:", "").strip()
                elif line.startswith("Food Name:"): result.food_name = line.replace("Food Name:", "").strip()
                elif line.startswith("الوصف:"): result.description = line.replace("الوصف:", "").strip()
                elif line.startswith("المكونات:"):
                    result.ingredients = [i.strip() for i in line.replace("المكونات:", "").strip().split('،')]
                elif line.startswith("السعرات الحرارية:"):
                    try: result.nutrition.calories = int(''.join(filter(str.isdigit, line.replace("السعرات الحرارية:", "").strip())) or 0)
                    except: pass
                elif line.startswith("الكربوهيدرات:"):
                    try: result.nutrition.carbohydrates = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.replace("الكربوهيدرات:", "").strip())) or 0)
                    except: pass
                elif line.startswith("السكريات:"):
                    try: result.nutrition.sugar = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.replace("السكريات:", "").strip())) or 0)
                    except: pass
                elif line.startswith("الدهون:"):
                    try: result.nutrition.fat = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.replace("الدهون:", "").strip())) or 0)
                    except: pass
                elif line.startswith("البروتين:"):
                    try: result.nutrition.protein = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.replace("البروتين:", "").strip())) or 0)
                    except: pass
                elif line.startswith("الصوديوم:"):
                    try: result.nutrition.sodium = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.replace("الصوديوم:", "").strip())) or 0)
                    except: pass
                elif "السكري" in line.lower() or "diabetes" in line.lower():
                    current_section = "diabetes"
                    if "غير مناسب" in line: result.diabetes_suitability.is_suitable = False; result.diabetes_suitability.risk_level = "high"
                    elif "بحذر" in line: result.diabetes_suitability.risk_level = "medium"
                elif "الضغط" in line.lower() or "hypertension" in line.lower():
                    current_section = "hypertension"
                    if "غير مناسب" in line: result.hypertension_suitability.is_suitable = False; result.hypertension_suitability.risk_level = "high"
                    elif "بحذر" in line: result.hypertension_suitability.risk_level = "medium"
                elif "القلب" in line.lower() or "heart" in line.lower():
                    current_section = "heart"
                    if "غير مناسب" in line: result.heart_suitability.is_suitable = False; result.heart_suitability.risk_level = "high"
                    elif "بحذر" in line: result.heart_suitability.risk_level = "medium"
                elif line.startswith("التوصية العامة:") or line.startswith("Overall:"):
                    result.overall_recommendation = line.replace("التوصية العامة:", "").replace("Overall:", "").strip()
                elif line.startswith("- ") or line.startswith("• "):
                    warning = line[2:].strip()
                    if current_section == "diabetes": result.diabetes_suitability.warnings.append(warning)
                    elif current_section == "hypertension": result.hypertension_suitability.warnings.append(warning)
                    elif current_section == "heart": result.heart_suitability.warnings.append(warning)
            return result
        except Exception as e:
            result.analysis_successful = False
            result.error_message = str(e)
            return result
    
    def analyze_image(self, image_path: str) -> FoodAnalysisResult:
        if self.model:
            try:
                image = self._encode_image(image_path)
                if image:
                    response = self.model.generate_content([self._get_analysis_prompt(), image])
                    return self._parse_response(response.text)
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Quota" in error_msg or "resource_exhausted" in error_msg.lower():
                    pass
        cf_result = self._analyze_with_cloudflare(image_path)
        if cf_result: return cf_result
        return FoodAnalysisResult(analysis_successful=False, error_message="All analysis services failed. Please try again later.")

    def _get_analysis_prompt(self):
        return """أنت خبير تغذية طبية. قم بتحليل هذه الصورة للطعام وأجب بالتنسيق التالي بالضبط:
        اسم الطعام: [اسم الطعام بالعربية]
        Food Name: [Food name in English]
        الوصف: [وصف قصير للطعام]
        المكونات: [المكونات الرئيسية مفصولة بفواصل]
        المعلومات الغذائية (تقديرية لكل حصة):
        السعرات الحرارية: [رقم] سعرة
        الكربوهيدرات: [رقم] جرام
        السكريات: [رقم] جرام
        الدهون: [رقم] جرام
        البروتين: [رقم] جرام
        الصوديوم: [رقم] مجم
        تقييم لمرضى السكري: [مناسب / بحذر / غير مناسب]
        - [سبب 1]
        تقييم لمرضى الضغط: [مناسب / بحذر / غير مناسب]
        - [سبب 1]
        تقييم لمرضى القلب: [مناسب / بحذر / غير مناسب]
        - [سبب 1]
        التوصية العامة: [توصية عامة مختصرة للمريض]"""
    
    def get_suitability_emoji(self, suitability: HealthSuitability) -> str:
        if not suitability.is_suitable: return "❌"
        elif suitability.risk_level == "high": return "🔴"
        elif suitability.risk_level == "medium": return "🟡"
        else: return "✅"
    
    def test(self):
        return self.model is not None


food_analyzer = FoodAnalyzer()

if __name__ == "__main__":
    food_analyzer.test()
