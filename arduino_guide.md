# ⚙️ دليل إعداد وبرمجة Arduino

هذا الدليل يشرح كيفية إعداد الأردوينو وتوصيله بنظام الروبوت الطبي، مع توضيح بروتوكول البيانات المستخدم.

---

## 🔌 التوصيل بالراسبري باي
- يتم توصيل الأردوينو عبر منفذ **USB** مباشرة بالراسبري باي.
- تأكد من أن الكابل المستخدم يدعم نقل البيانات (Data Cable).
- سيظهر الأردوينو في النظام غالباً كـ `/dev/ttyUSB0` أو `/dev/ttyACM0`.

---

## 📝 البروتوكول المستخدم (Data Protocol)

يرسل الأردوينو البيانات عبر السيريال (Serial) بالتنسيق التالي لكي يفهمها الروبوت:

```
BP:120/80,HR:75,TEMP:36.5
```

### شرح البارامترات:
- `BP`: ضغط الدم (انقباضي/انبساطي) بوحدة mmHg.
- `HR`: نبضات القلب (Heart Rate) بوحدة bpm.
- `TEMP`: درجة الحرارة بوحدة مئوية (Celsius).

---

## 💻 مثال كود Arduino (Sketch)

يمكنك استخدام هذا الكود كأساس لربط الحساسات الخاصة بك:

```cpp
void setup() {
    Serial.begin(9600); // يجب أن يكون نفس Baud Rate في ملف .env
}

void loop() {
    // هنا يتم قراءة الحساسات الحقيقية
    int systolic = 120; // مثال
    int diastolic = 80;  // مثال
    int heartRate = 75;  // مثال
    float temperature = 36.5; // مثال

    // إرسال البيانات بالتنسيق المطلوب
    Serial.print("BP:");
    Serial.print(systolic);
    Serial.print("/");
    Serial.print(diastolic);
    Serial.print(",HR:");
    Serial.print(heartRate);
    Serial.print(",TEMP:");
    Serial.println(temperature, 1);

    delay(2000); // إرسال تحديث كل ثانيتين
}
```

---

## 📄 التراخيص والخصوصية (License & Privacy)

### 1. ترخيص البرمجيات
المشروع يخضع لترخيص **[MIT License](LICENSE)**.

### 2. العلامات التجارية
- Arduino هي علامة تجارية مسجلة لشركة Arduino SA.
- استخدام الاسم هنا هو لغرض التوافق التقني فقط.

### 3. إخلاء مسؤولية
هذا الكود هو جزء من نموذج أولي طبي. لا يجب استخدامه في التشخيص الطبي الحقيقي دون فحص ومعايرة من جهات طبية معتمدة.

---

<p align="center">
  🌐 عرض الدليل على <a href="https://github.com/Ahmed122223-g/Medical-Robot/blob/main/arduino_guide.md">GitHub</a>
</p>
