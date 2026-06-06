"""Test script to verify speakers and microphone on Raspberry Pi."""
import sys
import os
import wave
import struct
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config import config
config.VOICE_ENABLED = True

def test_speakers():
    """Test speaker output using edge-tts or offline."""
    from modules.voice_assistant import voice_assistant
    print("\n[1/3] Testing SPEAKERS...")
    test_phrase = "مرحباً بكم. هذا اختبار لتشغيل السماعات."
    print(f"  Speaking: '{test_phrase}'")
    try:
        voice_assistant.speak(test_phrase, wait=True)
        print("  ✅ Speaker test completed!")
    except Exception as e:
        print(f"  ❌ Speaker error: {e}")

def test_raw_recording():
    """Test raw microphone recording using PyAudio directly (bypasses SpeechRecognition)."""
    print("\n[2/3] Testing RAW MICROPHONE (PyAudio direct)...")
    try:
        import pyaudio
    except ImportError:
        print("  ❌ PyAudio not installed. Run: pip install pyaudio")
        return False

    p = pyaudio.PyAudio()

    # Find USB mic
    usb_index = None
    print("  Available input devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            marker = ""
            name_lower = info['name'].lower()
            if 'usb' in name_lower:
                usb_index = i
                marker = " <-- USB MIC"
            print(f"    Index {i}: {info['name']} (inputs: {info['maxInputChannels']}){marker}")

    if usb_index is None:
        print("  ❌ No USB microphone found!")
        p.terminate()
        return False

    print(f"\n  Using device index {usb_index} for recording...")
    print("  🎙️ Recording 3 seconds... SPEAK NOW!")

    RATE = 16000
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    CHUNK = 1024
    DURATION = 3

    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, input_device_index=usb_index,
                        frames_per_buffer=CHUNK)

        frames = []
        for _ in range(int(RATE / CHUNK * DURATION)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        # Analyze audio level
        all_data = b''.join(frames)
        samples = struct.unpack(f'<{len(all_data)//2}h', all_data)
        max_amplitude = max(abs(s) for s in samples)
        avg_amplitude = sum(abs(s) for s in samples) / len(samples)

        print(f"\n  Audio Analysis:")
        print(f"    Max amplitude:  {max_amplitude} / 32767")
        print(f"    Avg amplitude:  {avg_amplitude:.0f}")

        # Save WAV file for manual verification
        wav_path = os.path.join(PROJECT_ROOT, "scratch", "test_recording.wav")
        with wave.open(wav_path, 'w') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(all_data)
        print(f"    Saved recording to: {wav_path}")

        if max_amplitude < 100:
            print("\n  ❌ Microphone seems SILENT (max amplitude < 100).")
            print("     Fix: Run 'alsamixer', press F6, select USB device,")
            print("     then press F4 (Capture), press SPACE to enable CAPTURE,")
            print("     and raise volume with UP arrow.")
            p.terminate()
            return False
        elif max_amplitude < 1000:
            print("\n  ⚠️ Microphone volume is VERY LOW. Raise capture volume in alsamixer.")
            p.terminate()
            return True
        else:
            print("\n  ✅ Microphone is capturing audio successfully!")
            p.terminate()
            return True

    except Exception as e:
        print(f"  ❌ Recording error: {e}")
        p.terminate()
        return False

def test_speech_recognition(mic_works):
    """Test Google Speech Recognition with the USB mic."""
    print("\n[3/3] Testing SPEECH RECOGNITION...")
    if not mic_works:
        print("  ⏭️ Skipping (microphone test failed).")
        return

    try:
        import speech_recognition as sr
    except ImportError:
        print("  ❌ SpeechRecognition not installed.")
        return

    # Find USB mic index
    usb_index = None
    try:
        for idx, name in enumerate(sr.Microphone.list_microphone_names()):
            if 'usb' in name.lower():
                usb_index = idx
                break
    except:
        pass

    print(f"  Using mic index: {usb_index}")
    print("  🎙️ Say something clearly now (10 seconds timeout)...")

    try:
        recognizer = sr.Recognizer()
        mic_kwargs = {'device_index': usb_index} if usb_index is not None else {}
        with sr.Microphone(**mic_kwargs) as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("  Listening...")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            print("  Processing with Google...")
            text = recognizer.recognize_google(audio, language="ar-EG")
            print(f"\n  ✅ Recognized: \"{text}\"")
    except sr.WaitTimeoutError:
        print("  ❌ Timeout: No speech detected within 10 seconds.")
    except sr.UnknownValueError:
        print("  ❌ Could not understand the audio (try speaking louder/closer).")
    except sr.RequestError as e:
        print(f"  ❌ Google API error (need internet): {e}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    print("=" * 55)
    print("  AUDIO HARDWARE TEST - Raspberry Pi")
    print("=" * 55)

    test_speakers()
    mic_ok = test_raw_recording()
    test_speech_recognition(mic_ok)

    print("\n" + "=" * 55)
    print("  TEST COMPLETED")
    print("=" * 55)

if __name__ == "__main__":
    main()
