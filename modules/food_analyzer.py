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
    print("⚠️ Google Generative AI not installed. pip install google-generativeai")

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
        if not GENAI_AVAILABLE:
            print("❌ Google Generative AI library not available")
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                print(f"✅ Food Analyzer initialized with model: {self.model_name}")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini: {e}")
        else:
            print("⚠️ Gemini API key not set")
            
        if self.cf_account_id and self.cf_api_token:
            print("✅ Cloudflare Vision initialized (Fallback)")
    
    def _analyze_with_cloudflare(self, image_path: str) -> Optional[FoodAnalysisResult]:
        if not self.cf_account_id or not self.cf_api_token:
            print("⚠️ Cloudflare credentials not set")
            return None
            
        try:
            import requests
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                image_data = list(image_bytes)
            
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cf_account_id}/ai/run/@cf/meta/llama-3.2-11b-vision-instruct"
            headers = {"Authorization": f"Bearer {self.cf_api_token}"}
            
            prompt = """
            Analyze this food image as a medical nutritionist. Respond ONLY in this exact format:
            
            Old Format:
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
            
            Evaluate for patients:
            تقييم لمرضى السكري: [مناسب / بحذر / غير مناسب]
            تقييم لمرضى الضغط: [مناسب / بحذر / غير مناسب]
            تقييم لمرضى القلب: [مناسب / بحذر / غير مناسب]
            التوصية العامة: [Recommendation in Arabic]
            """
            
            payload = {
                "image": image_data,
                "prompt": prompt,
                "max_tokens": 1024
            }
            
            print("🔄 Falling back to Cloudflare Vision...")
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    is_agreement_error = False
                    if "errors" in error_data:
                        for error in error_data["errors"]:
                            if error.get("code") == 5016:
                                is_agreement_error = True
                                break
                    
                    if is_agreement_error:
                        print("⚠️ Cloudflare Model Agreement required. Sending 'agree'...")
                        agree_payload = {
                            "image": image_data,
                            "prompt": "agree",
                            "max_tokens": 10
                        }
                        agree_response = requests.post(url, headers=headers, json=agree_payload)
                        agree_json = agree_response.json()
                        
                        agreement_successful = agree_json.get("success", False)
                        if not agreement_successful and "errors" in agree_json:
                            for error in agree_json["errors"]:
                                if "Thank you for agreeing" in error.get("message", ""):
                                    agreement_successful = True
                                    break
                        
                        if agreement_successful:
                            print("✅ Cloudflare agreement accepted. Retrying analysis...")
                            response = requests.post(url, headers=headers, json=payload)
                        else:
                            print(f"❌ Failed to accept agreement: {agree_response.text}")
                except Exception as e:
                    print(f"⚠️ Error checking agreement status: {e}")

            if response.status_code != 200:
                print(f"❌ Cloudflare API Error: {response.text}")
                return None
                
            result_json = response.json()
            if not result_json.get("success", False):
                print(f"❌ Cloudflare API Failed: {result_json}")
                return None
                
            response_text = result_json["result"]["response"]
            return self._parse_response(response_text)
            
        except Exception as e:
            print(f"❌ Cloudflare analysis failed: {e}")
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
        except Exception as e:
            print(f"❌ Error encoding image: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> FoodAnalysisResult:
        result = FoodAnalysisResult(analysis_successful=True)
        
        try:
            lines = response_text.strip().split('\n')
            current_section = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("اسم الطعام:"):
                    result.food_name_ar = line.replace("اسم الطعام:", "").strip()
                elif line.startswith("Food Name:"):
                    result.food_name = line.replace("Food Name:", "").strip()
                elif line.startswith("الوصف:"):
                    result.description = line.replace("الوصف:", "").strip()
                elif line.startswith("المكونات:"):
                    ingredients_str = line.replace("المكونات:", "").strip()
                    result.ingredients = [i.strip() for i in ingredients_str.split('،')]
                elif line.startswith("السعرات الحرارية:"):
                    try:
                        cal_str = line.replace("السعرات الحرارية:", "").strip()
                        result.nutrition.calories = int(''.join(filter(str.isdigit, cal_str)) or 0)
                    except:
                        pass
                elif line.startswith("الكربوهيدرات:"):
                    try:
                        carb_str = line.replace("الكربوهيدرات:", "").strip()
                        result.nutrition.carbohydrates = float(''.join(filter(lambda c: c.isdigit() or c == '.', carb_str)) or 0)
                    except:
                        pass
                elif line.startswith("السكريات:"):
                    try:
                        sugar_str = line.replace("السكريات:", "").strip()
                        result.nutrition.sugar = float(''.join(filter(lambda c: c.isdigit() or c == '.', sugar_str)) or 0)
                    except:
                        pass
                elif line.startswith("الدهون:"):
                    try:
                        fat_str = line.replace("الدهون:", "").strip()
                        result.nutrition.fat = float(''.join(filter(lambda c: c.isdigit() or c == '.', fat_str)) or 0)
                    except:
                        pass
                elif line.startswith("البروتين:"):
                    try:
                        protein_str = line.replace("البروتين:", "").strip()
                        result.nutrition.protein = float(''.join(filter(lambda c: c.isdigit() or c == '.', protein_str)) or 0)
                    except:
                        pass
                elif line.startswith("الصوديوم:"):
                    try:
                        sodium_str = line.replace("الصوديوم:", "").strip()
                        result.nutrition.sodium = float(''.join(filter(lambda c: c.isdigit() or c == '.', sodium_str)) or 0)
                    except:
                        pass
                elif "السكري" in line.lower() or "diabetes" in line.lower():
                    current_section = "diabetes"
                    if "غير مناسب" in line or "not suitable" in line.lower():
                        result.diabetes_suitability.is_suitable = False
                        result.diabetes_suitability.risk_level = "high"
                    elif "بحذر" in line or "caution" in line.lower():
                        result.diabetes_suitability.risk_level = "medium"
                elif "الضغط" in line.lower() or "hypertension" in line.lower():
                    current_section = "hypertension"
                    if "غير مناسب" in line or "not suitable" in line.lower():
                        result.hypertension_suitability.is_suitable = False
                        result.hypertension_suitability.risk_level = "high"
                    elif "بحذر" in line or "caution" in line.lower():
                        result.hypertension_suitability.risk_level = "medium"
                elif "القلب" in line.lower() or "heart" in line.lower():
                    current_section = "heart"
                    if "غير مناسب" in line or "not suitable" in line.lower():
                        result.heart_suitability.is_suitable = False
                        result.heart_suitability.risk_level = "high"
                    elif "بحذر" in line or "caution" in line.lower():
                        result.heart_suitability.risk_level = "medium"
                elif line.startswith("التوصية العامة:") or line.startswith("Overall:"):
                    result.overall_recommendation = line.replace("التوصية العامة:", "").replace("Overall:", "").strip()
                elif line.startswith("- ") or line.startswith("• "):
                    warning = line[2:].strip()
                    if current_section == "diabetes":
                        result.diabetes_suitability.warnings.append(warning)
                    elif current_section == "hypertension":
                        result.hypertension_suitability.warnings.append(warning)
                    elif current_section == "heart":
                        result.heart_suitability.warnings.append(warning)
            
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
                    prompt = self._get_analysis_prompt()
                    
                    response = self.model.generate_content([prompt, image])
                    return self._parse_response(response.text)
            except Exception as e:
                print(f"⚠️ Gemini analysis failed: {e}")
                error_msg = str(e)
                if "429" in error_msg or "Quota" in error_msg or "resource_exhausted" in error_msg.lower():
                    print("⚠️ Gemini Quota Exceeded. Switching to Cloudflare...")
        
        print("🔄 Trying Cloudflare Vision fallback...")
        cf_result = self._analyze_with_cloudflare(image_path)
        if cf_result:
            return cf_result
            
        return FoodAnalysisResult(
            analysis_successful=False,
            error_message="All analysis services failed. Please try again later."
        )

    def _get_analysis_prompt(self):
        return """
        أنت خبير تغذية طبية. قم بتحليل هذه الصورة للطعام وأجب بالتنسيق التالي بالضبط:
        
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
        
        تقييم لمرضى السكري:
        [مناسب / بحذر / غير مناسب]
        - [سبب 1]
        
        تقييم لمرضى الضغط:
        [مناسب / بحذر / غير مناسب]
        - [سبب 1]
        
        تقييم لمرضى القلب:
        [مناسب / بحذر / غير مناسب]
        - [سبب 1]
        
        التوصية العامة: [توصية عامة مختصرة للمريض]
        """

    
    def analyze_from_camera(self) -> FoodAnalysisResult:
        try:
            import cv2
            
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return FoodAnalysisResult(
                    analysis_successful=False,
                    error_message="Failed to open camera"
                )
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return FoodAnalysisResult(
                    analysis_successful=False,
                    error_message="Failed to capture image"
                )
            
            temp_path = config.BASE_DIR / "temp_capture.jpg"
            cv2.imwrite(str(temp_path), frame)
            
            result = self.analyze_image(str(temp_path))
            
            if temp_path.exists():
                temp_path.unlink()
            
            return result
            
        except ImportError:
            return FoodAnalysisResult(
                analysis_successful=False,
                error_message="OpenCV not installed"
            )
        except Exception as e:
            return FoodAnalysisResult(
                analysis_successful=False,
                error_message=str(e)
            )
    
    def get_suitability_emoji(self, suitability: HealthSuitability) -> str:
        if not suitability.is_suitable:
            return "❌"
        elif suitability.risk_level == "high":
            return "🔴"
        elif suitability.risk_level == "medium":
            return "🟡"
        else:
            return "✅"
    
    def format_result_for_display(self, result: FoodAnalysisResult) -> str:
        if not result.analysis_successful:
            return f"❌ خطأ في التحليل: {result.error_message}"
        
        output = []
        output.append(f"🍽️ {result.food_name_ar}")
        if result.food_name:
            output.append(f"   ({result.food_name})")
        output.append("")
        output.append(f"📝 {result.description}")
        output.append("")
        output.append("📊 المعلومات الغذائية:")
        output.append(f"   • السعرات: {result.nutrition.calories} سعرة")
        output.append(f"   • الكربوهيدرات: {result.nutrition.carbohydrates}g")
        output.append(f"   • السكريات: {result.nutrition.sugar}g")
        output.append(f"   • الدهون: {result.nutrition.fat}g")
        output.append(f"   • البروتين: {result.nutrition.protein}g")
        output.append("")
        output.append("🏥 التقييم الصحي:")
        output.append(f"   {self.get_suitability_emoji(result.diabetes_suitability)} السكري")
        output.append(f"   {self.get_suitability_emoji(result.hypertension_suitability)} الضغط")
        output.append(f"   {self.get_suitability_emoji(result.heart_suitability)} القلب")
        output.append("")
        output.append(f"💡 {result.overall_recommendation}")
        
        return "\n".join(output)
    
    def test(self):
        print("🧪 Testing Food Analyzer...")
        
        if not self.model:
            print("❌ Model not initialized")
            return False
        
        print(f"✅ Model initialized: {self.model_name}")
        print("✅ Ready to analyze food images")
        return True


food_analyzer = FoodAnalyzer()


if __name__ == "__main__":
    food_analyzer.test()
