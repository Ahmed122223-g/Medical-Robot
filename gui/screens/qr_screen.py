import customtkinter as ctk
import json
import webbrowser
import os
import random
from datetime import datetime
from pathlib import Path
from PIL import Image

try:
    import qrcode
except ImportError:
    qrcode = None

from config import config
from modules.vital_signs import vital_signs_monitor
from gui.styles.theme import COLORS, FONTS, RADIUS
from core.arabic_utils import fix_arabic as _

class QRCodeScreen(ctk.CTkFrame):
    def __init__(self,parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.qr_image_label = None
        self.base_url = "https://medical-robot.netlify.app/"
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main scrollable container
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"],
            scrollbar_button_hover_color=COLORS["primary"]
        )
        self.scroll_container.grid(row=0, column=0, sticky="nsew")
        self.scroll_container.grid_columnconfigure(0, weight=1)
        self.scroll_container.grid_columnconfigure(1, weight=1)
        
        self.input_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        self.setup_inputs()
        
        # QR Frame - centered in its column
        self.qr_frame = ctk.CTkFrame(self.scroll_container, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"], border_width=1, border_color=COLORS["border"])
        self.qr_frame.grid(row=0, column=1, sticky="n", padx=20, pady=20) # sticky="n" to keep it at top and centered horizontally
        
        self.setup_qr_display()

    def setup_inputs(self):
        title = ctk.CTkLabel(self.input_frame, text=_("بوابة المريض (QR)"), font=(FONTS["family"], 24, "bold"))
        title.pack(pady=(0, 20))
        
        vitals_frame = ctk.CTkFrame(self.input_frame)
        vitals_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(vitals_frame, text=_("قراءات الأجهزة (تلقائي)"), font=(FONTS["family"], 16, "bold"), text_color="#3b82f6").pack(pady=10)
        
        self.bp_label = ctk.CTkLabel(vitals_frame, text=_("ضغط الدم: --/--"), font=(FONTS["family"], 14))
        self.bp_label.pack(pady=5)
        
        self.temp_label = ctk.CTkLabel(vitals_frame, text=_("الحرارة: -- °C"), font=(FONTS["family"], 14))
        self.temp_label.pack(pady=5)
        
        ctk.CTkButton(vitals_frame, text=_("تحديث القراءات"), command=self.update_vitals_display, width=120).pack(pady=10)
        
        manual_frame = ctk.CTkFrame(self.input_frame)
        manual_frame.pack(fill="x", pady=20)
        
        ctk.CTkLabel(manual_frame, text=_("إدخال يدوي"), font=(FONTS["family"], 16, "bold"), text_color="#f43f5e").pack(pady=10)
        
        ctk.CTkLabel(manual_frame, text=_("مستوى السكر (mg/dL):"), font=(FONTS["family"], 14)).pack(pady=5)
        self.sugar_entry = ctk.CTkEntry(manual_frame, placeholder_text=_("مثال: 120"))
        self.sugar_entry.pack(pady=5)
        self.sugar_entry.insert(0, "")
        ctk.CTkLabel(manual_frame, text=_("الوزن (kg):"), font=(FONTS["family"], 14)).pack(pady=5)
        self.weight_entry = ctk.CTkEntry(manual_frame, placeholder_text=_("مثال: 75"))
        self.weight_entry.pack(pady=5)
        self.weight_entry.insert(0, "78")
        
        self.generate_btn = ctk.CTkButton(
            self.input_frame, 
            text=_("توليد QR وتحديث الصفحة"), 
            command=self.generate_qr,
            font=(FONTS["family"], 16, "bold"),
            height=40,
            fg_color="#10b981", 
            hover_color="#059669"
        )
        self.generate_btn.pack(pady=30, fill="x")

    def setup_qr_display(self):
        self.qr_title = ctk.CTkLabel(self.qr_frame, text=_("امسح الرمز لفتح الملف"), font=(FONTS["family"], 18, "bold"))
        self.qr_title.pack(pady=(20, 10), padx=20)
        
        # Fixed size container for the QR code to ensure centering
        self.qr_container = ctk.CTkFrame(self.qr_frame, fg_color="#ffffff", corner_radius=RADIUS["md"], width=220, height=220)
        self.qr_container.pack(pady=10, padx=20)
        self.qr_container.pack_propagate(False)
        
        self.qr_image_label = ctk.CTkLabel(self.qr_container, text=_("لم يتم التوليد بعد"), text_color="#333333", font=(FONTS["family"], 12))
        self.qr_image_label.pack(expand=True, fill="both")
        
        self.link_label = ctk.CTkLabel(self.qr_frame, text=self.base_url, font=("Cairo", 12), text_color="#3b82f6", cursor="hand2")
        self.link_label.pack(pady=10)
        self.link_label.bind("<Button-1>", lambda e: webbrowser.open(self.full_url if hasattr(self, 'full_url') else self.base_url))

    def update_vitals_display(self):
        vitals = vital_signs_monitor.get_current_vitals()
        self.bp_label.configure(text=_ (f"ضغط الدم: {vitals.systolic}/{vitals.diastolic} mmHg"))
        self.temp_label.configure(text=_ (f"الحرارة: {vitals.temperature} °C"))
        
        self.bp_label.configure(text_color="#10b981")
        self.after(500, lambda: self.bp_label.configure(text_color=("black", "white")))

    def generate_qr(self):
        if not qrcode:
            print("❌ qrcode library not installed. pip install qrcode[pil]")
            return

        vitals = vital_signs_monitor.get_current_vitals()
        
        if vitals.systolic > 0:
            systolic = vitals.systolic
            diastolic = vitals.diastolic
            temp = vitals.temperature
        else:
            systolic = 120
            diastolic = 80
            temp = 37.0
        
        weight = self.weight_entry.get()
        
        sugar = self.sugar_entry.get()
        
        try:
            vital_signs_monitor.set_manual_reading("weight", float(weight) if weight else 0)
            vital_signs_monitor.set_manual_reading("sugar", float(sugar) if sugar else 0)
        except ValueError:
            print("⚠️ Invalid number format for manual inputs")

        import base64
        import urllib.parse
        
        raw_data = {
            "sys": systolic,
            "dia": diastolic,
            "w": weight,
            "s": sugar,
            "t": temp
        }
        
        json_str = json.dumps(raw_data)
        
        b64_encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        
        safe_param = urllib.parse.quote(b64_encoded)
        
        params = f"?d={safe_param}"
        self.full_url = self.base_url + params
        
        print(f"🔗 Generated Secure URL: {self.full_url}")
        
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(self.full_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        import io
        img_buffer = io.BytesIO()
        img.save(img_buffer)
        img_buffer.seek(0)
        pil_img = Image.open(img_buffer)
        
        # Scale to fit standard scanners and screen
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 200))
        self.qr_image_label.configure(image=ctk_img, text="", fg_color="transparent")
        self.link_label.configure(text=_("اضغط لفتح الرابط"))
