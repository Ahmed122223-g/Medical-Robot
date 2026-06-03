import sys
import time
sys.path.append('d:/1/Ahmed/projects/mariam_pro/AI')
from modules.vital_signs import vital_signs_monitor

vital_signs_monitor.start_monitoring()
for i in range(5):
    vitals = vital_signs_monitor.get_current_vitals()
    print(f"BP: {vitals.systolic}/{vitals.diastolic}, HR: {vitals.heart_rate}, Temp: {vitals.temperature}")
    time.sleep(1.5)
vital_signs_monitor.stop_monitoring()
