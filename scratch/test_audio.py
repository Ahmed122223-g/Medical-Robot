"""Test script to verify VoiceAssistant output (speakers) and input (microphone)."""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Force voice enabled in config for this test
from config import config
config.VOICE_ENABLED = True

from modules.voice_assistant import voice_assistant

def run_test():
    print("=" * 50)
    print("STARTING AUDIO HARDWARE TEST")
    print("=" * 50)
    
    # 1. Test Speaker
    print("\n[1/2] Testing SPEAKERS...")
    test_phrase = "مرحباً بكم. هذا اختبار لتشغيل السماعات والمايكروفون."
    print(f"Speaking: '{test_phrase}'")
    try:
        voice_assistant.speak(test_phrase, wait=True)
        print("Speaker test completed successfully!")
    except Exception as e:
        print(f"Error during speaker test: {e}")
        
    # 2. Test Microphone
    print("\n[2/2] Testing MICROPHONE...")
    print("Please say something clearly into the microphone now (you have 5 seconds)...")
    try:
        # Enable listening for the assistant
        voice_assistant.listening_enabled = True
        heard_text = voice_assistant.listen_once()
        if heard_text:
            print(f"\n✅ Success! Microphone captured and recognized: \"{heard_text}\"")
        else:
            print("\n❌ Could not recognize any speech. Details to check:")
            print("- Ensure the USB Sound Card is set as the Default Input Device in your system settings.")
            print("- Speak closely and clearly into the mic.")
    except Exception as e:
        print(f"Error during microphone test: {e}")
        
    print("\n" + "=" * 50)
    print("TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    run_test()
