import os
import sys
import threading
import tempfile
import time
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
        self.current_screen = "home"
        self.on_command_callback: Optional[Callable] = None
        self.on_speech_callback: Optional[Callable] = None
        self.recognizer = sr.Recognizer() if SR_AVAILABLE else None
        self.microphone = None
        # تم تحديد رقم المايك (1) بناءً على اختبار sounddevice 
        self._mic_device_index = 1
        self.elevenlabs_client = None
        if ELEVENLABS_AVAILABLE and self.api_key:
            try:
                self.elevenlabs_client = ElevenLabs(api_key=self.api_key)
            except:
                pass
        self.voice_id = self.ARABIC_VOICE_IDS["female"]
        self._listen_thread = None
        self._stop_listening = threading.Event()
        self.elevenlabs_quota_exceeded = False
        
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
        self.is_speaking = True
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
        if wait: _speak()
        else: threading.Thread(target=_speak, daemon=True).start()
    
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
                voice_lang = "ar" if has_arabic else "en"
                result = subprocess.run(["espeak", "-v", voice_lang, text], capture_output=True, text=True, timeout=30)
                if result.returncode != 0 and has_arabic:
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
                # Try ffplay (very reliable)
                import shutil
                if shutil.which("ffplay"):
                    subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", filepath], check=True)
                    return
                # Try mpg123 as fallback for mp3
                elif shutil.which("mpg123"):
                    subprocess.run(["mpg123", "-q", filepath], check=True)
                    return
                # Try aplay for wav
                elif filepath.endswith(".wav") and shutil.which("aplay"):
                    subprocess.run(["aplay", "-q", filepath], check=True)
                    return
            except Exception as e:
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
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[Audio] Pygame playback error: {e}")
            try: pygame.mixer.music.unload()
            except: pass
    
    def start_listening(self):
        if not SR_AVAILABLE or not self.listening_enabled or self.is_listening: return
        self.is_listening = True
        self._stop_listening.clear()
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
    
    def stop_listening(self):
        self._stop_listening.set()
        self.is_listening = False
    
    def _listen_loop(self):
        try:
            mic_kwargs = {}
            if self._mic_device_index is not None:
                mic_kwargs['device_index'] = self._mic_device_index
            with sr.Microphone(**mic_kwargs) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                while not self._stop_listening.is_set():
                    try:
                        if self.is_speaking:
                            time.sleep(0.1)
                            continue
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        text = self._transcribe_with_gemini(audio)
                        if text: self._process_command(text)
                    except sr.WaitTimeoutError: continue
                    except sr.UnknownValueError: continue
                    except sr.RequestError: time.sleep(1)
        except:
            self.is_listening = False

    def _transcribe_with_gemini(self, audio_data: sr.AudioData) -> Optional[str]:
        """Transcribe audio using Gemini instead of Google Web API to avoid FLAC dependency."""
        if not self.gemini_model:
            # Fallback to Google if Gemini is not available
            return self.recognizer.recognize_google(audio_data, language="ar-EG")
            
        try:
            import tempfile
            import os
            import google.generativeai as genai
            
            # Save audio to a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(audio_data.get_wav_data())
                tmp_path = tmp_file.name
                
            try:
                # Upload and transcribe
                audio_file = genai.upload_file(tmp_path)
                response = self.gemini_model.generate_content([
                    "استخرج النص من هذا المقطع الصوتي واكتبه كما هو باللغة العربية بالضبط، بدون أي مقدمات أو تعليقات.",
                    audio_file
                ])
                text = response.text.strip()
                try: genai.delete_file(audio_file.name)
                except: pass
                
                if text:
                    print(f"[VoiceAssistant] Gemini Recognized: '{text}'")
                    return text
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        except Exception as e:
            print(f"[VoiceAssistant] Gemini Transcription Error: {e}")
            # Fallback to Google
            try:
                return self.recognizer.recognize_google(audio_data, language="ar-EG")
            except:
                pass
        return None
    
    def listen_once(self) -> Optional[str]:
        if not SR_AVAILABLE: return None
        try:
            mic_kwargs = {}
            if self._mic_device_index is not None:
                mic_kwargs['device_index'] = self._mic_device_index
            with sr.Microphone(**mic_kwargs) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                return self._transcribe_with_gemini(audio)
        except:
            return None
    
    def _process_command(self, text: str):
        if self.on_speech_callback: self.on_speech_callback(text)
    
    def set_command_callback(self, callback): self.on_command_callback = callback
    def set_speech_callback(self, callback): self.on_speech_callback = callback
    def set_current_screen(self, screen): self.current_screen = screen
    
    def welcome_message(self):
        self.speak("مرحباً بكم. أنا المساعد الطبي الذكي، مصمم لتقديم خدمات الرعاية والمتابعة الصحية.")
    
    def ask_permission(self, callback=None):
        self.speak("هل تأذن لي بتفعيل المساعد الصوتي للتفاعل معكم؟")
        response = self.listen_once()
        if response:
            if any(word in response.lower() for word in ["نعم", "اوك", "موافق", "تمام", "ايوه", "اه", "تفضل", "مقبول"]):
                self.set_voice_permission(True)
                self.speak("شكراً لكم. المساعد الصوتي نشط الآن وجاهز للاستخدام.")
                if callback: callback(True)
                return True
            else:
                self.set_voice_permission(False)
                self.speak("تم التعطيل. يمكنك تفعيل المساعد الصوتي في أي وقت عبر الإعدادات.")
                if callback: callback(False)
                return False
        return None
    
    def test(self): return True


voice_assistant = VoiceAssistant()

if __name__ == "__main__":
    voice_assistant.test()
