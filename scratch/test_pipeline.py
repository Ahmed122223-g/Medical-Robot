#!/usr/bin/env python3
"""
Standalone Mic -> Groq Whisper -> Groq LLaMA -> Speaker test.
Uses sounddevice (proven to work) instead of speech_recognition/PyAudio.
"""
import os
import sys
import time
import wave
import tempfile
import platform
import subprocess
import asyncio
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:
    pass

import sounddevice as sd
from groq import Groq

# ─── Audio playback ───────────────────────────────────────────────
def play_audio(filepath: str):
    system = platform.system()
    if system == 'Linux':
        import shutil
        if shutil.which("ffplay"):
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath])
            return
        elif shutil.which("mpg123"):
            subprocess.run(["mpg123", "-q", filepath])
            return
        elif filepath.endswith(".wav") and shutil.which("aplay"):
            subprocess.run(["aplay", "-q", filepath])
            return
    # Fallback: pygame
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
def synthesize_speech(text: str) -> str:
    """Generate speech audio file using edge_tts, return file path."""
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
        print(f"  [TTS] edge_tts error: {e}")
        # fallback: espeak
        if platform.system() == "Linux":
            subprocess.run(["espeak", "-v", "ar", text], capture_output=True)
        return None

# ─── Record with sounddevice ─────────────────────────────────────
def record_audio(device_id=1, sample_rate=44100, max_seconds=10, silence_thresh=0.01, silence_duration=1.5):
    """
    Record from microphone until silence is detected or max time is reached.
    Returns the path to a temporary WAV file.
    """
    chunk_duration = 0.5  # seconds per chunk
    chunk_samples = int(sample_rate * chunk_duration)
    chunks = []
    silent_chunks = 0
    max_silent = int(silence_duration / chunk_duration)
    max_chunks = int(max_seconds / chunk_duration)

    print(f"  [Recording up to {max_seconds}s, will stop on {silence_duration}s silence]")

    for i in range(max_chunks):
        audio_chunk = sd.rec(chunk_samples, samplerate=sample_rate, channels=1, dtype='int16', device=device_id)
        sd.wait()
        chunks.append(audio_chunk)

        # Check volume level
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2)) / 32768.0
        bar = "█" * int(rms * 200)
        print(f"\r  🎤 Level: [{bar:<20}] {rms:.4f}", end="", flush=True)

        if rms < silence_thresh:
            silent_chunks += 1
        else:
            silent_chunks = 0

        # Stop after enough silence (but only if we got some audio first)
        if silent_chunks >= max_silent and len(chunks) > max_silent + 2:
            break

    print()  # newline after the level meter

    all_audio = np.concatenate(chunks)

    # Save to WAV
    tmp_path = os.path.join(tempfile.gettempdir(), f"mic_{int(time.time())}.wav")
    with wave.open(tmp_path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(all_audio.tobytes())

    duration = len(all_audio) / sample_rate
    print(f"  ✅ Recorded {duration:.1f} seconds -> {tmp_path}")
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

    # ── Step 1: List devices ──
    print("\n[1] Audio devices:")
    print(sd.query_devices())

    # ── Step 2: Record ──
    print("\n[2] 🎤 SPEAK NOW! (Say 'مرحبا' or anything)")
    try:
        wav_path = record_audio(device_id=1, sample_rate=44100)
    except Exception as e:
        print(f"  ❌ Recording failed: {e}")
        return

    # ── Step 3: Transcribe with Groq Whisper ──
    print("\n[3] Transcribing with Groq Whisper...")
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

    # ── Step 4: Generate AI reply with LLaMA ──
    print("\n[4] Generating reply with LLaMA...")
    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "أنت مساعد طبي ذكي. قم بالرد بترحيب قصير ومختصر باللغة العربية الفصحى."},
                {"role": "user", "content": text},
            ],
            model="llama-3.3-70b-versatile",
        )
        reply = completion.choices[0].message.content.strip()
        print(f"  🤖 AI: {reply}")
    except Exception as e:
        print(f"  ❌ LLaMA error: {e}")
        return

    # ── Step 5: Speak the reply ──
    print("\n[5] Speaking response...")
    audio_path = synthesize_speech(reply)
    if audio_path and os.path.exists(audio_path):
        play_audio(audio_path)
        try: os.unlink(audio_path)
        except: pass
    else:
        print("  ⚠️ TTS failed.")

    print("\n" + "=" * 60)
    print("  ✅ PIPELINE TEST COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
