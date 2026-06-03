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
        """Update existing vitals from Arduino data line. Format: BP:120/80,HR:75,TEMP:36.5"""
        try:
            updated = False
            parts = data_line.strip().split(',')
            
            with self._lock:
                self._current_vitals.timestamp = time.time()
                for part in parts:
                    if part.startswith('BP:'):
                        bp_values = part[3:].split('/')
                        if len(bp_values) == 2:
                            self._current_vitals.systolic = int(bp_values[0])
                            self._current_vitals.diastolic = int(bp_values[1])
                            updated = True
                    elif part.startswith('HR:'):
                        self._current_vitals.heart_rate = int(part[3:])
                        updated = True
                    elif part.startswith('TEMP:'):
                        self._current_vitals.temperature = float(part[5:])
                        updated = True
            
            return updated
        except (ValueError, IndexError):
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
        test_data = "BP:130/85,HR:78,TEMP:36.8"
        if self.update_vitals(test_data):
            return True
        return False


arduino = ArduinoComm()


if __name__ == "__main__":
    arduino.test()
