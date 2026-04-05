"""
AI Robot Operating System - Food Analysis Screen
Screen for capturing food images and analyzing them using Gemini Vision AI.
"""

import customtkinter as ctk
import threading
from typing import Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS
from core.arabic_utils import fix_arabic as _
from modules.food_analyzer import food_analyzer, FoodAnalysisResult

try:
    import cv2
    from PIL import Image, ImageTk
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class FoodScreen(ctk.CTkFrame):
    """Food Analysis Screen"""
    
    def __init__(self, master, app_controller=None, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        
        self.app = app_controller
        self.camera_running = False
        self.cap = None
        self.current_frame = None
        self.analysis_result: Optional[FoodAnalysisResult] = None
        
        self._create_layout()
    
    def _create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="📷 AI Food Analysis",
            font=(FONTS["family_en"], FONTS["size_2xl"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="Capture a photo of food to analyze its suitability for your health condition",
            font=(FONTS["family_en"], FONTS["size_sm"]),
            text_color=COLORS["text_secondary"],
            anchor="w",
            wraplength=600
        )
        self.subtitle_label.pack(anchor="w")
        
        self._create_camera_section()
        
        self._create_results_section()
    
    def _create_camera_section(self):
        self.camera_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.camera_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        
        self.camera_frame.grid_columnconfigure(0, weight=1)
        self.camera_frame.grid_rowconfigure(0, weight=1)
        self.camera_frame.grid_rowconfigure(1, weight=0)
        
        self.preview_label = ctk.CTkLabel(
            self.camera_frame,
            text="📷\n\nPress 'Start Camera' to begin",
            font=(FONTS["family_en"], FONTS["size_lg"]),
            text_color=COLORS["text_muted"],
            fg_color=COLORS["bg_tertiary"],
            corner_radius=RADIUS["md"]
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        self.controls_frame = ctk.CTkFrame(
            self.camera_frame,
            fg_color="transparent"
        )
        self.controls_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        self.camera_btn = ctk.CTkButton(
            self.controls_frame,
            text="🎥 Start Camera",
            font=(FONTS["family_en"], FONTS["size_md"]),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=45,
            command=self._toggle_camera
        )
        self.camera_btn.pack(side="left", padx=5)
        
        self.capture_btn = ctk.CTkButton(
            self.controls_frame,
            text="📸 Capture & Analyze",
            font=(FONTS["family_en"], FONTS["size_md"]),
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            height=45,
            command=self._capture_and_analyze,
            state="disabled"
        )
        self.capture_btn.pack(side="left", padx=5)
    
    def _create_results_section(self):
        self.results_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        
        self.results_title = ctk.CTkLabel(
            self.results_frame,
            text="📊 Analysis Results",
            font=(FONTS["family_en"], FONTS["size_lg"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.results_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        self.results_scroll = ctk.CTkScrollableFrame(
            self.results_frame,
            fg_color="transparent"
        )
        self.results_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.placeholder_label = ctk.CTkLabel(
            self.results_scroll,
            text="🍽️\n\nCapture a photo to start analysis",
            font=(FONTS["family_en"], FONTS["size_lg"]),
            text_color=COLORS["text_muted"]
        )
        self.placeholder_label.pack(expand=True, pady=50)
    
    def _toggle_camera(self):
        if self.camera_running:
            self._stop_camera()
        else:
            self._start_camera()
    
    def _start_camera(self):
        if not CV2_AVAILABLE:
            self.preview_label.configure(
                text="❌\n\nCamera not available\nPlease install OpenCV"
            )
            return
        
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                self.preview_label.configure(
                    text="❌\n\nFailed to open camera"
                )
                return
            
            self.camera_running = True
            self.camera_btn.configure(text="⏹️ Stop Camera", fg_color=COLORS["danger"])
            self.capture_btn.configure(state="normal")
            
            threading.Thread(target=self._camera_loop, daemon=True).start()
            
        except Exception as e:
            self.preview_label.configure(text=f"❌ Error: {str(e)}")
    
    def _stop_camera(self):
        self.camera_running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.camera_btn.configure(text="🎥 Start Camera", fg_color=COLORS["primary"])
        self.capture_btn.configure(state="disabled")
        
        self.preview_label.configure(
            text="📷\n\nPress 'Start Camera' to begin",
            image=None
        )
    
    def _camera_loop(self):
        while self.camera_running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = frame.copy()
                    
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    preview_width = self.preview_label.winfo_width() - 10
                    preview_height = self.preview_label.winfo_height() - 10
                    
                    if preview_width > 100 and preview_height > 100:
                        h, w = frame_rgb.shape[:2]
                        aspect = w / h
                        
                        if preview_width / preview_height > aspect:
                            new_height = preview_height
                            new_width = int(preview_height * aspect)
                        else:
                            new_width = preview_width
                            new_height = int(preview_width / aspect)
                        
                        frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
                        
                        img = Image.fromarray(frame_resized)
                        photo = ctk.CTkImage(light_image=img, dark_image=img, 
                                           size=(new_width, new_height))
                        
                        self.preview_label.configure(text="", image=photo)
                        self.preview_label.image = photo
                
            except Exception:
                break
    
    def _capture_and_analyze(self):
        if self.current_frame is None:
            return
        
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        image_path = os.path.join(temp_dir, "food_capture.jpg")
        cv2.imwrite(image_path, self.current_frame)
        
        self.capture_btn.configure(state="disabled", text="⏳ Analyzing...")
        self._clear_results()
        
        loading_label = ctk.CTkLabel(
            self.results_scroll,
            text="⏳\n\nAnalyzing image...\nPlease wait",
            font=(FONTS["family_en"], FONTS["size_lg"]),
            text_color=COLORS["primary"]
        )
        loading_label.pack(expand=True, pady=50)
        
        def analyze():
            result = food_analyzer.analyze_image(image_path)
            self.after(0, lambda: self._show_results(result))
            
            try:
                os.remove(image_path)
            except:
                pass
        
        threading.Thread(target=analyze, daemon=True).start()
    
    def _clear_results(self):
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
    
    def _show_results(self, result: FoodAnalysisResult):
        self._clear_results()
        self.capture_btn.configure(state="normal", text="📸 Capture & Analyze")
        
        if not result.analysis_successful:
            error_msg = result.error_message
            if "429" in error_msg or "Quota" in error_msg:
                error_msg = "⚠️ Daily free AI usage limit exceeded.\nPlease try again later."
            
            error_label = ctk.CTkLabel(
                self.results_scroll,
                text=f"❌ {error_msg}",
                font=(FONTS["family_en"], FONTS["size_lg"]),
                text_color=COLORS["danger"]
            )
            error_label.pack(expand=True, pady=50)
            return
        
        self.analysis_result = result
        
        self._add_suitability_warning(result)
        
        name_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["lg"])
        name_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            name_frame,
            text=f"🍽️ {result.food_name_ar}",
            font=(FONTS["family"], FONTS["size_xl"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w", padx=15, pady=10)
        
        if result.food_name:
            ctk.CTkLabel(
                name_frame,
                text=f"({result.food_name})",
                font=(FONTS["family_en"], FONTS["size_sm"]),
                text_color=COLORS["text_muted"],
                anchor="w"
            ).pack(anchor="w", padx=15, pady=(0, 10))
        
        if result.description:
            ctk.CTkLabel(
                self.results_scroll,
                text=result.description,
                font=(FONTS["family"], FONTS["size_md"]),
                text_color=COLORS["text_secondary"],
                anchor="w",
                wraplength=int(self.winfo_width() * 0.4) if self.winfo_width() > 100 else 350
            ).pack(anchor="w", pady=10, padx=5, fill="x")
        
        self._add_nutrition_section(result)
        
        self._add_suitability_section(result)
        
        if result.overall_recommendation:
            rec_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["primary"], corner_radius=RADIUS["md"])
            rec_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                rec_frame,
                text=f"💡 {result.overall_recommendation}",
                font=(FONTS["family"], FONTS["size_md"]),
                text_color="#ffffff",
                anchor="w",
                wraplength=int(self.winfo_width() * 0.45) if self.winfo_width() > 100 else 450
            ).pack(anchor="w", padx=15, pady=15, fill="x")
        
        self._speak_results(result)
    
    def _speak_results(self, result: FoodAnalysisResult):
        try:
            from modules.voice_assistant import voice_assistant
            
            speech_parts = []
            
            food_name = result.food_name_ar or result.food_name or "طعام غير معروف"
            speech_parts.append(f"هذا الطعام هو {food_name}")
            
            warnings = []
            
            if not result.diabetes_suitability.is_suitable or result.diabetes_suitability.risk_level == "high":
                sugar_warning = ""
                if result.nutrition.sugar > 15:
                    sugar_warning = f"نسبة السكريات مرتفعة وتبلغ {result.nutrition.sugar} جرام"
                elif result.nutrition.carbohydrates > 50:
                    sugar_warning = f"نسبة الكربوهيدرات مرتفعة وتبلغ {result.nutrition.carbohydrates} جرام"
                else:
                    sugar_warning = "نسبة السكريات مرتفعة"
                warnings.append(f"{sugar_warning}، وهذا خطر على مرضى السكري")
            
            if not result.hypertension_suitability.is_suitable or result.hypertension_suitability.risk_level == "high":
                if result.nutrition.sodium > 500:
                    warnings.append(f"نسبة الصوديوم مرتفعة وتبلغ {result.nutrition.sodium} ملليجرام، وهذا خطر على مرضى الضغط")
                else:
                    warnings.append("نسبة الصوديوم مرتفعة، وهذا خطر على مرضى الضغط")
            
            if not result.heart_suitability.is_suitable or result.heart_suitability.risk_level == "high":
                if result.nutrition.fat > 20:
                    warnings.append(f"نسبة الدهون مرتفعة وتبلغ {result.nutrition.fat} جرام، وهذا خطر على مرضى القلب")
                elif result.nutrition.cholesterol > 100:
                    warnings.append(f"نسبة الكوليسترول مرتفعة، وهذا خطر على مرضى القلب")
                else:
                    warnings.append("نسبة الدهون مرتفعة، وهذا خطر على مرضى القلب")
            
            if warnings:
                speech_parts.append("تحذير")
                speech_parts.extend(warnings)
                speech_parts.append("هذا الطعام غير مناسب لحالتك الصحية")
            else:
                all_suitable = (
                    result.diabetes_suitability.is_suitable and 
                    result.hypertension_suitability.is_suitable and 
                    result.heart_suitability.is_suitable
                )
                if all_suitable:
                    speech_parts.append("هذا الطعام مناسب لحالتك الصحية")
                else:
                    speech_parts.append("ينصح بتناوله بكميات معتدلة")
            
            full_speech = ". ".join(speech_parts)
            voice_assistant.speak(full_speech, wait=False)
            
        except Exception:
            pass
    
    def _add_suitability_warning(self, result: FoodAnalysisResult):
        unsuitable_conditions = []
        reasons = []
        
        if not result.diabetes_suitability.is_suitable or result.diabetes_suitability.risk_level == "high":
            unsuitable_conditions.append("Diabetes Patients")
            if result.diabetes_suitability.warnings:
                reasons.extend(result.diabetes_suitability.warnings)
            elif result.nutrition.sugar > 15:
                reasons.append(f"High sugar content ({result.nutrition.sugar}g)")
            elif result.nutrition.carbohydrates > 50:
                reasons.append(f"High carbohydrate content ({result.nutrition.carbohydrates}g)")
        
        if not result.hypertension_suitability.is_suitable or result.hypertension_suitability.risk_level == "high":
            unsuitable_conditions.append("Hypertension Patients")
            if result.hypertension_suitability.warnings:
                reasons.extend(result.hypertension_suitability.warnings)
            elif result.nutrition.sodium > 500:
                reasons.append(f"High sodium content ({result.nutrition.sodium}mg)")
        
        if not result.heart_suitability.is_suitable or result.heart_suitability.risk_level == "high":
            unsuitable_conditions.append("Heart Disease Patients")
            if result.heart_suitability.warnings:
                reasons.extend(result.heart_suitability.warnings)
            elif result.nutrition.fat > 20:
                reasons.append(f"High fat content ({result.nutrition.fat}g)")
            elif result.nutrition.cholesterol > 100:
                reasons.append(f"High cholesterol ({result.nutrition.cholesterol}mg)")
        
        if unsuitable_conditions:
            warning_frame = ctk.CTkFrame(
                self.results_scroll, 
                fg_color=COLORS["danger_light"], 
                corner_radius=RADIUS["lg"],
                border_width=2,
                border_color=COLORS["danger"]
            )
            warning_frame.pack(fill="x", pady=10)
            
            header_frame = ctk.CTkFrame(warning_frame, fg_color=COLORS["danger"], corner_radius=RADIUS["md"])
            header_frame.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(
                header_frame,
                text="⚠️ This food is not suitable",
                font=(FONTS["family_en"], FONTS["size_lg"], "bold"),
                text_color="#ffffff",
                anchor="center"
            ).pack(pady=10)
            
            conditions_text = "Not suitable for: " + " - ".join(unsuitable_conditions)
            ctk.CTkLabel(
                warning_frame,
                text=conditions_text,
                font=(FONTS["family_en"], FONTS["size_md"], "bold"),
                text_color=COLORS["danger"],
                anchor="w"
            ).pack(anchor="w", padx=15, pady=(10, 5))
            
            if reasons:
                ctk.CTkLabel(
                    warning_frame,
                    text="📋 Reasons:",
                    font=(FONTS["family_en"], FONTS["size_md"], "bold"),
                    text_color=COLORS["text_primary"],
                    anchor="w"
                ).pack(anchor="w", padx=15, pady=(5, 0))
                
                unique_reasons = list(dict.fromkeys(reasons))
                for reason in unique_reasons[:5]:
                    ctk.CTkLabel(
                        warning_frame,
                        text=f"• {reason}",
                        font=(FONTS["family_en"], FONTS["size_sm"]),
                        text_color=COLORS["text_secondary"],
                        anchor="w",
                        wraplength=300
                    ).pack(anchor="w", padx=20, pady=2)
            
            ctk.CTkLabel(warning_frame, text="", height=10).pack()
    
    def _add_nutrition_section(self, result: FoodAnalysisResult):
        section_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["lg"], border_width=1, border_color=COLORS["border"])
        section_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            section_frame,
            text="📊 Nutritional Information",
            font=(FONTS["family_en"], FONTS["size_md"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        nutrition = result.nutrition
        items = [
            ("Calories", f"{nutrition.calories}", "kcal"),
            ("Carbohydrates", f"{nutrition.carbohydrates}", "g"),
            ("Sugar", f"{nutrition.sugar}", "g"),
            ("Fat", f"{nutrition.fat}", "g"),
            ("Protein", f"{nutrition.protein}", "g"),
        ]
        
        for name, value, unit in items:
            item_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            item_frame.pack(fill="x", padx=15, pady=2)
            
            ctk.CTkLabel(
                item_frame,
                text=name,
                font=(FONTS["family_en"], FONTS["size_sm"]),
                text_color=COLORS["text_secondary"]
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=f"{value} {unit}",
                font=(FONTS["family_en"], FONTS["size_sm"]),
                text_color=COLORS["text_muted"]
            ).pack(side="right")
        
        ctk.CTkLabel(section_frame, text="", height=10).pack()
    
    def _add_suitability_section(self, result: FoodAnalysisResult):
        section_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["lg"], border_width=1, border_color=COLORS["border"])
        section_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            section_frame,
            text="🏥 Health Assessment",
            font=(FONTS["family_en"], FONTS["size_md"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        suitabilities = [
            ("Diabetes", result.diabetes_suitability),
            ("Hypertension", result.hypertension_suitability),
            ("Heart Disease", result.heart_suitability),
        ]
        
        for name, suit in suitabilities:
            emoji = food_analyzer.get_suitability_emoji(suit)
            color = COLORS["success"] if suit.is_suitable and suit.risk_level == "low" else (
                COLORS["warning"] if suit.risk_level == "medium" else COLORS["danger"]
            )
            
            item_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            item_frame.pack(fill="x", padx=15, pady=3)
            
            ctk.CTkLabel(
                item_frame,
                text=name,
                font=(FONTS["family_en"], FONTS["size_md"]),
                text_color=color
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=emoji,
                font=(FONTS["family"], FONTS["size_lg"]),
            ).pack(side="right")
        
        ctk.CTkLabel(section_frame, text="", height=10).pack()
    
    def on_hide(self):
        self._stop_camera()
    
    def on_show(self):
        pass
