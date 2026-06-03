"""
AI Robot Operating System - Arduino Communication Module
Handles serial communication with Arduino for vital signs data.
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

import sys
sys.path.append('..')
from config import config


@dataclass
class VitalSigns:
    """Vital signs data structure"""
    systolic: int = 0
    diastolic: int = 0
    heart_rate: int = 0
    temperature: float = 0.0
    spo2: float = 0.0
    timestamp: float = 0.0
    is_valid: bool = False   


class ArduinoComm:
    """Arduino Communication Handler"""
    
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
        """Connect to Arduino"""
        if not SERIAL_AVAILABLE:
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
            return True
        except serial.SerialException:
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        self.stop_reading()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.is_connected = False
    
    def add_callback(self, callback: Callable[[VitalSigns], None]):
        """Add a callback function to be called when new data is received"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[VitalSigns], None]):
        """Remove a callback function"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, vitals: VitalSigns):
        """Notify all registered callbacks"""
        for callback in self._callbacks:
            try:
                callback(vitals)
            except Exception:
                pass

    def send_command(self, command: str) -> bool:
        """Send command to Arduino"""
        if not self.is_connected or not self.serial_conn:
            return False
            
        try:
            full_cmd = f"{command}\n"
            self.serial_conn.write(full_cmd.encode('utf-8'))
            return True
        except Exception:
            return False
    
    def update_vitals(self, data_line: str) -> bool:
        """
        Update existing vitals from Arduino data line.
        Supports both comma-separated (Format A) and individual multi-line block values (Format B).
        """
        try:
            updated = False
            data_line = data_line.strip()
            if not data_line:
                return False
                
            # If the Arduino indicates that the finger is not placed properly, reset vitals to 0
            if "place finger" in data_line.lower():
                with self._lock:
                    self._current_vitals.systolic = 0
                    self._current_vitals.diastolic = 0
                    self._current_vitals.heart_rate = 0
                    self._current_vitals.temperature = 0.0
                    self._current_vitals.spo2 = 0.0
                    self._current_vitals.is_valid = False
                    self._current_vitals.timestamp = time.time()
                return True

            # Split by comma if it's the old Format A, otherwise treat as single line
            parts = data_line.split(',') if ',' in data_line else [data_line]
            
            with self._lock:
                self._current_vitals.timestamp = time.time()
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    
                    # 1. Heart Rate (e.g., "Heart Rate: 51.6 bpm" or "HR:75")
                    if "heart rate" in part.lower() or part.startswith("HR:"):
                        val_str = part.split(":")[1].lower().replace("bpm", "").strip()
                        self._current_vitals.heart_rate = int(float(val_str))
                        self._current_vitals.is_valid = True
                        updated = True
                        
                    # 2. Oxygen Saturation (e.g., "Oxygen Saturation (SpO2): 90.0 %")
                    elif "spo2" in part.lower() or "oxygen" in part.lower():
                        if ":" in part:
                            val_str = part.split(":")[1].replace("%", "").strip()
                        else:
                            val_str = part.replace("%", "").strip()
                        self._current_vitals.spo2 = float(val_str)
                        self._current_vitals.is_valid = True
                        updated = True
                        
                    # 3. Blood Pressure (e.g., "Estimated BP: 108 / 71" or "BP:120/80")
                    elif "bp:" in part.lower() or "blood pressure" in part.lower():
                        val_str = part.split(":")[1].strip()
                        bp_values = val_str.split('/')
                        if len(bp_values) == 2:
                            self._current_vitals.systolic = int(float(bp_values[0].strip()))
                            self._current_vitals.diastolic = int(float(bp_values[1].strip()))
                            self._current_vitals.is_valid = True
                            updated = True
                            
                    # 4. Temperature (e.g., "Body Temp: 34.3 C" or "TEMP:36.5")
                    elif "temp:" in part.lower() or "temperature" in part.lower() or "body temp" in part.lower():
                        val_str = part.split(":")[1].lower().replace("c", "").strip()
                        self._current_vitals.temperature = float(val_str)
                        self._current_vitals.is_valid = True
                        updated = True
            
            return updated
        except (ValueError, IndexError, KeyError):
            return False
    
    def _reading_loop(self):
        """Main reading loop (runs in separate thread)"""
        while self.is_running:
            try:
                if SERIAL_AVAILABLE and self.serial_conn and self.serial_conn.is_open:
                    if self.serial_conn.in_waiting > 0:
                        line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            if self.update_vitals(line):
                                with self._lock:
                                    import copy
                                    vitals_copy = copy.copy(self._current_vitals)
                                self._notify_callbacks(vitals_copy)
                
                time.sleep(0.1)  
            except Exception:
                time.sleep(1)
    
    def _simulate_vitals(self):
        """Simulate vital signs for testing"""
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
        time.sleep(5)
    
    def start_reading(self):
        """Start reading data from Arduino in a background thread"""
        if not self.is_connected:
            if not self.connect():
                self.is_connected = True
        
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._reading_loop, daemon=True)
            self._thread.start()
    
    def stop_reading(self):
        """Stop reading data"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
    
    def get_current_vitals(self) -> VitalSigns:
        """Get the most recent vital signs reading"""
        with self._lock:
            return self._current_vitals
    
    def test(self):
        """Test connection and data parsing"""
        # Test old format (Format A)
        assert self.update_vitals("BP:130/85,HR:78,TEMP:36.8")
        assert self._current_vitals.systolic == 130
        assert self._current_vitals.diastolic == 85
        assert self._current_vitals.heart_rate == 78
        assert self._current_vitals.temperature == 36.8
        
        # Test new multi-line formats (Format B)
        assert self.update_vitals("Heart Rate: 51.6 bpm")
        assert self._current_vitals.heart_rate == 51
        
        assert self.update_vitals("Oxygen Saturation (SpO2): 92.5 %")
        assert self._current_vitals.spo2 == 92.5
        
        assert self.update_vitals("Estimated BP: 109 / 72")
        assert self._current_vitals.systolic == 109
        assert self._current_vitals.diastolic == 72
        
        assert self.update_vitals("Body Temp: 34.5 C")
        assert self._current_vitals.temperature == 34.5
        
        # Test place finger properly message
        assert self.update_vitals("Place finger properly...")
        assert self._current_vitals.heart_rate == 0
        assert self._current_vitals.spo2 == 0.0
        assert self._current_vitals.systolic == 0
        assert self._current_vitals.temperature == 0.0
        assert not self._current_vitals.is_valid
        
        print("All tests passed successfully!")
        return True


arduino = ArduinoComm()


if __name__ == "__main__":
    arduino.test()
