# 🤖 دليل تثبيت نظام الروبوت الطبي على Raspberry Pi

هذا الدليل يشرح بالتفصيل كيفية تحويل مشروعك من بيئة التطوير (Windows) إلى بيئة الإنتاج والروبوت الحقيقي (Raspberry Pi).

---

## 🛠️ أولاً: أفضل العتاد (Hardware Recommendations)
لضمان عمل الروبوت "بسلاسة" دون تقطيع (Lag) في معالجة الكاميرا أو الذكاء الاصطناعي، أنصحك بهذه المواصفات:

### 1. العقل المدبر (Raspberry Pi)
*   **الخيار الأفضل:** **Raspberry Pi 4 Model B (8GB RAM)**.
    *   لماذا؟ الـ 8GB مهمة جداً لتشغيل نماذج الذكاء الاصطناعي ومعالجة الفيديو (OpenCV) وواجهة المستخدم في نفس الوقت.
    *   *ملاحظة:* Raspberry Pi 5 أسرع ولكن الـ Pi 4 أكثر استقراراً حالياً مع المكتبات القديمة وأقل حرارة.
*   **التبريد:** **مروحة تبريد (Ice Tower Cooling Fan)** أو صندوق ألومنيوم مشتت للحرارة (Passive Cooling Case). الحرارة هي العدو الأول للسرعة؛ إذا سخن المعالج، سيصبح الروبوت بطيئاً جداً.
*   **التخزين:** **A2 Class microSD Card** (SanDisk Extreme Pro) بمساحة 64GB على الأقل.
    *   *نصيحة احترافية:* استخدم **SSD** خارجي بدلاً من الكارت ميموري لتسريع النظام 10 أضعاف.

### 2. الشاشة (Touch Screen)
*   **الخيار الرسمي:** **Official Raspberry Pi 7" Touchscreen**.
    *   **الميزة:** تتصل عبر منفذ **DSI** (شريط) وليس HDMI، مما يوفر منافذ HDMI ويجعل اللمس يعمل فوراً بدون تعريفات معقدة. كما أنها تأخذ الطاقة من الراسبري مباشرة.

### 3. الصوت (Audio)
*   **الخيار الأسهل والأفضل:** **USB Conference Speakerphone** (مثل Anker PowerConf أو Jabra Speak أو أنواع أرخص صينية).
    *   **الميزة:** يدمج **الميكروفون + السماعة** في جهاز واحد. يحتوي على **عازل صدى (Echo Cancellation)** مدمج، مما يمنع الروبوت من سماع نفسه (مشكلة شائعة جداً).
*   **الخيار البديل (مدمج):** **ReSpeaker 2-Mics Pi HAT**. يركب فوق الراسبري باي، لكن إعداده البرمجي أصعب قليلاً.

### 4. الكاميرا (Vision)
*   **Raspberry Pi Camera Module 3**. تتصل بشريط CSI. جودتها عالية والتركيز التلقائي (Auto-focus) ممتاز لقراءة الأدوية.

### 5. الطاقة (Power) - ⚠️ أخطر جزء
*   لا تعتمد على شاحن موبايل. استخدم **Raspberry Pi Official Power Supply**.
*   للمحركات والاردوينو: استخدم **بطاريات الليثيوم (Li-ion 18650)** مع دائرة تنظيم جهد (Buck Converter) لتعطيك 5V نظيفة. **لا تسحب طاقة المحركات من الراسبري باي أبداً** وإلا سيحترق أو يعيد التشغيل.

---

## ⚙️ ثانياً: إعداد نظام التشغيل (OS Setup)

1.  حمل برنامج **Raspberry Pi Imager** على الكمبيوتر.
2.  اختر النظام: **Raspberry Pi OS (64-bit)**. النسخة الـ 64-bit ضرورية لمكتبات الذكاء الاصطناعي الحديثة.
3.  بعد حرق النظام وتشغيل الراسبري، افتح التيرمينال ونفذ الأمر:
    ```bash
    sudo raspi-config
    ```
4.  قم بتفعيل التالي من قائمة `Interface Options`:
    *   **SSH**: للتحكم عن بعد.
    *   **VNC**: لرؤية الشاشة عن بعد.
    *   **I2C**: للشاشة أو الحساسات.
    *   **Serial Port**: لكي يعمل الاتصال مع الأردوينو. (اختر No للـ login shell، و Yes للـ hardware enable).
    *   **Legacy Camera** (إذا كنت تستخدم كاميرا Pi القديمة): قم بتفعيلها.
5.  **هام جداً للشاشة:** إذا كنت تستخدم واجهة رسومية ثقيلة، يفضل إلغاء Wayland والعودة لـ X11 إذا واجهت مشاكل (في النسخ الحديثة جداً)، لكن جرب الافتراضي أولاً.

---

## 📦 ثالثاً: تثبيت البيئة والمكتبات

افتح التيرمينال على الراسبري باي ونفذ الأوامر التالية بالترتيب:

### 1. تحديث النظام وتثبيت مكتبات النظام الضرورية
هذه المكتبات ضرورية لعمل PyAudio و OpenCV والصوت:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip python3-tk
sudo apt install -y libatlas-base-dev portaudio19-dev libespeak-dev ffmpeg
sudo apt install -y libhdf5-dev libhdf5-serial-dev libopenjp2-7
sudo apt install -y libcamera-apps  # للكاميرا الجديدة
```

### 2. ⚠️ هام جداً: تثبيت محرك الصوت Offline (espeak)
النظام يستخدم `espeak` للنطق بدون إنترنت. هذا ضروري جداً:
```bash
sudo apt install -y espeak espeak-ng
```

**لدعم اللغة العربية في الصوت (اختياري لكن مُحسِّن للتجربة):**
```bash
sudo apt install -y mbrola mbrola-ar1 mbrola-ar2
```

### 3. إعداد صلاحيات المستخدم
لكي يستطيع البرنامج التحدث مع الأردوينو والكاميرا بدون `sudo`:
```bash
sudo usermod -a -G dialout $USER
sudo usermod -a -G video $USER
```
*(يجب إعادة تشغيل الجهاز بعد هذا الأمر: `sudo reboot`)*.

### 4. نقل المشروع وإنشاء البيئة الوهمية
انقل مجلد المشروع (AI) إلى الراسبري باي (يمكنك استخدام فلاشة أو SFTP). لنفترض أن المسار هو `/home/pi/AI`.

```bash
cd /home/pi/AI
python3 -m venv venv
source venv/bin/activate
```

### 5. تثبيت مكتبات البايثون
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**⚠️ ملاحظات هامة:**
*   تثبيت `opencv-python` و `numpy` على الراسبري يأخذ وقتاً طويلاً (قد يصل لـ 20 دقيقة)، انتظر حتى ينتهي.
*   إذا فشل تثبيت `PyAudio`، جرب:
    ```bash
    sudo apt install python3-pyaudio
    ```
*   إذا فشل تثبيت `opencv-python`، جرب النسخة المخففة:
    ```bash
    pip install opencv-python-headless
    ```

---

## 🔌 رابعاً: التوصيل والربط (Integration)

لكي يعمل كل شيء كـ "كيان واحد":

### الشاشة
ركب كابل الـ DSI (الشريط العريض) في منفذ الشاشة بالراسبري. ثبت الشاشة بمسامير في ظهر المجسم.

### الكاميرا
ركب شريط الكاميرا في منفذ CSI (بجوار منفذ الشاشة). تأكد أن الجزء الأزرق من الشريط يواجه مدخل الإيثرنت (في Pi 4).

**اختبار الكاميرا:**
```bash
libcamera-hello  # للكاميرا الجديدة (Module 3)
# أو
raspistill -o test.jpg  # للكاميرا القديمة
```

### USB
قم بتوصيل:
*   الأردوينو (سيظهر كـ `/dev/ttyUSB0` أو `/dev/ttyACM0`).
*   المايك/السماعة USB.

**للتحقق من منفذ الأردوينو:**
```bash
ls /dev/tty*
# أو
dmesg | grep tty
```

### المحركات
أوصلها بـ Driver (مثل L298N) والـ Driver بالأردوينو. **تذكر:** البطاريات تغذي الـ Driver، والأردوينو يأخذ أوامر من الراسبري (USB) ويعطي إشارة للـ Driver.

---

## 🎤 خامساً: إعداد الصوت (Audio Setup)

### اختبار السماعة
```bash
speaker-test -t wav -c 2
```

### اختبار الميكروفون
```bash
arecord -d 5 test.wav && aplay test.wav
```

### تعيين جهاز الصوت الافتراضي (USB Audio)
إذا كان لديك أكثر من جهاز صوت:
```bash
# عرض الأجهزة المتاحة
aplay -l
arecord -l

# تعديل الإعدادات
sudo nano /etc/asound.conf
```

أضف التالي (غير الأرقام حسب جهازك):
```
defaults.pcm.card 1
defaults.ctl.card 1
```

### اختبار espeak (محرك الصوت Offline)
```bash
espeak "مرحبا بك"
# أو بالعربية
espeak -v ar "مرحبا بك في الروبوت الطبي"
```

---

## ▶️ سادساً: التشغيل التلقائي (Auto-Run)

لجعل الروبوت يعمل فور تشغيل الكهرباء:

1.  أنشئ ملف تشغيل:
    ```bash
    nano /home/pi/run_robot.sh
    ```
2.  اكتب فيه:
    ```bash
    #!/bin/bash
    cd /home/pi/AI
    source venv/bin/activate
    export DISPLAY=:0
    python main.py
    ```
3.  احفظ (`Ctrl+X` ثم `Y`). اجعله قابلاً للتنفيذ:
    ```bash
    chmod +x /home/pi/run_robot.sh
    ```
4.  أضفه لقائمة بدء التشغيل (Autostart):
    ```bash
    mkdir -p ~/.config/autostart
    nano ~/.config/autostart/robot.desktop
    ```
5.  اكتب فيه:
    ```ini
    [Desktop Entry]
    Type=Application
    Name=MedicalRobot
    Exec=/home/pi/run_robot.sh
    ```

---

## 🔧 سابعاً: حل المشاكل الشائعة (Troubleshooting)

### مشكلة: الكاميرا لا تعمل
```bash
# تفعيل الكاميرا
sudo raspi-config  # Interface Options > Camera > Enable

# للكاميرا الجديدة (Module 3)، تأكد من عدم تفعيل Legacy Camera
```

### مشكلة: الأردوينو لا يتصل
```bash
# تحقق من المنفذ
ls /dev/ttyUSB* /dev/ttyACM*

# أضف نفسك لمجموعة dialout
sudo usermod -a -G dialout $USER
sudo reboot
```

### مشكلة: الصوت لا يعمل
```bash
# تحقق من الأجهزة
aplay -l

# اختبر السماعة
speaker-test -t wav

# تأكد من عدم كتم الصوت
alsamixer
```

### مشكلة: الشاشة سوداء أو لا تعمل باللمس
```bash
# تحقق من كابل DSI
# أعد التشغيل
sudo reboot

# إذا استمرت المشكلة، أضف للـ config.txt
sudo nano /boot/config.txt
# أضف:
dtoverlay=vc4-kms-v3d
```

### مشكلة: البرنامج بطيء جداً
```bash
# راقب استهلاك الموارد
htop

# قلل دقة الشاشة
sudo raspi-config  # Display Options > Resolution

# تأكد من التبريد الجيد
vcgencmd measure_temp  # يجب أن تكون أقل من 70°C
```

---

## 💡 نصائح ذهبية لـ "السلاسة"

1.  **تثبيت منفذ الأردوينو:** في ملف `config.py`، تأكدنا بالفعل من الكود:
    ```python
    if platform.system() == 'Linux':
        DEFAULT_PORT = '/dev/ttyUSB0'
    ```
    إذا تغير المنفذ، يمكنك تثبيته باستخدام قواعد `udev`.

2.  **تسريع الواجهة:** قلل دقة الشاشة قليلاً من إعدادات الراسبري باي إذا شعرت ببطء.

3.  **جودة الصوت:** اجعل الـ USB Audio هو الافتراضي.

4.  **سلسلة الـ TTS Fallback:** النظام يحاول بالترتيب:
    *   ElevenLabs (جودة عالية، يحتاج إنترنت ورصيد)
    *   Edge TTS (مجاني، صوت عربي مصري ممتاز) ✅ **الأفضل!**
    *   espeak (Offline، مدمج في Linux)

5.  **الاتصال بالإنترنت:** للحصول على أفضل تجربة صوتية، وصل الراسبري بالإنترنت عبر WiFi أو Ethernet.

---

## 🌐 ثامناً: تثبيت المتصفح (Browser Setup)

الروبوت يحتاج متصفح لفتح صفحة البوابة الطبية عند طلب المريض.

### الخيار 1: Chromium (موجود افتراضياً)
Chromium موجود عادةً في Raspberry Pi OS:
```bash
# للتحقق
which chromium-browser

# إذا غير موجود
sudo apt install -y chromium-browser
```

### الخيار 2: Firefox (أخف على الموارد)
```bash
sudo apt install -y firefox-esr
```

### الخيار 3: Brave Browser (أمان وخصوصية)
```bash
# تثبيت المفاتيح
sudo apt install -y curl
sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg

# إضافة المستودع
echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=arm64] https://brave-browser-apt-release.s3.brave.com/ stable main" | sudo tee /etc/apt/sources.list.d/brave-browser-release.list

# التثبيت
sudo apt update
sudo apt install -y brave-browser
```

### اختبار المتصفح
```bash
# فتح صفحة البوابة الطبية
chromium-browser https://medical-robot.netlify.app/ &
# أو
firefox https://medical-robot.netlify.app/ &
```

### تعيين متصفح افتراضي
```bash
sudo update-alternatives --config x-www-browser
```

**ملاحظة:** يمكن للمريض قول "افتح الرابط" أو "افتح الموقع" والروبوت سيفتح صفحة القياسات في المتصفح تلقائياً.

---

## ✅ قائمة التحقق النهائية (Checklist)

قبل تشغيل الروبوت، تأكد من:

- [ ] Raspberry Pi 4 (8GB) مع تبريد جيد
- [ ] نظام Raspberry Pi OS 64-bit محدث
- [ ] تم تفعيل Serial و I2C و Camera من raspi-config
- [ ] تم تثبيت جميع مكتبات النظام (espeak, portaudio, etc.)
- [ ] تم إنشاء البيئة الوهمية وتثبيت requirements.txt
- [ ] تم إضافة المستخدم لمجموعات dialout و video
- [ ] الشاشة متصلة وتعمل باللمس
- [ ] الكاميرا متصلة ومختبرة
- [ ] الصوت (مايك + سماعة) يعمل
- [ ] الأردوينو متصل ويظهر في /dev/ttyUSB0
- [ ] تم اختبار espeak: `espeak "test"`
- [ ] **متصفح (Chromium/Firefox) مثبت ويعمل**
- [ ] تم إعداد التشغيل التلقائي

---

## 🎤 الأوامر الصوتية للروبوت

### أوامر التنقل
| الأمر | الفعل |
|-------|-------|
| "القياسات" أو "بوابة المريض" | فتح شاشة القياسات |
| "حلل الطعام" أو "صور" | فتح تحليل الطعام |
| "شغل القرآن" | فتح شاشة القرآن |
| "تحدث معي" | فتح المحادثة |
| "الصفحة الرئيسية" | العودة للشاشة الرئيسية |

### أوامر بوابة المريض
| الأمر | الفعل |
|-------|-------|
| "السكر 120" | تسجيل قياس السكر |
| "تحديث" أو "ولد الكود" | توليد QR جديد |
| "افتح الرابط" | فتح صفحة الويب في المتصفح |

بهذا الشكل، يتحول المشروع من مجرد كود على لابتوب إلى منتج متكامل يعمل بمجرد توصيل الكهرباء! 🚀🤖

---

## 📄 التراخيص والخصوصية (License & Privacy)

هذا المشروع مفتوح المصدر ومتاح للجميع للاستخدام والتطوير.

### 1. ترخيص البرمجيات (Software License)
المشروع يخضع لترخيص **MIT License**. يمكنك استخدامه، تعديله، وتوزيعه حتى في المشاريع التجارية، بشرط الإشارة للمؤلف الأصلي.

### 2. العلامات التجارية (Trademarks)
- جميع أسماء المنتجات (مثل Raspberry Pi, Arduino, Gemini) هي علامات تجارية مملوكة لأصحابها.
- استخدام هذه الأسماء هنا هو لغرض الشرح والتوافق التقني فقط.

### 3. إخلاء مسؤولية (Disclaimer)
هذا المشروع هو **نموذج أولي طبي (Medical Prototype)** وليس جهازاً طبياً معتمداً. يجب استشارة الأطباء المختصين قبل الاعتماد على أي من نتائجه في القرارات الطبية الحقيقية.

---

<p align="center">
  🌐 عرض الدليل على <a href="https://github.com/Ahmed122223-g/Medical-Robot/blob/main/raspberry_pi_guide.md">GitHub</a>
</p>
