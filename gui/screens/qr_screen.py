import customtkinter as ctk
import json
import webbrowser
import os
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
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.qr_image_label = None
        self.base_url = "https://medical-robot.netlify.app/"
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.scroll_container = ctk.CTkScrollableFrame(self, fg_color="transparent",
            scrollbar_button_color=COLORS["bg_tertiary"], scrollbar_button_hover_color=COLORS["primary"])
        self.scroll_container.grid(row=0, column=0, sticky="nsew")
        self.scroll_container.grid_columnconfigure(0, weight=1)
        self.scroll_container.grid_columnconfigure(1, weight=1)
        self.input_frame = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.setup_inputs()
        self.qr_frame = ctk.CTkFrame(self.scroll_container, fg_color=COLORS["bg_card"], corner_radius=RADIUS["lg"], border_width=1, border_color=COLORS["border"])
        self.qr_frame.grid(row=0, column=1, sticky="n", padx=20, pady=20)
        self.setup_qr_display()

    def setup_inputs(self):
        ctk.CTkLabel(self.input_frame, text="Patient Portal (QR)", font=(FONTS["family_en"], 24, "bold")).pack(pady=(0, 20))
        vf = ctk.CTkFrame(self.input_frame)
        vf.pack(fill="x", pady=10)
        ctk.CTkLabel(vf, text="Device Readings (Auto)", font=(FONTS["family_en"], 16, "bold"), text_color="#3b82f6").pack(pady=10)
        self.bp_label = ctk.CTkLabel(vf, text="Blood Pressure: --/--", font=(FONTS["family_en"], 14))
        self.bp_label.pack(pady=5)
        self.temp_label = ctk.CTkLabel(vf, text="Temperature: -- °C", font=(FONTS["family_en"], 14))
        self.temp_label.pack(pady=5)
        ctk.CTkButton(vf, text="Refresh Readings", command=self.update_vitals_display, width=120).pack(pady=10)
        mf = ctk.CTkFrame(self.input_frame)
        mf.pack(fill="x", pady=20)
        ctk.CTkLabel(mf, text="Manual Input", font=(FONTS["family_en"], 16, "bold"), text_color="#f43f5e").pack(pady=10)
        ctk.CTkLabel(mf, text="Blood Sugar (mg/dL):", font=(FONTS["family_en"], 14)).pack(pady=5)
        self.sugar_entry = ctk.CTkEntry(mf, placeholder_text="e.g. 120")
        self.sugar_entry.pack(pady=5)
        self.sugar_entry.insert(0, "")
        ctk.CTkLabel(mf, text="Weight (kg):", font=(FONTS["family_en"], 14)).pack(pady=5)
        self.weight_entry = ctk.CTkEntry(mf, placeholder_text="e.g. 75")
        self.weight_entry.pack(pady=5)
        self.weight_entry.insert(0, "78")
        self.generate_btn = ctk.CTkButton(self.input_frame, text="Generate QR & Update", command=self.generate_qr,
            font=(FONTS["family_en"], 16, "bold"), height=40, fg_color="#10b981", hover_color="#059669")
        self.generate_btn.pack(pady=30, fill="x")

    def setup_qr_display(self):
        ctk.CTkLabel(self.qr_frame, text="Scan code to open file", font=(FONTS["family_en"], 18, "bold")).pack(pady=(20, 10), padx=20)
        self.qr_container = ctk.CTkFrame(self.qr_frame, fg_color="#ffffff", corner_radius=RADIUS["md"], width=220, height=220)
        self.qr_container.pack(pady=10, padx=20)
        self.qr_container.pack_propagate(False)
        self.qr_image_label = ctk.CTkLabel(self.qr_container, text="Not generated yet", text_color="#333333", font=(FONTS["family_en"], 12))
        self.qr_image_label.pack(expand=True, fill="both")
        self.link_label = ctk.CTkLabel(self.qr_frame, text=self.base_url, font=(FONTS["family_en"], 12), text_color="#3b82f6", cursor="hand2")
        self.link_label.pack(pady=10)
        self.link_label.bind("<Button-1>", lambda e: webbrowser.open(self.full_url if hasattr(self, 'full_url') else self.base_url))

    def update_vitals_display(self):
        vitals = vital_signs_monitor.get_current_vitals()
        self.bp_label.configure(text=f"Blood Pressure: {vitals.systolic}/{vitals.diastolic} mmHg")
        self.temp_label.configure(text=f"Temperature: {vitals.temperature} °C")
        self.bp_label.configure(text_color="#10b981")
        self.after(500, lambda: self.bp_label.configure(text_color=("black", "white")))

    def generate_qr(self):
        if not qrcode:
            return
        vitals = vital_signs_monitor.get_current_vitals()
        if vitals.systolic > 0:
            systolic, diastolic, temp = vitals.systolic, vitals.diastolic, vitals.temperature
        else:
            systolic, diastolic, temp = 120, 80, 37.0
        weight = self.weight_entry.get()
        sugar = self.sugar_entry.get()
        try:
            vital_signs_monitor.set_manual_reading("weight", float(weight) if weight else 0)
            vital_signs_monitor.set_manual_reading("sugar", float(sugar) if sugar else 0)
        except ValueError:
            pass
        import base64, urllib.parse
        raw_data = {"sys": systolic, "dia": diastolic, "w": weight, "s": sugar, "t": temp}
        json_str = json.dumps(raw_data)
        b64_encoded = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
        safe_param = urllib.parse.quote(b64_encoded)
        self.full_url = self.base_url + f"?d={safe_param}"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(self.full_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        import io
        img_buffer = io.BytesIO()
        img.save(img_buffer)
        img_buffer.seek(0)
        pil_img = Image.open(img_buffer)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 200))
        self.qr_image_label.configure(image=ctk_img, text="", fg_color="transparent")
        self.link_label.configure(text="Click to open link")
