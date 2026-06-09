import os
import time
import tempfile
import platform
import subprocess
import asyncio
from pathlib import Path

# Load env variables (if needed)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
env_path = os.path.join(PROJECT_ROOT, ".env")
try:
    from dotenv import load_dotenv
    load_dotenv(env_path)
except ImportError:
    pass

def play_audio(filepath: str):
    print(f"  [Audio] Attempting to play {filepath} ...")
    system = platform.system()
    
    if system == 'Linux':
        import shutil
        try:
            if shutil.which("ffplay"):
                subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath], check=True)
                return
            elif shutil.which("mpg123"):
                subprocess.run(["mpg123", "-q", filepath], check=True)
                return
            elif filepath.endswith(".wav") and shutil.which("aplay"):
                subprocess.run(["aplay", "-q", filepath], check=True)
                return
        except Exception as e:
            print(f"  [Audio] Linux player failed: {e}")

    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy(): 
            time.sleep(0.1)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"  [Audio] Pygame playback error: {e}")


def synthesize_speech_edge(text: str):
    print("  [TTS] Generating audio using edge_tts...")
    try:
        import edge_tts
        temp_file = os.path.join(tempfile.gettempdir(), f"response_{int(time.time())}.mp3")
        
        async def _generate():
            communicate = edge_tts.Communicate(text, "ar-EG-SalmaNeural")
            await communicate.save(temp_file)
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate())
        loop.close()
        
        return temp_file
    except Exception as e:
        print(f"  [TTS] edge_tts error: {e}")
        return None

def synthesize_speech_espeak(text: str):
    print("  [TTS] Generating audio using espeak...")
    system = platform.system()
    if system == 'Linux':
        subprocess.run(["espeak", "-v", "ar", text], capture_output=True, text=True)
        return True
    return False

def test_pipeline():
    print("="*60)
    print("  MIC -> AI -> SPEAKER PIPELINE TEST")
    print("="*60)
    
    import speech_recognition as sr
    import google.generativeai as genai
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY is missing from .env!")
        return

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    recognizer = sr.Recognizer()
    
    mic_kwargs = {
        'device_index': 1,      # Explicitly set to 1 for the USB sound card
        'sample_rate': 44100,   # Prevents [Errno -9997] Invalid sample rate
        'chunk_size': 4096      
    }
    
    print("\n[1] Preparing microphone... (Device=1, Rate=44100)")
    try:
        with sr.Microphone(**mic_kwargs) as source:
            print("  ⏳ Adjusting for ambient noise... Please wait...")
            recognizer.adjust_for_ambient_noise(source, duration=1.5)
            
            print("\n  🎤 SPEAK NOW! (Say 'مرحبا')")
            print("  [Recording...] (Will stop when you stop speaking)")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print("  ✅ Audio captured successfully!")
    except Exception as e:
        print(f"  ❌ Microphone error: {e}")
        return

    print("\n[2] Transcribing with Gemini AI...")
    try:
        wav_data = audio.get_wav_data()
        temp_wav = os.path.join(tempfile.gettempdir(), f"input_{int(time.time())}.wav")
        with open(temp_wav, "wb") as f:
            f.write(wav_data)
        
        audio_file = genai.upload_file(temp_wav)
        response = model.generate_content([
            "استخرج النص من هذا المقطع الصوتي واكتبه كما هو باللغة العربية بالضبط، بدون أي مقدمات.",
            audio_file
        ])
        recognized_text = response.text.strip()
        print(f"  ✅ Recognized: \"{recognized_text}\"")
        
        try: genai.delete_file(audio_file.name)
        except: pass
        try: os.unlink(temp_wav)
        except: pass
        
    except Exception as e:
        print(f"  ❌ Transcription error: {e}")
        return

    if not recognized_text:
        print("  ⚠️ No text recognized. Pipeline stopped.")
        return

    print("\n[3] Generating AI Response Audio...")
    reply_text = f"أهلاً بك، لقد سمعتُك تقول: {recognized_text}"
    print(f"  🤖 AI says: {reply_text}")
    
    audio_path = synthesize_speech_edge(reply_text)
    
    if audio_path and os.path.exists(audio_path):
        print("\n[4] Playing Response Audio...")
        play_audio(audio_path)
        try: os.unlink(audio_path)
        except: pass
    else:
        print("  ⚠️ edge_tts failed, falling back to espeak...")
        synthesize_speech_espeak(reply_text)

    print("\n" + "="*60)
    print("  PIPELINE TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    test_pipeline()
