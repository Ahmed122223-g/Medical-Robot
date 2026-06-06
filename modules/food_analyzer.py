import base64
import io
import sys
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
from PIL import Image, ImageEnhance, ImageFilter

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
    # Multi-food support
    additional_foods: list = field(default_factory=list)  # List of FoodAnalysisResult


class FoodAnalyzer:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_name = config.GEMINI_VISION_MODEL
        self.model = None
        self.cf_account_id = config.CLOUDFLARE_ACCOUNT_ID
        self.cf_api_token = config.CLOUDFLARE_API_TOKEN
        self._last_error = ""
        self._initialize()
    
    def _initialize(self):
        if not GENAI_AVAILABLE or not self.api_key:
            print(f"[FoodAnalyzer] GENAI_AVAILABLE={GENAI_AVAILABLE}, API_KEY={'set' if self.api_key else 'MISSING'}")
            return
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            print(f"[FoodAnalyzer] Initialized with model: {self.model_name}")
        except Exception as e:
            print(f"[FoodAnalyzer] Init error: {e}")
    
    def _analyze_with_cloudflare(self, image_path: str) -> Optional[FoodAnalysisResult]:
        if not self.cf_account_id or not self.cf_api_token:
            return None
        try:
            import requests
            with open(image_path, "rb") as f:
                image_data = list(f.read())
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/run/@cf/meta/llama-3.2-11b-vision-instruct"
            headers = {"Authorization": f"Bearer {self.cf_api_token}"}
            prompt = self._get_cloudflare_prompt()
            payload = {"image": image_data, "prompt": prompt, "max_tokens": 2048}
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
                print(f"[FoodAnalyzer] Cloudflare HTTP error: {response.status_code}")
                return None
            result_json = response.json()
            if not result_json.get("success"):
                print(f"[FoodAnalyzer] Cloudflare returned success=false")
                return None
            response_text = result_json["result"]["response"]
            print(f"[FoodAnalyzer] Cloudflare response: {response_text[:200]}...")
            return self._parse_response(response_text)
        except Exception as e:
            print(f"[FoodAnalyzer] Cloudflare error: {e}")
            return None

    def _encode_image(self, image_path: str) -> Optional[Image.Image]:
        """Load, enhance and preprocess image for better AI recognition."""
        try:
            img = Image.open(image_path)
            
            # Convert to RGB first
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to optimal size for analysis
            max_size = 1024
            min_size = 512
            w, h = img.size
            if max(w, h) > max_size:
                ratio = max_size / max(w, h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            elif max(w, h) < min_size:
                ratio = min_size / max(w, h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Enhancement pipeline
            try:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.3)
            except: pass
            
            try:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.15)
            except: pass
            
            try:
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
            except: pass
            
            try:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.2)
            except: pass
            
            print(f"[FoodAnalyzer] Image preprocessed: {img.size}")
            return img
        except Exception as e:
            print(f"[FoodAnalyzer] Image encode error: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> FoodAnalysisResult:
        """Parse the AI response, supporting multi-food detection."""
        result = FoodAnalysisResult(analysis_successful=True)
        try:
            # Check if this is a multi-food response (contains separators or multiple food names)
            sections = self._split_multi_food(response_text)
            
            if len(sections) > 1:
                # Parse first food as main result
                result = self._parse_single_food(sections[0])
                result.analysis_successful = True
                # Parse additional foods
                for section in sections[1:]:
                    additional = self._parse_single_food(section)
                    if additional.food_name or additional.food_name_ar:
                        result.additional_foods.append(additional)
            else:
                result = self._parse_single_food(response_text)
                result.analysis_successful = True
            
            return result
        except Exception as e:
            print(f"[FoodAnalyzer] Parse error: {e}")
            result.analysis_successful = False
            result.error_message = str(e)
            return result
    
    def _split_multi_food(self, text: str) -> list:
        """Split response into multiple food sections."""
        # Look for separator patterns
        separators = ["---", "===", "━━━", "***", "────"]
        for sep in separators:
            if sep in text:
                parts = [p.strip() for p in text.split(sep) if p.strip()]
                # Verify each part looks like a food entry
                valid_parts = [p for p in parts if "اسم الطعام" in p or "Food Name" in p]
                if len(valid_parts) > 1:
                    return valid_parts
        
        # Check for numbered food items like "1." "2." etc.
        import re
        # Look for pattern: lines starting with digit followed by food name pattern
        food_starts = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("اسم الطعام:") or stripped.startswith("Food Name:"):
                food_starts.append(i)
        
        if len(food_starts) > 1:
            sections = []
            for idx, start in enumerate(food_starts):
                end = food_starts[idx + 1] if idx + 1 < len(food_starts) else len(lines)
                section = '\n'.join(lines[start:end])
                if section.strip():
                    sections.append(section.strip())
            if len(sections) > 1:
                return sections
        
        return [text]
    
    def _parse_single_food(self, text: str) -> FoodAnalysisResult:
        """Parse a single food section from AI response."""
        result = FoodAnalysisResult(analysis_successful=True)
        lines = text.strip().split('\n')
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove leading numbers like "1." "2." etc.
            import re
            line = re.sub(r'^\d+[\.\)]\s*', '', line)
            
            if "اسم الطعام" in line and ":" in line:
                result.food_name_ar = line.split(":", 1)[1].strip()
            elif line.startswith("Food Name") and ":" in line:
                result.food_name = line.split(":", 1)[1].strip()
            elif "الوصف" in line and ":" in line:
                result.description = line.split(":", 1)[1].strip()
            elif "المكونات" in line and ":" in line:
                ingredients_text = line.split(":", 1)[1].strip()
                # Split by Arabic comma, English comma, or dash
                for sep in ['،', ',']:
                    if sep in ingredients_text:
                        result.ingredients = [i.strip() for i in ingredients_text.split(sep)]
                        break
                else:
                    result.ingredients = [ingredients_text]
            elif "السعرات الحرارية" in line and ":" in line:
                try:
                    result.nutrition.calories = int(''.join(filter(str.isdigit, line.split(":", 1)[1].strip())) or 0)
                except: pass
            elif "الكربوهيدرات" in line and ":" in line:
                try:
                    result.nutrition.carbohydrates = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.split(":", 1)[1].strip())) or 0)
                except: pass
            elif "السكريات" in line and ":" in line:
                try:
                    result.nutrition.sugar = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.split(":", 1)[1].strip())) or 0)
                except: pass
            elif "الدهون" in line and ":" in line:
                try:
                    result.nutrition.fat = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.split(":", 1)[1].strip())) or 0)
                except: pass
            elif "البروتين" in line and ":" in line:
                try:
                    result.nutrition.protein = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.split(":", 1)[1].strip())) or 0)
                except: pass
            elif "الصوديوم" in line and ":" in line:
                try:
                    result.nutrition.sodium = float(''.join(filter(lambda c: c.isdigit() or c == '.', line.split(":", 1)[1].strip())) or 0)
                except: pass
            elif "السكري" in line or "diabetes" in line.lower():
                current_section = "diabetes"
                if "غير مناسب" in line:
                    result.diabetes_suitability.is_suitable = False
                    result.diabetes_suitability.risk_level = "high"
                elif "بحذر" in line:
                    result.diabetes_suitability.risk_level = "medium"
            elif "الضغط" in line or "hypertension" in line.lower():
                current_section = "hypertension"
                if "غير مناسب" in line:
                    result.hypertension_suitability.is_suitable = False
                    result.hypertension_suitability.risk_level = "high"
                elif "بحذر" in line:
                    result.hypertension_suitability.risk_level = "medium"
            elif "القلب" in line or "heart" in line.lower():
                current_section = "heart"
                if "غير مناسب" in line:
                    result.heart_suitability.is_suitable = False
                    result.heart_suitability.risk_level = "high"
                elif "بحذر" in line:
                    result.heart_suitability.risk_level = "medium"
            elif "التوصية العامة" in line and ":" in line:
                result.overall_recommendation = line.split(":", 1)[1].strip()
            elif "Overall" in line and ":" in line:
                result.overall_recommendation = line.split(":", 1)[1].strip()
            elif line.startswith("- ") or line.startswith("• "):
                warning = line[2:].strip()
                if current_section == "diabetes":
                    result.diabetes_suitability.warnings.append(warning)
                elif current_section == "hypertension":
                    result.hypertension_suitability.warnings.append(warning)
                elif current_section == "heart":
                    result.heart_suitability.warnings.append(warning)
        
        return result
    
    def analyze_image(self, image_path: str) -> FoodAnalysisResult:
        """Analyze food image. Tries Gemini first, then Cloudflare as fallback."""
        print(f"[FoodAnalyzer] Analyzing image: {image_path}")
        
        gemini_error = ""
        
        # Try Gemini first
        if self.model:
            try:
                image = self._encode_image(image_path)
                if image:
                    print(f"[FoodAnalyzer] Sending to Gemini ({self.model_name})...")
                    response = self.model.generate_content(
                        [self._get_analysis_prompt(), image],
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.4,
                            max_output_tokens=2048,
                        )
                    )
                    
                    if response and response.text:
                        print(f"[FoodAnalyzer] Gemini response received ({len(response.text)} chars)")
                        print(f"[FoodAnalyzer] Response preview: {response.text[:300]}...")
                        result = self._parse_response(response.text)
                        
                        # Validate - if food name is empty or "unknown", retry with simpler prompt
                        if not result.food_name and not result.food_name_ar:
                            print("[FoodAnalyzer] Empty food name, retrying with simple prompt...")
                            result = self._retry_simple(image)
                            if result:
                                return result
                        elif self._is_unknown_food(result):
                            print("[FoodAnalyzer] Got 'unknown food' response, retrying...")
                            result = self._retry_simple(image)
                            if result:
                                return result
                        else:
                            return result
                    else:
                        gemini_error = "Empty response from Gemini"
                        print(f"[FoodAnalyzer] {gemini_error}")
                        # Check for blocked response
                        if response and hasattr(response, 'prompt_feedback'):
                            print(f"[FoodAnalyzer] Prompt feedback: {response.prompt_feedback}")
                else:
                    gemini_error = "Failed to encode image"
                    print(f"[FoodAnalyzer] {gemini_error}")
            except Exception as e:
                gemini_error = str(e)
                print(f"[FoodAnalyzer] Gemini error: {gemini_error}")
                if "429" in gemini_error or "Quota" in gemini_error or "resource_exhausted" in gemini_error.lower():
                    gemini_error = "API quota exceeded"
        else:
            gemini_error = "Gemini model not initialized"
            print(f"[FoodAnalyzer] {gemini_error}")
        
        # Try Cloudflare as fallback
        print("[FoodAnalyzer] Trying Cloudflare fallback...")
        cf_result = self._analyze_with_cloudflare(image_path)
        if cf_result:
            return cf_result
        
        # All failed
        error = gemini_error or "All analysis services failed"
        self._last_error = error
        return FoodAnalysisResult(
            analysis_successful=False,
            error_message=f"{error}. Please try again."
        )
    
    def _is_unknown_food(self, result: FoodAnalysisResult) -> bool:
        """Check if the result indicates unknown food."""
        unknown_phrases = [
            "غير معروف", "لا أستطيع", "غير واضح", "لا يمكن",
            "unknown", "not identified", "cannot identify", "can't identify",
            "unidentified", "not clear", "unclear"
        ]
        name = (result.food_name + " " + result.food_name_ar).lower()
        return any(phrase in name for phrase in unknown_phrases)
    
    def _retry_simple(self, image: Image.Image) -> Optional[FoodAnalysisResult]:
        """Retry with a simpler, more direct prompt."""
        try:
            simple_prompt = """Look at this image carefully. There is food in this image.

YOUR JOB: Identify what food items are visible and provide nutritional analysis.

RULES:
- If you CANNOT identify any food in the image, or if there is no food, you MUST reply with "اسم الطعام: غير معروف" and do not guess randomly.
- If image is blurry, try your best based on color, shape, plate, context, but do not guess if unsure.
- If you see a person holding food, identify ONLY the food.
- If there are multiple food items, identify each one separately.

For EACH food item found, provide this info:
اسم الطعام: [name in Arabic]
Food Name: [name in English]
الوصف: [short description]
المكونات: [main ingredients]
السعرات الحرارية: [number]
الكربوهيدرات: [number]g
السكريات: [number]g
الدهون: [number]g
البروتين: [number]g
الصوديوم: [number]mg
تقييم لمرضى السكري: [مناسب / بحذر / غير مناسب]
تقييم لمرضى الضغط: [مناسب / بحذر / غير مناسب]
تقييم لمرضى القلب: [مناسب / بحذر / غير مناسب]
التوصية العامة: [recommendation]

If there are multiple foods, separate each food's analysis with a line of ---"""

            response = self.model.generate_content(
                [simple_prompt, image],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,  # Higher temperature for more creative guessing
                    max_output_tokens=2048,
                )
            )
            
            if response and response.text:
                print(f"[FoodAnalyzer] Retry response: {response.text[:300]}...")
                result = self._parse_response(response.text)
                if result.food_name or result.food_name_ar:
                    if not self._is_unknown_food(result):
                        return result
            
            return None
        except Exception as e:
            print(f"[FoodAnalyzer] Retry error: {e}")
            return None

    def _get_analysis_prompt(self):
        return """You are a medical nutrition expert specialized in food identification from images.

CRITICAL RULES:
1. Try your best to identify the food. Use visual clues: color, shape, size, texture, context.
2. CRITICAL: If you are unsure, or if there is NO food in the image, you MUST output "اسم الطعام: غير معروف" and DO NOT guess randomly.
3. If the image shows a person holding food or eating, IGNORE the person and focus ONLY on the food.
4. If you see multiple food items, analyze EACH food item separately, and separate them with ---
5. Common foods to look for: bread, rice, eggs, meat, chicken, fish, salad, fruit, vegetables, soup, pasta, cheese, milk, juice, cake, chocolate, chips, sandwiches, falafel, hummus, beans, lentils.

For EACH food item, respond in this EXACT format:
اسم الطعام: [اسم الطعام بالعربية]
Food Name: [English name]  
الوصف: [وصف قصير]
المكونات: [المكونات مفصولة بفواصل]
السعرات الحرارية: [رقم] سعرة
الكربوهيدرات: [رقم] جرام
السكريات: [رقم] جرام
الدهون: [رقم] جرام
البروتين: [رقم] جرام
الصوديوم: [رقم] مجم
تقييم لمرضى السكري: [مناسب / بحذر / غير مناسب]
- [سبب]
تقييم لمرضى الضغط: [مناسب / بحذر / غير مناسب]
- [سبب]
تقييم لمرضى القلب: [مناسب / بحذر / غير مناسب]
- [سبب]
التوصية العامة: [توصية مختصرة]

If multiple foods, separate with:
---"""
    
    def _get_cloudflare_prompt(self):
        return """Analyze this food image. IMPORTANT: If there is no food or you are unsure, output "اسم الطعام: غير معروف" and do not guess. If multiple foods visible, analyze each.

For each food:
اسم الطعام: [Arabic Name]
Food Name: [English Name]
الوصف: [Description]
المكونات: [Ingredients]
السعرات الحرارية: [Number]
الكربوهيدرات: [Number]g
السكريات: [Number]g
الدهون: [Number]g
البروتين: [Number]g
الصوديوم: [Number]mg
تقييم لمرضى السكري: [مناسب / بحذر / غير مناسب]
تقييم لمرضى الضغط: [مناسب / بحذر / غير مناسب]
تقييم لمرضى القلب: [مناسب / بحذر / غير مناسب]
التوصية العامة: [Recommendation]

Separate multiple foods with ---"""

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
