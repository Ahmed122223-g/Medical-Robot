import os
import sys
import threading
import tempfile
import time
import platform
import subprocess
import shutil
from typing import Optional, Callable
from pathlib import Path

sys.path.append('..')
from config import config
from core.translations import translate

try:
    from elevenlabs import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

try:
    import edge_tts
    import asyncio
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import pygame
    # Deferred init to avoid ALSA startup freeze on Raspberry Pi
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False


class VoiceAssistant:
    ARABIC_VOICE_IDS = {"male": "pNInz6obpgDQGcFmaJgB", "female": "EXAVITQu4vr4xnSDxMaL"}
    
    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY
        self.voice_enabled = config.VOICE_ENABLED
        self.listening_enabled = False
        self.is_listening = False
        self.is_speaking = False
        self._speech_cooldown_until = 0  # timestamp until which mic stays muted after speech
        self._speech_cooldown_seconds = 1.5  # seconds to wait after speech ends
        self.current_screen = "home"
        self.on_command_callback: Optional[Callable] = None
        self.on_speech_callback: Optional[Callable] = None
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        if self.recognizer:
            self.recognizer.energy_threshold = 1200  # Good base sensitivity floor
            self.recognizer.dynamic_energy_threshold = False  # Keep threshold stable during recording
            self.recognizer.pause_threshold = 2.0  # Wait for 2.0s of silence before ending speech
        self.microphone = None
        
        # Try to find USB mic index first
        self._mic_device_index = self._find_usb_mic_index()
        # Fallback: on Linux (Raspberry Pi), if no USB mic detected, default to index 1. On Windows/macOS, default to None.
        if self._mic_device_index is None:
            if platform.system() == 'Linux':
                self._mic_device_index = 1
            else:
                self._mic_device_index = None
                
        self.elevenlabs_client = None
        if ELEVENLABS_AVAILABLE and self.api_key:
            try:
                self.elevenlabs_client = ElevenLabs(api_key=self.api_key)
            except:
                pass
        self.voice_id = self.ARABIC_VOICE_IDS["female"]
        self._listen_thread = None
        self._stop_listening = threading.Event()
        self._listen_lock = threading.Lock()
        self.elevenlabs_quota_exceeded = False
        self._current_audio_process = None  # Track subprocess for Linux audio playback
        
        # Speech start/stop time tracking for echo/overlap detection
        self._last_speech_start_time = 0.0
        self._last_speech_stop_time = 0.0

        
        # Initialize Gemini for Speech Recognition
        self.gemini_model = None
        if config.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            except Exception as e:
                print(f"[VoiceAssistant] Error initializing Gemini: {e}")
    
    def _find_usb_mic_index(self):
        """Auto-detect USB microphone device index."""
        if not SR_AVAILABLE:
            return None
        try:
            mic_names = sr.Microphone.list_microphone_names()
            for idx, name in enumerate(mic_names):
                name_lower = name.lower()
                if 'usb' in name_lower and ('audio' in name_lower or 'sound' in name_lower or 'pnp' in name_lower):
                    print(f"[VoiceAssistant] Found USB microphone: '{name}' at index {idx}")
                    return idx
        except Exception as e:
            print(f"[VoiceAssistant] Error detecting USB mic: {e}")
        return None
    
    def _audio_overlaps_speech(self, start_time: float, end_time: float) -> bool:
        """Check if the recorded audio interval overlaps with bot speech or cooldown."""
        mute_start = self._last_speech_start_time
        mute_end = time.time() + 9999.0 if self.is_speaking else (self._last_speech_stop_time + self._speech_cooldown_seconds)
        return (start_time <= mute_end) and (mute_start <= end_time)

    
    def set_voice_permission(self, allowed: bool):
        self.listening_enabled = allowed
        if not allowed:
            self.stop_listening()
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Remove emojis, markdown formatting, and special characters from text before speech."""
        if not text:
            return ""
        
        import re
        
        # 1. Remove markdown formatting characters
        text = re.sub(r'[*_`#~=\-\+\[\]\{\}\(\)\<\>]', ' ', text)
        
        # 2. Filter out non-alphanumeric/non-basic punctuation characters (like emojis)
        cleaned_chars = []
        for char in text:
            code = ord(char)
            # Allow:
            # - Standard ASCII & Latin/European characters (code < 0x0370)
            # - Arabic character blocks (0x0600-0x06FF, 0x0750-0x077F, 0x08A0-0x08FF)
            if (code < 0x0370) or (0x0600 <= code <= 0x06FF) or (0x0750 <= code <= 0x077F) or (0x08A0 <= code <= 0x08FF):
                # Exclude specific symbol/punctuation marks that are not naturally spoken
                if char not in ['*', '_', '`', '#', '~', '=', '-', '+', '[', ']', '{', '}', '<', '>', '/', '\\', '|', '^']:
                    cleaned_chars.append(char)
            else:
                # Replace symbol/emoji with a space
                cleaned_chars.append(' ')
                
        cleaned_text = "".join(cleaned_chars)
        
        # 3. Clean up multiple whitespaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text

    def speak(self, text: str, wait: bool = True):
        if not self.voice_enabled or not text:
            return
        cleaned_text = self._clean_text_for_speech(text)
        if not cleaned_text:
            return
        self.is_speaking = True  # Set BEFORE starting speech
        self._last_speech_start_time = time.time()  # Track speech start time
        def _speak():
            try:
                if self.elevenlabs_client and not self.elevenlabs_quota_exceeded:
                    self._speak_elevenlabs(cleaned_text)
                elif EDGE_TTS_AVAILABLE:
                    self._speak_edge_tts(cleaned_text)
                else:
                    self._speak_offline(cleaned_text)
            except:
                if EDGE_TTS_AVAILABLE:
                    try:
                        self._speak_edge_tts(cleaned_text)
                        return
                    except:
                        pass
                try:
                    self._speak_offline(cleaned_text)
                except:
                    pass
            finally:
                self.is_speaking = False
                self._last_speech_stop_time = time.time()  # Track speech stop time
                # Set cooldown so mic stays muted for a bit after speech ends
                self._speech_cooldown_until = time.time() + self._speech_cooldown_seconds
        if wait: _speak()
        else: threading.Thread(target=_speak, daemon=True).start()
    
    def stop_speaking(self):
        """Immediately stop current speech playback (works on both Linux and Windows)."""
        self.is_speaking = False
        self._last_speech_stop_time = time.time()  # Track speech stop time
        
        # Kill Linux subprocess (ffplay/mpg123/aplay)
        if self._current_audio_process is not None:
            try:
                self._current_audio_process.terminate()
                try:
                    self._current_audio_process.wait(timeout=1)
                except:
                    self._current_audio_process.kill()
                self._current_audio_process = None
            except Exception as e:
                print(f"[VoiceAssistant] Error killing audio process: {e}")
        
        # Stop pygame (Windows fallback)
        try:
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                pygame.mixer.music.stop()
                try:
                    pygame.mixer.music.unload()
                except:
                    pass
        except Exception as e:
            print(f"[VoiceAssistant] Error stopping pygame: {e}")
        
        # Set cooldown after stopping
        self._speech_cooldown_until = time.time() + self._speech_cooldown_seconds
    
    def _is_in_cooldown(self):
        """Check if we're still in post-speech cooldown period."""
        return time.time() < self._speech_cooldown_until
    
    def _speak_elevenlabs(self, text: str):
        import requests as req
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {"xi-api-key": self.api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
            payload = {"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}
            response = req.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code != 200:
                raise Exception(f"ElevenLabs API error {response.status_code}")
            temp_path = os.path.join(tempfile.gettempdir(), f"el_tts_{int(time.time()*1000)}.mp3")
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            self._play_audio(temp_path)
            try: os.unlink(temp_path)
            except: pass
        except Exception as e:
            if "quota" in str(e).lower():
                self.elevenlabs_quota_exceeded = True
            raise
    
    def _speak_edge_tts(self, text: str):
        async def _generate_speech():
            temp_file = os.path.join(tempfile.gettempdir(), f"edge_tts_{int(time.time()*1000)}.mp3")
            has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
            voice = "ar-EG-SalmaNeural" if has_arabic else "en-US-AriaNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file)
            return temp_file
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            temp_file = loop.run_until_complete(_generate_speech())
            loop.close()
            self._play_audio(temp_file)
            try: os.unlink(temp_file)
            except: pass
        except:
            raise
    
    def _speak_offline(self, text: str):
        import subprocess, platform
        system = platform.system()
        has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
        try:
            if system == 'Windows':
                translated_text = translate(text) if has_arabic else text
                safe_text = translated_text.replace('"', '`"').replace("'", "`'").replace('\n', ' ')
                ps_command = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Rate = 0; $synth.Speak("{safe_text}")'
                subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, timeout=60)
            elif system == 'Linux':
                voice_lang = "mb-ar1" if has_arabic else "en"
                result = subprocess.run(["espeak", "-v", voice_lang, text], capture_output=True, text=True, timeout=30)
                if result.returncode != 0 and has_arabic:
                    # Fallback to standard Arabic if mb-ar1 fails, before translating
                    result_fallback = subprocess.run(["espeak", "-v", "ar", text], capture_output=True, text=True, timeout=30)
                    if result_fallback.returncode != 0:
                        subprocess.run(["espeak", translate(text)], capture_output=True, text=True, timeout=30)
        except:
            raise
    
    def _play_audio(self, filepath: str):
        import platform
        import subprocess
        import os
        system = platform.system()
        
        # On Linux (Raspberry Pi), native players avoid ALSA locking issues common with PyGame
        if system == 'Linux':
            try:
                import shutil
                cmd = None
                if shutil.which("ffplay"):
                    cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath]
                elif shutil.which("mpg123"):
                    cmd = ["mpg123", "-q", filepath]
                elif filepath.endswith(".wav") and shutil.which("aplay"):
                    cmd = ["aplay", "-q", filepath]
                
                if cmd:
                    proc = subprocess.Popen(cmd)
                    self._current_audio_process = proc
                    proc.wait()  # Block until playback finishes
                    self._current_audio_process = None
                    return
            except Exception as e:
                self._current_audio_process = None
                print(f"[Audio] Linux player failed, falling back to pygame: {e}")

        # Windows / Mac / Fallback
        if not PYGAME_AVAILABLE: 
            print("[Audio] Pygame not available for playback")
            return
            
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): 
                if not self.is_speaking:  # Check if stop was requested
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[Audio] Pygame playback error: {e}")
            try: pygame.mixer.music.unload()
            except: pass
    
    def start_listening(self):
        if not SR_AVAILABLE or not self.listening_enabled: return
        
        with self._listen_lock:
            # Prevent spawning multiple concurrent thread loops
            if self._listen_thread and self._listen_thread.is_alive():
                print("[VoiceAssistant] Listen thread is already running or stopping. Reusing it.")
                self._stop_listening.clear()
                self.is_listening = True
                return
                
            self.is_listening = True
            self._stop_listening.clear()
            self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._listen_thread.start()
    
    def stop_listening(self):
        with self._listen_lock:
            self._stop_listening.set()
            self.is_listening = False
    
    def _record_arecord(self, duration: int) -> Optional[str]:
        """Record using arecord directly via ALSA - bypasses PulseAudio completely."""
        tmp_path = os.path.join(tempfile.gettempdir(), f"mic_{int(time.time()*1000)}.wav")
        
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
        
        try:
            # Use subprocess.Popen so we can monitor and terminate it early
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Check status of process and check if we need to stop
            start_time = time.time()
            while time.time() - start_time < duration:
                # If we need to stop listening or start speaking, terminate the recording
                if self._stop_listening.is_set() or self.is_speaking:
                    process.terminate()
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    if os.path.exists(tmp_path):
                        try: os.unlink(tmp_path)
                        except: pass
                    return None
                
                # Check if the process exited early for some reason (error)
                if process.poll() is not None:
                    break
                    
                time.sleep(0.1)
                
            # Wait for process to finish completely if it's still running
            if process.poll() is None:
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait()
            
            # Check exit code
            if process.returncode != 0:
                stderr = process.stderr.read().decode('utf-8', errors='ignore')
                print(f"[VoiceAssistant] arecord failed with code {process.returncode}: {stderr}")
                if os.path.exists(tmp_path):
                    try: os.unlink(tmp_path)
                    except: pass
                return None
                
            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                print(f"[VoiceAssistant] arecord produced empty file or file doesn't exist.")
                return None
                
            return tmp_path
            
        except Exception as e:
            print(f"[VoiceAssistant] Exception while recording with arecord: {e}")
            if os.path.exists(tmp_path):
                try: os.unlink(tmp_path)
                except: pass
            return None

    def _transcribe_file(self, filepath: str) -> Optional[str]:
        """Transcribe a WAV file using Groq Whisper with custom vocabulary guidance prompt."""
        try:
            from groq import Groq
            api_key = config.GROQ_API_KEY
            if not api_key:
                print("[VoiceAssistant] GROQ_API_KEY not found in config!")
                return None
            
            # Guides Whisper to transcribe custom vocabulary and dialects correctly
            guide_prompt = "موافق، غير موافق، أسباب نقص فيتامين دال، المساعد الطبي الذكي، قياس السكر، تحليل الطعام، الصفحة الرئيسية، خروج، نعم، لا، تمام، تفضل"
            
            client = Groq(api_key=api_key)
            with open(filepath, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(filepath, audio_file.read()),
                    model="whisper-large-v3",
                    language="ar",
                    prompt=guide_prompt
                )
            text = transcription.text.strip()
            return text
        except Exception as e:
            print(f"[VoiceAssistant] Whisper transcription error: {e}")
            return None

    def _is_silence(self, audio_data: sr.AudioData, threshold: float = 350.0) -> bool:
        """Check if the recorded audio is silent/noise based on RMS amplitude."""
        try:
            raw_data = audio_data.frame_data
            if not raw_data:
                return True
                
            # If sample width is 2 bytes (16-bit PCM)
            if audio_data.sample_width == 2:
                count = len(raw_data) // 2
                if count == 0:
                    return True
                
                # Sample a maximum of 10000 points to keep calculations fast and efficient
                step = max(1, count // 10000)
                samples = []
                import struct
                for i in range(0, count, step):
                    val, = struct.unpack("<h", raw_data[i*2 : i*2+2])
                    samples.append(val)
                
                if not samples:
                    return True
                    
                sum_squares = sum(s * s for s in samples)
                rms = (sum_squares / len(samples)) ** 0.5
                print(f"[VoiceAssistant] Audio analysis: RMS volume = {rms:.1f} (threshold = {threshold})")
                return rms < threshold
        except Exception as e:
            print(f"[VoiceAssistant] Error analyzing audio volume: {e}")
        return False

    def _is_wav_file_silence(self, filepath: str, threshold: float = 350.0) -> bool:
        """Check if a WAV file is silent/noise based on RMS amplitude."""
        try:
            if not os.path.exists(filepath):
                return True
            with open(filepath, "rb") as f:
                f.read(44)  # Skip WAV header (44 bytes)
                raw_data = f.read()
            
            if not raw_data:
                return True
                
            count = len(raw_data) // 2
            if count == 0:
                return True
                
            step = max(1, count // 10000)
            samples = []
            import struct
            for i in range(0, count, step):
                val, = struct.unpack("<h", raw_data[i*2 : i*2+2])
                samples.append(val)
                
            if not samples:
                return True
                
            sum_squares = sum(s * s for s in samples)
            rms = (sum_squares / len(samples)) ** 0.5
            print(f"[VoiceAssistant] arecord analysis: RMS volume = {rms:.1f} (threshold = {threshold})")
            return rms < threshold
        except Exception as e:
            print(f"[VoiceAssistant] Error analyzing WAV file volume: {e}")
        return False

    def _get_working_microphone(self) -> Optional[sr.Microphone]:
        """Try to initialize sr.Microphone. If it fails, scan for other available indices."""
        if not SR_AVAILABLE:
            return None
            
        # 1. Try the configured device index first
        try:
            # Using 16000Hz standard sample rate for high compatibility and Whisper speed
            mic_kwargs = {'sample_rate': 16000, 'chunk_size': 1024}
            if self._mic_device_index is not None:
                mic_kwargs['device_index'] = self._mic_device_index
            mic = sr.Microphone(**mic_kwargs)
            with mic as source:
                pass
            return mic
        except Exception as e:
            print(f"[VoiceAssistant] Failed to open microphone with index {self._mic_device_index}: {e}")
            
        # 2. Try default (None) if configured failed and is not None
        if self._mic_device_index is not None:
            try:
                print("[VoiceAssistant] Trying system default microphone (device_index=None)...")
                mic = sr.Microphone(sample_rate=16000, chunk_size=1024)
                with mic as source:
                    pass
                self._mic_device_index = None
                return mic
            except Exception as ex:
                print(f"[VoiceAssistant] Failed to open default microphone: {ex}")
                
        # 3. Loop through all available microphone indices
        try:
            mic_names = sr.Microphone.list_microphone_names()
            print(f"[VoiceAssistant] Searching for any working microphone among {len(mic_names)} devices...")
            for idx in range(len(mic_names)):
                if idx == self._mic_device_index:
                    continue
                try:
                    mic = sr.Microphone(device_index=idx, sample_rate=16000, chunk_size=1024)
                    with mic as source:
                        pass
                    print(f"[VoiceAssistant] Found working microphone '{mic_names[idx]}' at index {idx}")
                    self._mic_device_index = idx
                    return mic
                except Exception:
                    continue
        except Exception as ex:
            print(f"[VoiceAssistant] Error listing microphones: {ex}")
            
        return None

    def _listen_loop(self):
        use_arecord = (platform.system() == 'Linux' and shutil.which("arecord"))
        if use_arecord:
            print("[VoiceAssistant] Starting arecord-based listen loop (direct ALSA USB plughw:1,0)...")
            while not self._stop_listening.is_set():
                try:
                    if self.is_speaking or self._is_in_cooldown():
                        time.sleep(0.2)
                        continue
                    
                    # Record 5-second segments
                    listen_start = time.time()
                    wav_path = self._record_arecord(duration=5)
                    listen_end = time.time()
                    
                    if not wav_path:
                        time.sleep(0.2)
                        continue
                    
                    # Check for overlap with speech or cooldown
                    if self._audio_overlaps_speech(listen_start, listen_end):
                        print("[VoiceAssistant] arecord audio discarded due to overlap with speech/cooldown.")
                        try: os.unlink(wav_path)
                        except: pass
                        continue
                    
                    # RMS silence filter for Linux WAV recording
                    if self._is_wav_file_silence(wav_path, threshold=350.0):
                        print("[VoiceAssistant] arecord audio discarded as silence.")
                        try: os.unlink(wav_path)
                        except: pass
                        continue
                    
                    text = self._transcribe_file(wav_path)
                    try: os.unlink(wav_path)
                    except: pass
                    
                    if text:
                        print(f"[VoiceAssistant] Transcribed via Whisper: {text}")
                        self._process_command(text)
                except Exception as e:
                    print(f"[VoiceAssistant] Error in arecord listen loop: {e}")
                    time.sleep(1)
            self.is_listening = False
        else:
            print(f"[VoiceAssistant] Fallback: Starting speech_recognition-based listen loop (device_index={self._mic_device_index})...")
            
            while not self._stop_listening.is_set():
                try:
                    mic = self._get_working_microphone()
                    if not mic:
                        print("[VoiceAssistant] No working microphone found. Stopping listen loop.")
                        break
                        
                    with mic as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                        if self.recognizer.energy_threshold < 1200:
                            self.recognizer.energy_threshold = 1200
                        print(f"[VoiceAssistant] Calibration complete. Energy threshold set to: {self.recognizer.energy_threshold}")
                        
                        while not self._stop_listening.is_set():
                            try:
                                # Mute mic while bot is speaking or in cooldown
                                if self.is_speaking or self._is_in_cooldown():
                                    time.sleep(0.3)
                                    continue
                                
                                listen_start = time.time()
                                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=20)
                                listen_end = time.time()
                                
                                # Check for overlap with speech or cooldown
                                if self._audio_overlaps_speech(listen_start, listen_end):
                                    print("[VoiceAssistant] Audio discarded due to overlap with speech/cooldown.")
                                    continue
                                
                                # RMS silence filter to prevent Whisper silence-hallucinations
                                if self._is_silence(audio, threshold=350.0):
                                    print("[VoiceAssistant] Audio discarded as silence.")
                                    continue
                                    
                                text = self._transcribe_audio(audio)
                                # Filter out noise: discard very short transcriptions
                                if text and len(text.strip()) > 2:
                                    print(f"[VoiceAssistant] Transcribed via Whisper (fallback): '{text}'")
                                    self._process_command(text)
                            except sr.WaitTimeoutError:
                                continue
                            except sr.UnknownValueError:
                                continue
                            except sr.RequestError:
                                time.sleep(1)
                except AttributeError as e:
                    if "PyAudio" in str(e):
                        print("[VoiceAssistant] PyAudio not installed - microphone listening disabled. App will continue without voice input.")
                    else:
                        print(f"[VoiceAssistant] Listen loop crashed: {e}")
                    break
                except Exception as e:
                    print(f"[VoiceAssistant] Listen loop error: {e}")
                    time.sleep(1)
            
            self.is_listening = False

    def _transcribe_audio(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcribe audio using Groq Whisper to avoid FLAC dependency and be faster."""
        try:
            # Enforce 16000Hz 16-bit mono PCM conversion for compatibility
            wav_data = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
            
            # Save to temporary file
            tmp_path = os.path.join(tempfile.gettempdir(), f"audio_{int(time.time()*1000)}.wav")
            with open(tmp_path, "wb") as f:
                f.write(wav_data)
                
            try:
                return self._transcribe_file(tmp_path)
            finally:
                # Cleanup
                try: os.unlink(tmp_path)
                except: pass
                
        except Exception as e:
            print(f"[VoiceAssistant] Whisper transcription error: {e}")
            return None
    
    def listen_once(self) -> Optional[str]:
        use_arecord = (platform.system() == 'Linux' and shutil.which("arecord"))
        if use_arecord:
            wav_path = self._record_arecord(duration=6)
            if not wav_path:
                return None
            try:
                if self._is_wav_file_silence(wav_path, threshold=350.0):
                    return None
                text = self._transcribe_file(wav_path)
                return text
            finally:
                try: os.unlink(wav_path)
                except: pass
        else:
            if not SR_AVAILABLE: return None
            try:
                mic = self._get_working_microphone()
                if not mic:
                    print("[VoiceAssistant] listen_once: No working microphone found.")
                    return None
                    
                with mic as source:
                    print(f"[VoiceAssistant] listen_once: opening mic with device_index={self._mic_device_index}")
                    # Bypass calibration to prevent cutting off the start of the user's speech
                    self.recognizer.energy_threshold = 1200
                    print(f"[VoiceAssistant] listen_once: energy_threshold set to {self.recognizer.energy_threshold}, listening...")
                    audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=20)
                    print("[VoiceAssistant] listen_once: audio captured, transcribing...")
                    
                    # RMS silence filter
                    if self._is_silence(audio, threshold=350.0):
                        print("[VoiceAssistant] listen_once: audio discarded as silence.")
                        return None
                        
                    return self._transcribe_audio(audio)
            except Exception as e:
                print(f"[VoiceAssistant] Error in listen_once: {e}")
                return None
    
    def _process_command(self, text: str):
        if self.on_speech_callback: self.on_speech_callback(text)
    
    def set_command_callback(self, callback): self.on_command_callback = callback
    def set_speech_callback(self, callback): self.on_speech_callback = callback
    def set_current_screen(self, screen): self.current_screen = screen
    
    def welcome_message(self):
        self.speak("مرحباً بكم. أنا المساعد الطبي الذكي، مصمم لتقديم خدمات الرعاية والمتابعة الصحية.")
    
    def ask_permission(self, callback=None):
        accept_words = ["نعم", "اوك", "موافق", "تمام", "ايوه", "اه", "تفضل", 
                       "مقبول", "اكيد", "طبعا", "بالتأكيد", "يلا", "ماشي",
                       "yes", "ok", "okay", "sure", "yeah"]
        reject_words = ["لا", "لأ", "مش موافق", "غير موافق", "ارفض", "مرفوض",
                       "no", "nope", "cancel"]
        
        max_attempts = 3
        
        for attempt in range(max_attempts):
            if attempt == 0:
                self.speak("هل تأذن لي بتفعيل المساعد الصوتي للتفاعل معكم؟ قل موافق أو غير موافق.")
            else:
                self.speak("من فضلك قل موافق لتفعيل الصوت، أو غير موافق لإيقافه.")
            
            # Wait a tiny fraction of a second for audio device transition
            time.sleep(0.2)
            
            print(f"[VoiceAssistant] Permission attempt {attempt+1}: opening microphone to listen...")
            response = self.listen_once()
            if not response:
                print(f"[VoiceAssistant] Permission attempt {attempt+1}: no response heard")
                continue
            
            response_lower = response.lower().strip()
            print(f"[VoiceAssistant] Permission attempt {attempt+1} heard: '{response}'")
            
            # Check for clear reject FIRST to prevent "غير موافق" matching "موافق"
            if any(word in response_lower for word in reject_words):
                self.speak("حسناً. يمكنك تفعيل المساعد الصوتي في أي وقت من القائمة الجانبية.")
                if callback: callback(False)
                return False
                
            # Check for clear accept SECOND
            if any(word in response_lower for word in accept_words):
                self.speak("شكراً لكم. المساعد الصوتي نشط الآن وجاهز للاستخدام.")
                if callback: callback(True)
                return True
            
            # Unclear response - ignore and retry
            print(f"[VoiceAssistant] Unclear response '{response}', ignoring...")
        
        # Max attempts reached with no clear answer - default to disabled
        self.speak("لم أتلقى رداً واضحاً. سيتم إيقاف المساعد الصوتي. يمكنك تفعيله من القائمة الجانبية.")
        if callback: callback(False)
        return False
    
    def test(self): return True


voice_assistant = VoiceAssistant()

if __name__ == "__main__":
    voice_assistant.test()
