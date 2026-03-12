# 🤖 AI Robot Operating System

## نظام تشغيل الروبوت الطبي الذكي

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Raspberry%20Pi-red.svg" alt="Platform">
  <img src="https://img.shields.io/badge/AI-Gemini-green.svg" alt="AI">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

نظام تشغيل متكامل للروبوت الطبي الذكي يعمل على Raspberry Pi مع شاشة لمس. النظام مصمم لمساعدة المرضى الذين يعانون من السكري وارتفاع ضغط الدم وأمراض القلب.

---

## ✨ الميزات

### 📷 تحليل الطعام بالذكاء الاصطناعي

- التقاط صور الطعام باستخدام كاميرا Raspberry Pi
- تحليل المكونات والقيمة الغذائية
- تقييم ملاءمة الطعام لمرضى السكري والضغط والقلب
- توصيات صحية فورية

### 📊 مراقبة العلامات الحيوية

- استقبال بيانات من Arduino عبر Serial
- عرض ضغط الدم ونبضات القلب ودرجة الحرارة
- تنبيهات فورية عند القراءات غير الطبيعية

### 💬 شات بوت ذكي

- محادثة طبيعية باللغة العربية
- سياق طبي (يعرف حالة المريض)
- تذكير بمواعيد الأدوية
- إجابة على الأسئلة الصحية

### 💊 تذكير بالأدوية

- جدول كامل للأدوية اليومية
- تنبيهات صوتية ومرئية
- حاسبة جرعة الأنسولين
- تتبع الأدوية المأخوذة

---

## 🛠️ دليل التجهيز من الألف إلى الياء (Raspberry Pi 4B)

هذا الدليل مخصص لتجهيز نظام التشغيل والبيئة البرمجية والعتاد الصلب بالكامل.

### 1️⃣ المكونات المطلوبة (Hardware)
- **Raspberry Pi 4B** (يفضل رامات 4 جيجا أو أكثر).
- **كاميرا Raspberry Pi** (V2 أو V3).
- **شاشة لمس** (7 بوصة أو HDMI).
- **Arduino Uno/Nano** + حساسات (نبض، حرارة، ضغط).
- **بطاقة ذاكرة (Micro SD)** سعة 16 جيجا على الأقل.
- **مزود طاقة** 5V 3A (Type-C).

### 2️⃣ تجهيز نظام التشغيل (OS)
1. قم بتحميل **Raspberry Pi Imager** على جهاز الكمبيوتر الخاص بك.
2. اختر نظام التشغيل: **Raspberry Pi OS (64-bit)**.
3. قم بضبط الإعدادات المتقدمة (اسم الجهاز، كلمة المرور، تفعيل SSH، إعدادات الواي فاي).
4. قم بحرق النظام على بطاقة الذاكرة وقم بإدخالها في الراسبري باي.

### 3️⃣ إعدادات النظام الأساسية
بعد فتح الراسبري باي، افتح Terminal ونفذ التالي:
```bash
# تحديث النظام
sudo apt update && sudo apt upgrade -y

# تفعيل الكاميرا وواجهات التواصل
sudo raspi-config
# انتقل إلى Interface Options ثم قم بتفعيل:
# - I2C
# - SPI
# - Camera
```

### 4️⃣ تثبيت المشروع والبيئة البرمجية
```bash
# الانتقال لمجلد البيت
cd /home/pi

# تحميل ملفات المشروع
git clone <repository-url> mariam_pro
cd mariam_pro/AI

# إنشاء البيئة الافتراضية
python3 -m venv venv
source venv/bin/activate

# تثبيت المكتبات اللازمة
# ملاحظة: قد تحتاج لتثبيت مكتبات النظام لبعض ملفات OpenCV
sudo apt install -y libatlas-base-dev libhdf5-dev libqt5gui5 libqt5test5
pip install -r requirements.txt
```

### 5️⃣ إعداد مفاتيح API
1. انسخ ملف الإعدادات المثال: `cp .env.example .env`
2. حرر الملف: `nano .env`
3. أضف مفاتيحك الخاصة لكل من:
   - `GEMINI_API_KEY` (من Google AI Studio)
   - `ELEVENLABS_API_KEY` (من ElevenLabs للصوت)
   - `GROQ_API_KEY` (اختياري للشات بوت السريع)

### 6️⃣ ربط الأردوينو (Arduino)
1. قم برفع كود الأردوينو الموجود في مجلد `AI/core/arduino_code` (إن وجد) أو استخدم المثال في قسم إعداد الأردوينو بالأسفل.
2. تأكد من توصيل الأردوينو عبر منفذ USB بالراسبري باي.
3. تأكد من ضبط المنفذ في ملف `.env` (غالباً `/dev/ttyUSB0` أو `/dev/ttyACM0`).

### 7️⃣ التشغيل التلقائي الفوري (Instant Autostart)
لجعل البرنامج يعمل بمجرد تشغيل الشاشة وبدون تدخل منك:
1. سكريبت `install.sh` يقوم تلقائياً بوضع ملف `airobot.desktop` في مجلد `~/.config/autostart/`.
2. تأكد من تفعيل **Auto-login** في إعدادات الراسبري باي:
   ```bash
   sudo raspi-config
   # System Options -> Boot / Auto Login -> Desktop Autologin
   ```
3. عند إعادة التشغيل، ستفتح الواجهة البرمجية فوراً بعد تحميل سطح المكتب.

### 8️⃣ التشغيل كخدمة خلفية (اختياري)
إذا أردت تشغيله كخدمة نظام (Systemd):
```bash
sudo systemctl enable airobot.service
sudo systemctl start airobot.service
```

---

## 📁 هيكل المشروع

```
AI/
├── main.py                    # نقطة البداية الرئيسية
├── config.py                  # إعدادات التطبيق
├── requirements.txt           # المتطلبات
├── .env                       # متغيرات البيئة (سري)
├── .env.example              # قالب متغيرات البيئة
├── boot/
│   └── autostart.sh          # سكريبت الإقلاع التلقائي
├── core/
│   ├── __init__.py
│   ├── arduino_comm.py       # اتصال Arduino
│   └── utils.py              # دوال مساعدة
├── modules/
│   ├── __init__.py
│   ├── food_analyzer.py      # تحليل الطعام
│   ├── chatbot.py            # الشات بوت
│   ├── medication_reminder.py # تذكير الأدوية
│   └── vital_signs.py        # العلامات الحيوية
└── gui/
    ├── __init__.py
    ├── main_window.py        # النافذة الرئيسية
    ├── screens/
    │   ├── home_screen.py    # الشاشة الرئيسية
    │   ├── food_screen.py    # شاشة تحليل الطعام
    │   ├── chat_screen.py    # شاشة المحادثة
    │   └── meds_screen.py    # شاشة الأدوية
    ├── widgets/
    │   ├── vital_card.py     # بطاقة العلامات الحيوية
    │   └── nav_button.py     # زر التنقل
    └── styles/
        └── theme.py          # السمة والألوان
```

---

## ⚙️ إعداد Arduino

### البروتوكول المستخدم

Arduino يرسل البيانات بالتنسيق التالي:

```
BP:120/80,HR:75,TEMP:36.5
```

حيث:

- `BP`: ضغط الدم (انقباضي/انبساطي)
- `HR`: نبضات القلب
- `TEMP`: درجة الحرارة

### مثال كود Arduino

```cpp
void loop() {
    // Read sensors
    int systolic = readBloodPressureSystolic();
    int diastolic = readBloodPressureDiastolic();
    int heartRate = readHeartRate();
    float temperature = readTemperature();

    // Send data
    Serial.print("BP:");
    Serial.print(systolic);
    Serial.print("/");
    Serial.print(diastolic);
    Serial.print(",HR:");
    Serial.print(heartRate);
    Serial.print(",TEMP:");
    Serial.println(temperature, 1);

    delay(2000);
}
```

---

## 🎨 لقطات الشاشة

### الشاشة الرئيسية

- عرض العلامات الحيوية
- أزرار الوصول السريع
- تذكيرات الأدوية القادمة

### شاشة تحليل الطعام

- عرض الكاميرا المباشر
- نتائج التحليل التفصيلية
- تقييم الملاءمة الصحية

### شاشة القرآن الكريم

- قائمة القراء
- قائمة السور مع البحث
- أزرار التحكم بالتشغيل

---

## 🔧 استكشاف الأخطاء

### الكاميرا لا تعمل

```bash
# تأكد من تفعيل الكاميرا
sudo raspi-config
# Interface Options -> Camera -> Enable
```

### Arduino غير متصل

```bash
# تحقق من البورت
ls /dev/ttyUSB*
# أو
ls /dev/ttyACM*
```

### Gemini API لا يعمل

- تأكد من أن API Key صحيح
- تحقق من الاتصال بالإنترنت

---

## 📄 الترخيص

MIT License - راجع ملف LICENSE للتفاصيل

---

## 👥 المساهمة

نرحب بالمساهمات! يرجى فتح Issue أو Pull Request.

---

## 📞 الدعم

للأسئلة أو المشاكل، يرجى فتح Issue في GitHub.

---

<p align="center">
  صنع بـ ❤️ لخدمة المرضى
</p>
