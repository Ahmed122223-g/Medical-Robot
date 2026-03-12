"""
AI Robot Operating System - Arduino Communication Module
نظام تشغيل الروبوت الطبي الذكي - وحدة الاتصال بالأردوينو

This module handles serial communication with Arduino
to receive vital signs data (blood pressure, heart rate, temperature)
هذه الوحدة تتعامل مع الاتصال التسلسلي مع الأردوينو
لاستقبال بيانات العلامات الحيوية (ضغط الدم، نبضات القلب، درجة الحرارة)
"""

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("⚠️ PySerial not installed. Arduino communication will be simulated.")

import sys
sys.path.append('..')
from config import config


@dataclass
class VitalSigns:
    """Vital signs data structure - هيكل بيانات العلامات الحيوية"""
    systolic: int = 120      # ضغط انقباضي
    diastolic: int = 80      # ضغط انبساطي
    heart_rate: int = 75     # نبضات القلب
    temperature: float = 36.5  # درجة الحرارة
    timestamp: float = 0.0   # وقت القراءة
    is_valid: bool = True    # هل البيانات صحيحة


class ArduinoComm:
    """
    Arduino Communication Handler
    معالج الاتصال بالأردوينو
    
    Expected Arduino data format:
    BP:120/80,HR:75,TEMP:36.5
    """
    
    def __init__(self):
        self.port = config.ARDUINO_PORT
        self.baud_rate = config.ARDUINO_BAUD_RATE
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: list[Callable[[VitalSigns], None]] = []
        self._current_vitals = VitalSigns()
        self._lock = threading.Lock()
        
    def connect(self) -> bool:
        """
        Connect to Arduino
        الاتصال بالأردوينو
        """
        if not SERIAL_AVAILABLE:
            print("🔄 Running in simulation mode (PySerial not available)")
            self.is_connected = True
            return True
            
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1
            )
            time.sleep(2) 
            self.is_connected = True
            print(f"✅ Connected to Arduino on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"❌ Failed to connect to Arduino: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """
        Disconnect from Arduino
        قطع الاتصال بالأردوينو
        """
        self.stop_reading()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False
        print("🔌 Disconnected from Arduino")
    
    def add_callback(self, callback: Callable[[VitalSigns], None]):
        """
        Add a callback function to be called when new data is received
        إضافة دالة استدعاء عند استقبال بيانات جديدة
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[VitalSigns], None]):
        """Remove a callback function - إزالة دالة الاستدعاء"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    def _notify_callbacks(self, vitals: VitalSigns):
        """Notify all registered callbacks - إعلام جميع دوال الاستدعاء"""
        for callback in self._callbacks:
            try:
                callback(vitals)
            except Exception as e:
                print(f"❌ Callback error: {e}")

    def send_command(self, command: str) -> bool:
        """
        Send command to Arduino (e.g., motor control)
        إرسال أمر إلى الأردوينو (مثل التحكم في المحركات)
        """
        if not self.is_connected or not self.serial_conn:
            if config.DEBUG_MODE:
                print(f"⚠️ Cannot send command '{command}': Not connected")
            return False
            
        try:
            full_cmd = f"{command}\n"
            self.serial_conn.write(full_cmd.encode('utf-8'))
            if config.DEBUG_MODE:
                print(f"📤 Sent to Arduino: {command}")
            return True
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
            return False
    
    def parse_data(self, data_line: str) -> Optional[VitalSigns]:
        """
        Parse Arduino data line
        تحليل سطر بيانات الأردوينو
        
        Format: BP:120/80,HR:75,TEMP:36.5
        """
        try:
            vitals = VitalSigns(timestamp=time.time())
            parts = data_line.strip().split(',')
            
            for part in parts:
                if part.startswith('BP:'):
                    bp_values = part[3:].split('/')
                    vitals.systolic = int(bp_values[0])
                    vitals.diastolic = int(bp_values[1])
                elif part.startswith('HR:'):
                    vitals.heart_rate = int(part[3:])
                elif part.startswith('TEMP:'):
                    vitals.temperature = float(part[5:])
            
            return vitals
        except (ValueError, IndexError) as e:
            if config.DEBUG_MODE:
                print(f"⚠️ Parse error: {e} - Data: {data_line}")
            return None
    
    def _reading_loop(self):
        """
        Main reading loop (runs in separate thread)
        حلقة القراءة الرئيسية (تعمل في خيط منفصل)
        """
        while self.is_running:
            try:
                if SERIAL_AVAILABLE and self.serial_conn and self.serial_conn.is_open:
                    if self.serial_conn.in_waiting > 0:
                        line = self.serial_conn.readline().decode('utf-8').strip()
                        if line:
                            vitals = self.parse_data(line)
                            if vitals:
                                with self._lock:
                                    self._current_vitals = vitals
                                self._notify_callbacks(vitals)
                else:
                    self._simulate_vitals()
                
                time.sleep(0.1)  
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"❌ Reading error: {e}")
                time.sleep(1)
    
    def _simulate_vitals(self):
        """
        Simulate vital signs for testing (when Arduino is not connected)
        محاكاة العلامات الحيوية للاختبار
        """
        import random
        
        vitals = VitalSigns(
            systolic=random.randint(115, 145),
            diastolic=random.randint(75, 95),
            heart_rate=random.randint(65, 95),
            temperature=round(36.0 + random.random() * 1.5, 1),
            timestamp=time.time(),
            is_valid=True
        )
        
        with self._lock:
            self._current_vitals = vitals
        self._notify_callbacks(vitals)
        time.sleep(2)  
    
    def start_reading(self):
        """
        Start reading data from Arduino in a background thread
        بدء قراءة البيانات من الأردوينو في خيط منفصل
        """
        if not self.is_connected:
            if not self.connect():
                print("⚠️ Starting in simulation mode")
                self.is_connected = True
        
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._reading_loop, daemon=True)
            self._thread.start()
            print("📊 Started reading vital signs")
    
    def stop_reading(self):
        """
        Stop reading data
        إيقاف قراءة البيانات
        """
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        print("⏹️ Stopped reading vital signs")
    
    def get_current_vitals(self) -> VitalSigns:
        """
        Get the most recent vital signs reading
        الحصول على أحدث قراءة للعلامات الحيوية
        """
        with self._lock:
            return self._current_vitals
    
    def test(self):
        """
        Test connection and data parsing
        اختبار الاتصال وتحليل البيانات
        """
        print("🧪 Testing Arduino communication...")
        
        test_data = "BP:130/85,HR:78,TEMP:36.8"
        vitals = self.parse_data(test_data)
        if vitals:
            print(f"✅ Parse test passed:")
            print(f"   Blood Pressure: {vitals.systolic}/{vitals.diastolic} mmHg")
            print(f"   Heart Rate: {vitals.heart_rate} bpm")
            print(f"   Temperature: {vitals.temperature}°C")
        else:
            print("❌ Parse test failed")
        
        if self.connect():
            print("✅ Connection test passed")
            self.disconnect()
        else:
            print("⚠️ Connection test: Running in simulation mode")
        
        print("🧪 Test completed")


arduino = ArduinoComm()


if __name__ == "__main__":
    arduino.test()
