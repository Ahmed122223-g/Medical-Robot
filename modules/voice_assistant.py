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
    
    def set_voice_permission(self, allowed: bool):
        self.listening_enabled = allowed
        if not allowed:
            self.stop_listening()
    
    def speak(self, text: str, wait: bool = True):
        if not self.voice_enabled or not text:
            return
        self.is_speaking = True
        def _speak():
            try:
                if self.elevenlabs_client and not self.elevenlabs_quota_exceeded:
                    self._speak_elevenlabs(text)
                elif EDGE_TTS_AVAILABLE:
                    self._speak_edge_tts(text)
                else:
                    self._speak_offline(text)
            except:
                if EDGE_TTS_AVAILABLE:
                    try:
                        self._speak_edge_tts(text)
                        return
                    except:
                        pass
                try:
                    self._speak_offline(text)
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
            communicate = edge_tts.Communicate(text, "ar-EG-SalmaNeural")
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
        try:
            if system == 'Windows':
                translated_text = translate(text)
                safe_text = translated_text.replace('"', '`"').replace("'", "`'").replace('\n', ' ')
                ps_command = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Rate = 0; $synth.Speak("{safe_text}")'
                subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, timeout=60)
            elif system == 'Linux':
                result = subprocess.run(["espeak", "-v", "ar", text], capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    subprocess.run(["espeak", translate(text)], capture_output=True, text=True, timeout=30)
        except:
            raise
    
    def _play_audio(self, filepath: str):
        if not PYGAME_AVAILABLE: return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): time.sleep(0.1)
            pygame.mixer.music.unload()
        except:
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
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                while not self._stop_listening.is_set():
                    try:
                        if self.is_speaking:
                            time.sleep(0.1)
                            continue
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        text = self.recognizer.recognize_google(audio, language="ar-EG")
                        if text: self._process_command(text)
                    except sr.WaitTimeoutError: continue
                    except sr.UnknownValueError: continue
                    except sr.RequestError: time.sleep(1)
        except:
            self.is_listening = False
    
    def listen_once(self) -> Optional[str]:
        if not SR_AVAILABLE: return None
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                return self.recognizer.recognize_google(audio, language="ar-EG")
        except:
            return None
    
    def _process_command(self, text: str):
        if self.on_speech_callback: self.on_speech_callback(text)
    
    def set_command_callback(self, callback): self.on_command_callback = callback
    def set_speech_callback(self, callback): self.on_speech_callback = callback
    def set_current_screen(self, screen): self.current_screen = screen
    
    def welcome_message(self):
        self.speak("مرحباً بك! أنا مريم، الروبوت الطبي الذكي. أنا هنا لمساعدتك ورعايتك.")
    
    def ask_permission(self, callback=None):
        self.speak("هل تسمح لي بالاستماع إليك والتحدث معك؟")
        response = self.listen_once()
        if response:
            if any(word in response.lower() for word in ["نعم", "اوك", "موافق", "تمام", "ايوه", "اه"]):
                self.set_voice_permission(True)
                self.speak("شكراً لك! أنا مستعد لمساعدتك.")
                if callback: callback(True)
                return True
            else:
                self.set_voice_permission(False)
                self.speak("حسناً، يمكنك تفعيل الصوت في أي وقت من الإعدادات.")
                if callback: callback(False)
                return False
        return None
    
    def test(self): return True


voice_assistant = VoiceAssistant()

if __name__ == "__main__":
    voice_assistant.test()
