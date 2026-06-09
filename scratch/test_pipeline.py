#!/usr/bin/env python3
"""
Standalone Mic -> Groq Whisper -> Groq LLaMA -> Speaker test.
Uses arecord directly (proven to work on this Pi) to bypass PortAudio/PulseAudio issues.
"""
import os
import sys
import time
import tempfile
import platform
import subprocess
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    pass

from groq import Groq

# ─── Audio playback ───────────────────────────────────────────────
def play_audio(filepath: str):
    import shutil
    if shutil.which("ffplay"):
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath])
    elif shutil.which("mpg123"):
        subprocess.run(["mpg123", "-q", filepath])
    elif filepath.endswith(".wav") and shutil.which("aplay"):
        subprocess.run(["aplay", "-q", filepath])
    else:
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
            print(f"  [Audio] Playback error: {e}")

# ─── TTS ──────────────────────────────────────────────────────────
def synthesize_speech(text: str):
    try:
        import edge_tts
        temp_file = os.path.join(tempfile.gettempdir(), f"response_{int(time.time())}.mp3")
        async def _gen():
            comm = edge_tts.Communicate(text, "ar-EG-SalmaNeural")
            await comm.save(temp_file)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_gen())
        loop.close()
        return temp_file
    except Exception as e:
        print(f"  [TTS] edge_tts error: {e}, trying espeak...")
        subprocess.run(["espeak", "-v", "ar", text], capture_output=True)
        return None

# ─── Record with arecord (PROVEN TO WORK) ────────────────────────
def record_audio(duration=6):
    """Record using arecord directly via ALSA - bypasses PulseAudio completely."""
    tmp_path = os.path.join(tempfile.gettempdir(), f"mic_{int(time.time())}.wav")
    
    cmd = [
        "arecord",
        "-D", "plughw:1,0",   # USB sound card directly
        "-f", "S16_LE",       # 16-bit signed little-endian
        "-r", "16000",        # 16kHz (good for speech, Whisper prefers this)
        "-c", "1",            # Mono
        "-d", str(duration),  # Duration in seconds
        "-q",                 # Quiet (no verbose output)
        tmp_path
    ]
    
    print(f"  ⏳ Recording {duration} seconds... SPEAK NOW!")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
    
    if result.returncode != 0:
        print(f"  ❌ arecord failed: {result.stderr}")
        return None
    
    file_size = os.path.getsize(tmp_path)
    print(f"  ✅ Recorded! File size: {file_size} bytes")
    return tmp_path

# ─── Main pipeline ───────────────────────────────────────────────
def test_pipeline():
    print("=" * 60)
    print("  MIC -> GROQ WHISPER -> GROQ LLAMA -> SPEAKER")
    print("=" * 60)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in .env!")
        return
    client = Groq(api_key=api_key)

    # ── Step 1: Record ──
    print("\n[1] 🎤 Recording from USB mic (plughw:1,0)...")
    wav_path = record_audio(duration=6)
    if not wav_path:
        return

    # ── Step 2: Transcribe with Groq Whisper ──
    print("\n[2] 📝 Transcribing with Groq Whisper...")
    try:
        with open(wav_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(wav_path, f.read()),
                model="whisper-large-v3",
                language="ar"
            )
        text = transcription.text.strip()
        print(f"  ✅ You said: \"{text}\"")
    except Exception as e:
        print(f"  ❌ Transcription error: {e}")
        return
    finally:
        try: os.unlink(wav_path)
        except: pass

    if not text:
        print("  ⚠️ No speech detected.")
        return

    # ── Step 3: Generate AI reply with LLaMA ──
    print("\n[3] 🤖 Generating reply with LLaMA...")
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "أنت مساعد طبي ذكي. قم بالرد بترحيب قصير ومختصر باللغة العربية الفصحى."},
                {"role": "user", "content": text},
            ],
            model="llama-3.3-70b-versatile",
        )
        reply = completion.choices[0].message.content.strip()
        print(f"  🤖 AI says: {reply}")
    except Exception as e:
        print(f"  ❌ LLaMA error: {e}")
        return

    # ── Step 4: Speak the reply ──
    print("\n[4] 🔊 Speaking response...")
    audio_path = synthesize_speech(reply)
    if audio_path and os.path.exists(audio_path):
        play_audio(audio_path)
        try: os.unlink(audio_path)
        except: pass
    else:
        print("  ⚠️ TTS fallback used (espeak).")

    print("\n" + "=" * 60)
    print("  ✅ PIPELINE TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
