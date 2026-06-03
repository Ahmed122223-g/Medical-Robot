"""
AI Robot OS - Camera Verification Tool
Tests the camera capture wrapper on both PC (OpenCV) and Raspberry Pi (libcamera fallback).
"""
import sys
import time
from pathlib import Path

# Fix Windows console encoding for emojis and special characters
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Add project root to python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("❌ OpenCV (cv2) is not installed! Run: pip install opencv-python")
    sys.exit(1)

# Import the project's native CameraCapture wrapper
try:
    from gui.screens.food_screen import CameraCapture
except ImportError as e:
    print(f"❌ Failed to import project CameraCapture wrapper: {e}")
    sys.exit(1)


def main():
    print("=" * 50)
    print("📸 CAMERA DIAGNOSTIC TOOL")
    print("=" * 50)
    
    camera = CameraCapture()
    
    print("⏳ Attempting to initialize camera...")
    success = camera.open()
    
    if not success:
        print("❌ ERROR: Could not open the camera!")
        print("\nSuggestions for Raspberry Pi:")
        print("  1. Make sure camera is enabled in raspi-config.")
        print("  2. Verify connections of the ribbon cable (blue side faces Ethernet on Pi 4).")
        print("  3. Run 'libcamera-hello' to check system-level access.")
        print("  4. If using legacy camera, run 'vcgencmd get_camera' to verify connection.")
        print("\nSuggestions for Windows Laptop:")
        print("  1. Ensure no other application (e.g. Teams, Zoom, Camera app) is using the webcam.")
        print("  2. Check your antivirus webcam block settings.")
        sys.exit(1)
        
    print("✅ SUCCESS: Camera initialized and opened successfully!")
    print("\n⏳ Capturing 10 test frames (allowing exposure to settle)...")
    
    last_frame = None
    for i in range(1, 11):
        time.sleep(0.15)  # Pause to let sensor adjust
        ret, frame = camera.read()
        if ret and frame is not None:
            last_frame = frame
            h, w = frame.shape[:2]
            print(f"  [Frame {i}/10] Read success! Resolution: {w}x{h}")
        else:
            print(f"  [Frame {i}/10] ⚠️ Read failed or empty frame received.")
            
    # Release camera resource
    camera.release()
    print("🔒 Camera released.")
    
    if last_frame is not None:
        output_name = "test_camera.jpg"
        cv2.imwrite(output_name, last_frame)
        print(f"\n🎉 Test image successfully saved to: {PROJECT_ROOT / output_name}")
        print("👉 Open this image to verify the camera output!")
    else:
        print("\n❌ ERROR: Opened camera but failed to grab any valid frames.")
        sys.exit(1)

    print("=" * 50)


if __name__ == "__main__":
    main()
