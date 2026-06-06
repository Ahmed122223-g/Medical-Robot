"""
AI Robot Operating System - Food Analysis Screen
Screen for capturing food images and analyzing them using Gemini Vision AI.
Fully responsive - 50/50 split, SVG-like scaling.
"""

import customtkinter as ctk
import threading
from typing import Optional
import sys

sys.path.append('../..')
from gui.styles.theme import COLORS, FONTS, RADIUS, responsive
from core.arabic_utils import fix_arabic as _
from modules.food_analyzer import food_analyzer, FoodAnalysisResult

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageTk
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class CameraCapture:
    """Wrapper to support Raspberry Pi libcamera and fallback to OpenCV V4L2/DirectShow"""
    def __init__(self):
        self.cap = None
        self.rpi_process = None
        self.rpi_running = False
        self.rpi_frame = None
        self.rpi_lock = threading.Lock()
        self.rpi_errors = []
        
    def open(self):
        import platform
        import os
        import shutil
        
        is_rpi = platform.system() == 'Linux' and ('arm' in platform.machine() or 'aarch' in platform.machine())
            
        if is_rpi:
            # Try using rpicam-vid for libcamera support
            try:
                cmd = [
                    'rpicam-vid', '-t', '0', '--inline', '--codec', 'mjpeg',
                    '--width', '640', '--height', '480', '--framerate', '15',
                    '--nopreview', '-o', '-'
                ]
                if not shutil.which('rpicam-vid') and shutil.which('libcamera-vid'):
                    cmd[0] = 'libcamera-vid'
                    
                if shutil.which(cmd[0]):
                    import subprocess
                    self.rpi_errors = []
                    self.rpi_process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE
                    )
                    self.rpi_running = True
                    threading.Thread(target=self._rpi_reader, daemon=True).start()
                    threading.Thread(target=self._rpi_error_reader, daemon=True).start()
                    
                    import time
                    time.sleep(1.5)  # Wait for first frame
                    with self.rpi_lock:
                        if self.rpi_frame is not None:
                            return True
                            
                    # If it failed to capture any frame, print stderr
                    if self.rpi_errors:
                        print("❌ rpicam-vid/libcamera-vid process error log:")
                        for err in self.rpi_errors:
                            print(f"   [stderr] {err}")
            except Exception as e:
                print("Failed to start rpicam-vid:", e)
                
            # If rpicam fails or doesn't start, try V4L2 fallback
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if self.cap.isOpened():
                return True
        
        # Default fallback for Windows / Mac / Linux (non-RPi)
        self.cap = cv2.VideoCapture(0)
        return self.cap.isOpened()

    def _rpi_error_reader(self):
        while self.rpi_running and self.rpi_process:
            try:
                line = self.rpi_process.stderr.readline()
                if not line:
                    break
                decoded_line = line.decode('utf-8', errors='ignore').strip()
                if decoded_line:
                    self.rpi_errors.append(decoded_line)
            except Exception:
                break

    def _rpi_reader(self):
        bytes_data = b''
        while self.rpi_running and self.rpi_process:
            try:
                chunk = self.rpi_process.stdout.read(4096)
                if not chunk:
                    break
                bytes_data += chunk
                
                while True:
                    a = bytes_data.find(b'\xff\xd8')
                    if a == -1:
                        if len(bytes_data) > 1:
                            bytes_data = bytes_data[-1:]
                        break
                        
                    b = bytes_data.find(b'\xff\xd9', a)
                    if b == -1:
                        bytes_data = bytes_data[a:]
                        break
                        
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        with self.rpi_lock:
                            self.rpi_frame = frame
            except Exception:
                break

    def read(self):
        if self.rpi_running:
            with self.rpi_lock:
                if self.rpi_frame is not None:
                    return True, self.rpi_frame.copy()
            return False, None
        elif self.cap and self.cap.isOpened():
            return self.cap.read()
        return False, None

    def release(self):
        self.rpi_running = False
        if self.rpi_process:
            self.rpi_process.terminate()
            self.rpi_process.wait()
            self.rpi_process = None
        if self.cap:
            self.cap.release()
            self.cap = None


class FoodScreen(ctk.CTkFrame):
    """Food Analysis Screen - Responsive 50/50 layout"""
    
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
        self._last_w = 0
        self._last_h = 0
        
        self._create_layout()
        self.bind("<Configure>", self._on_resize)
    
    def _on_resize(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        if abs(w - self._last_w) < 30 and abs(h - self._last_h) < 30:
            return
        self._last_w = w
        self._last_h = h
        self._update_responsive()
    
    def _update_responsive(self):
        r = responsive
        self.title_label.configure(font=r.font(base_size=18, weight="bold"))
        self.subtitle_label.configure(font=r.font(base_size=10))
        self.camera_btn.configure(font=r.font(base_size=11), height=r.size(38))
        self.capture_btn.configure(font=r.font(base_size=11), height=r.size(38))
        self.results_title.configure(font=r.font(base_size=13, weight="bold"))
    
    def _create_layout(self):
        r = responsive
        
        # Main grid: title on top, then 2 columns 50/50
        self.grid_columnconfigure(0, weight=1, uniform="food_col")
        self.grid_columnconfigure(1, weight=1, uniform="food_col")
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=1)  # Content
        
        # Title bar
        self.title_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=r.pad(15), pady=(r.pad(10), r.pad(4)))
        
        self.title_label = ctk.CTkLabel(
            self.title_frame,
            text="📷 AI Food Analysis",
            font=r.font(base_size=18, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(
            self.title_frame,
            text="Capture a photo of food to analyze its suitability for your health condition",
            font=r.font(base_size=10),
            text_color=COLORS["text_secondary"],
            anchor="w"
        )
        self.subtitle_label.pack(anchor="w")
        
        # Left half: Camera
        self._create_camera_section()
        
        # Right half: Results
        self._create_results_section()
    
    def _create_camera_section(self):
        r = responsive
        self.camera_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.camera_frame.grid(row=1, column=0, sticky="nsew", padx=(r.pad(15), r.pad(4)), pady=(0, r.pad(10)))
        
        self.camera_frame.grid_columnconfigure(0, weight=1)
        self.camera_frame.grid_rowconfigure(0, weight=1)
        self.camera_frame.grid_rowconfigure(1, weight=0)
        
        self.preview_label = ctk.CTkLabel(
            self.camera_frame,
            text="📷\n\nPress 'Start Camera' to begin",
            font=r.font(base_size=14),
            text_color=COLORS["text_muted"],
            fg_color=COLORS["bg_tertiary"],
            corner_radius=RADIUS["md"]
        )
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=r.pad(8), pady=r.pad(8))
        
        # 2 buttons side-by-side at bottom
        self.controls_frame = ctk.CTkFrame(
            self.camera_frame,
            fg_color="transparent"
        )
        self.controls_frame.grid(row=1, column=0, sticky="ew", padx=r.pad(8), pady=(0, r.pad(8)))
        self.controls_frame.grid_columnconfigure(0, weight=1, uniform="cam_btn")
        self.controls_frame.grid_columnconfigure(1, weight=1, uniform="cam_btn")
        
        self.camera_btn = ctk.CTkButton(
            self.controls_frame,
            text="🎥 Start Camera",
            font=r.font(base_size=11),
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            height=r.size(38),
            command=self._toggle_camera
        )
        self.camera_btn.grid(row=0, column=0, padx=r.pad(3), sticky="ew")
        
        self.capture_btn = ctk.CTkButton(
            self.controls_frame,
            text="📸 Capture & Analyze",
            font=r.font(base_size=11),
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            height=r.size(38),
            command=self._capture_and_analyze,
            state="disabled"
        )
        self.capture_btn.grid(row=0, column=1, padx=r.pad(3), sticky="ew")
    
    def _create_results_section(self):
        r = responsive
        self.results_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            corner_radius=RADIUS["lg"]
        )
        self.results_frame.grid(row=1, column=1, sticky="nsew", padx=(r.pad(4), r.pad(15)), pady=(0, r.pad(10)))
        
        self.results_title = ctk.CTkLabel(
            self.results_frame,
            text="📊 Analysis Results",
            font=r.font(base_size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        )
        self.results_title.pack(anchor="w", padx=r.pad(12), pady=(r.pad(8), r.pad(4)))
        
        self.results_scroll = ctk.CTkScrollableFrame(
            self.results_frame,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.results_scroll.pack(fill="both", expand=True, padx=r.pad(8), pady=(0, r.pad(8)))
        
        self.placeholder_label = ctk.CTkLabel(
            self.results_scroll,
            text="🍽️\n\nCapture a photo to start analysis",
            font=r.font(base_size=13),
            text_color=COLORS["text_muted"]
        )
        self.placeholder_label.pack(expand=True, pady=r.pad(40))
    
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
            self.cap = CameraCapture()
            if not self.cap.open():
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
        
        r = responsive
        self.capture_btn.configure(state="disabled", text="⏳ Analyzing...")
        self._clear_results()
        
        loading_label = ctk.CTkLabel(
            self.results_scroll,
            text="⏳\n\nAnalyzing image...\nPlease wait",
            font=r.font(base_size=13),
            text_color=COLORS["primary"]
        )
        loading_label.pack(expand=True, pady=r.pad(40))
        
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
        r = responsive
        self.capture_btn.configure(state="normal", text="📸 Capture & Analyze")
        
        if not result.analysis_successful:
            error_msg = result.error_message
            if "429" in error_msg or "Quota" in error_msg:
                error_msg = "⚠️ Daily free AI usage limit exceeded.\nPlease try again later."
            
            ctk.CTkLabel(
                self.results_scroll,
                text=f"❌ {error_msg}",
                font=r.font(base_size=13),
                text_color=COLORS["danger"]
            ).pack(expand=True, pady=r.pad(40))
            return
        
        self.analysis_result = result
        
        # Count total foods found
        total_foods = 1 + len(getattr(result, 'additional_foods', []))
        if total_foods > 1:
            ctk.CTkLabel(
                self.results_scroll,
                text=f"🔍 Found {total_foods} food items",
                font=r.font(base_size=12, weight="bold"),
                text_color=COLORS["primary"]
            ).pack(anchor="w", padx=r.pad(4), pady=r.pad(4))
        
        # Show main food
        self._render_single_food(result, food_number=1 if total_foods > 1 else 0)
        
        # Show additional foods
        for idx, extra_food in enumerate(getattr(result, 'additional_foods', [])):
            # Separator
            sep_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["border"], height=2)
            sep_frame.pack(fill="x", pady=r.pad(6), padx=r.pad(8))
            
            self._render_single_food(extra_food, food_number=idx + 2)
        
        self._speak_results(result)
    
    def _render_single_food(self, result, food_number=0):
        """Render a single food item's analysis results."""
        r = responsive
        
        self._add_suitability_warning(result)
        
        # Food name with number if multiple
        name_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["md"])
        name_frame.pack(fill="x", pady=r.pad(3))
        
        display_name = result.food_name or result.food_name_ar or "Unknown Food"
        food_label = f"🍽️ {display_name}" if not food_number else f"🍽️ [{food_number}] {display_name}"
        ctk.CTkLabel(
            name_frame,
            text=food_label,
            font=r.font(base_size=15, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w", padx=r.pad(10), pady=r.pad(6))
        
        if result.description:
            wrap = max(200, int(self.winfo_width() * 0.35))
            ctk.CTkLabel(
                self.results_scroll,
                text=result.description,
                font=r.font(base_size=10),
                text_color=COLORS["text_secondary"],
                anchor="w",
                wraplength=wrap
            ).pack(anchor="w", pady=r.pad(4), padx=r.pad(3), fill="x")
        
        self._add_nutrition_section(result)
        self._add_suitability_section(result)
        
        if result.overall_recommendation:
            rec_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["primary"], corner_radius=RADIUS["md"])
            rec_frame.pack(fill="x", pady=r.pad(4))
            
            wrap = max(200, int(self.winfo_width() * 0.35))
            ctk.CTkLabel(
                rec_frame,
                text=f"💡 {result.overall_recommendation}",
                font=r.font(base_size=10),
                text_color="#ffffff",
                anchor="w",
                wraplength=wrap
            ).pack(anchor="w", padx=r.pad(10), pady=r.pad(8), fill="x")
    
    def _speak_results(self, result: FoodAnalysisResult):
        try:
            from modules.voice_assistant import voice_assistant
            
            speech_parts = []
            
            # Collect all food names
            all_foods = [result]
            all_foods.extend(getattr(result, 'additional_foods', []))
            
            if len(all_foods) > 1:
                food_names = []
                for f in all_foods:
                    name = f.food_name or f.food_name_ar or ""
                    if name:
                        food_names.append(name)
                if food_names:
                    speech_parts.append(f"I found {len(food_names)} food items in the image: {', '.join(food_names)}")
            else:
                food_name = result.food_name or result.food_name_ar or "food"
                speech_parts.append(f"This food is {food_name}")
            
            warnings = []
            
            if not result.diabetes_suitability.is_suitable or result.diabetes_suitability.risk_level == "high":
                sugar_warning = ""
                if result.nutrition.sugar > 15:
                    sugar_warning = f"sugar content is high at {result.nutrition.sugar} grams"
                elif result.nutrition.carbohydrates > 50:
                    sugar_warning = f"carbohydrate content is high at {result.nutrition.carbohydrates} grams"
                else:
                    sugar_warning = "sugar content is high"
                warnings.append(f"{sugar_warning}, which is risky for diabetes patients")
            
            if not result.hypertension_suitability.is_suitable or result.hypertension_suitability.risk_level == "high":
                if result.nutrition.sodium > 500:
                    warnings.append(f"sodium content is high at {result.nutrition.sodium} milligrams, which is risky for hypertension patients")
                else:
                    warnings.append("sodium content is high, which is risky for hypertension patients")
            
            if not result.heart_suitability.is_suitable or result.heart_suitability.risk_level == "high":
                if result.nutrition.fat > 20:
                    warnings.append(f"fat content is high at {result.nutrition.fat} grams, which is risky for heart patients")
                elif result.nutrition.cholesterol > 100:
                    warnings.append(f"cholesterol is high, which is risky for heart patients")
                else:
                    warnings.append("fat content is high, which is risky for heart patients")
            
            if warnings:
                speech_parts.append("Warning")
                speech_parts.extend(warnings)
                speech_parts.append("This food is not suitable for your health condition")
            else:
                all_suitable = (
                    result.diabetes_suitability.is_suitable and 
                    result.hypertension_suitability.is_suitable and 
                    result.heart_suitability.is_suitable
                )
                if all_suitable:
                    speech_parts.append("This food is suitable for your health condition")
                else:
                    speech_parts.append("It is recommended to consume it in moderation")
            
            full_speech = ". ".join(speech_parts)
            voice_assistant.speak(full_speech, wait=False)
            
        except Exception:
            pass
    
    def _add_suitability_warning(self, result: FoodAnalysisResult):
        r = responsive
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
                corner_radius=RADIUS["md"],
                border_width=2,
                border_color=COLORS["danger"]
            )
            warning_frame.pack(fill="x", pady=r.pad(4))
            
            header_frame = ctk.CTkFrame(warning_frame, fg_color=COLORS["danger"], corner_radius=RADIUS["sm"])
            header_frame.pack(fill="x", padx=r.pad(3), pady=r.pad(3))
            
            ctk.CTkLabel(
                header_frame,
                text="⚠️ This food is not suitable",
                font=r.font(base_size=12, weight="bold"),
                text_color="#ffffff",
                anchor="center"
            ).pack(pady=r.pad(6))
            
            conditions_text = "Not suitable for: " + " - ".join(unsuitable_conditions)
            ctk.CTkLabel(
                warning_frame,
                text=conditions_text,
                font=r.font(base_size=10, weight="bold"),
                text_color=COLORS["danger"],
                anchor="w"
            ).pack(anchor="w", padx=r.pad(10), pady=(r.pad(4), r.pad(2)))
            
            if reasons:
                unique_reasons = list(dict.fromkeys(reasons))
                for reason in unique_reasons[:4]:
                    ctk.CTkLabel(
                        warning_frame,
                        text=f"• {reason}",
                        font=r.font(base_size=9),
                        text_color=COLORS["text_secondary"],
                        anchor="w",
                        wraplength=max(200, int(self.winfo_width() * 0.3))
                    ).pack(anchor="w", padx=r.pad(12), pady=1)
            
            ctk.CTkLabel(warning_frame, text="", height=r.pad(4)).pack()
    
    def _add_nutrition_section(self, result: FoodAnalysisResult):
        r = responsive
        section_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["md"], border_width=1, border_color=COLORS["border"])
        section_frame.pack(fill="x", pady=r.pad(3))
        
        ctk.CTkLabel(
            section_frame,
            text="📊 Nutritional Information",
            font=r.font(base_size=11, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w", padx=r.pad(10), pady=(r.pad(6), r.pad(2)))
        
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
            item_frame.pack(fill="x", padx=r.pad(10), pady=1)
            
            ctk.CTkLabel(
                item_frame,
                text=name,
                font=r.font(base_size=9),
                text_color=COLORS["text_secondary"]
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=f"{value} {unit}",
                font=r.font(base_size=9),
                text_color=COLORS["text_muted"]
            ).pack(side="right")
        
        ctk.CTkLabel(section_frame, text="", height=r.pad(4)).pack()
    
    def _add_suitability_section(self, result: FoodAnalysisResult):
        r = responsive
        section_frame = ctk.CTkFrame(self.results_scroll, fg_color=COLORS["bg_secondary"], corner_radius=RADIUS["md"], border_width=1, border_color=COLORS["border"])
        section_frame.pack(fill="x", pady=r.pad(3))
        
        ctk.CTkLabel(
            section_frame,
            text="🏥 Health Assessment",
            font=r.font(base_size=11, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w"
        ).pack(anchor="w", padx=r.pad(10), pady=(r.pad(6), r.pad(2)))
        
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
            item_frame.pack(fill="x", padx=r.pad(10), pady=r.pad(2))
            
            ctk.CTkLabel(
                item_frame,
                text=name,
                font=r.font(base_size=10),
                text_color=color
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=emoji,
                font=r.font_ar(base_size=13),
            ).pack(side="right")
        
        ctk.CTkLabel(section_frame, text="", height=r.pad(4)).pack()
    
    def on_hide(self):
        self._stop_camera()
    
    def on_show(self):
        pass
