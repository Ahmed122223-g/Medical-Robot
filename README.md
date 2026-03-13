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

## 🛠️ دليل التجهيز (Raspberry Pi 4B)

للحصول على أفضل أداء وتجربة مستخدم، يرجى اتباع الدليل الكامل المخصص للراسبري باي:

👉 **[دليل تثبيت وتشغيل Raspberry Pi 4B](raspberry_pi_guide.md)**

### مقتطف من خطوات التثبيت:

```bash
# 1. تحميل المشروع
git clone https://github.com/Ahmed122223-g/Medical-Robot.git
cd Medical-Robot

# 2. إنشاء البيئة وتثبيت المكتبات
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

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

