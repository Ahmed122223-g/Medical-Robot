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
    print("⚠️ ElevenLabs not installed. pip install elevenlabs")

try:
    import edge_tts
    import asyncio
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("⚠️ edge-tts not installed. pip install edge-tts")

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("⚠️ SpeechRecognition not installed. pip install SpeechRecognition")

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False
    print("⚠️ pygame audio not available")


class VoiceAssistant:
    
    ARABIC_VOICE_IDS = {
        "male": "pNInz6obpgDQGcFmaJgB",
        "female": "EXAVITQu4vr4xnSDxMaL",
    }
    
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
                print("✅ ElevenLabs initialized")
            except Exception as e:
                print(f"⚠️ ElevenLabs init failed: {e}")
        
        self.voice_id = self.ARABIC_VOICE_IDS["female"]
        
        self._listen_thread = None
        self._stop_listening = threading.Event()
        
        self.elevenlabs_quota_exceeded = False
        
        print(f"✅ Voice Assistant initialized (Enabled: {self.voice_enabled})")
    
    def set_voice_permission(self, allowed: bool):
        self.listening_enabled = allowed
        if allowed:
            print("🎤 Voice permission granted - الإذن بالتحدث والاستماع")
        else:
            self.stop_listening()
            print("🔇 Voice permission denied - تم إيقاف الاستماع")
    
    def speak(self, text: str, wait: bool = True):
        if not self.voice_enabled:
            print(f"🔇 TTS disabled: {text}")
            return
        
        if not text:
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
            except Exception as e:
                print(f"⚠️ TTS Error: {e}")
                if EDGE_TTS_AVAILABLE:
                    try:
                        self._speak_edge_tts(text)
                        return
                    except Exception as e2:
                        print(f"⚠️ Edge TTS fallback failed: {e2}")
                try:
                    self._speak_offline(text)
                except Exception as e3:
                    print(f"⚠️ Offline TTS also failed: {e3}")
            finally:
                self.is_speaking = False
        
        if wait:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()
    
    def _speak_elevenlabs(self, text: str):
        import requests as req
        
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg"
            }
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = req.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"ElevenLabs API error {response.status_code}: {response.text}")
            
            temp_path = os.path.join(tempfile.gettempdir(), f"el_tts_{int(time.time()*1000)}.mp3")
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            self._play_audio(temp_path)
            
            try:
                os.unlink(temp_path)
            except:
                pass
            
            print("🔊 Played via ElevenLabs")
            
        except Exception as e:
            error_str = str(e)
            print(f"⚠️ ElevenLabs TTS failed: {e}")
            
            if "quota_exceeded" in error_str or "quota" in error_str.lower():
                self.elevenlabs_quota_exceeded = True
                print("📢 ElevenLabs quota exceeded - Switching to Edge TTS")
            
            raise
    
    def _speak_edge_tts(self, text: str):
        async def _generate_speech():
            voice = "ar-EG-SalmaNeural" 
            
            temp_file = os.path.join(tempfile.gettempdir(), f"edge_tts_{int(time.time()*1000)}.mp3")
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file)
            
            return temp_file
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            temp_file = loop.run_until_complete(_generate_speech())
            loop.close()
            
            self._play_audio(temp_file)
            
            try:
                os.unlink(temp_file)
            except:
                pass
            
            print("🔊 Played via Edge TTS (Arabic)")
            
        except Exception as e:
            print(f"⚠️ Edge TTS failed: {e}")
            raise
    
    def _speak_offline(self, text: str):
        import subprocess
        import platform
        
        system = platform.system()
        
        try:
            if system == 'Windows':
                translated_text = translate(text)
                safe_text = translated_text.replace('"', '`"').replace("'", "`'").replace('\n', ' ')
                
                ps_command = f'''
                Add-Type -AssemblyName System.Speech
                $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synth.Rate = 0
                $synth.Speak("{safe_text}")
                '''
                
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print("🔊 Played via Windows SAPI (English)")
                else:
                    print(f"⚠️ Windows SAPI error: {result.stderr}")                    
            elif system == 'Linux':
                result = subprocess.run(
                    ["espeak", "-v", "ar", text],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print("🔊 Played via espeak (Arabic)")
                else:
                    english_text = translate(text)
                    result = subprocess.run(
                        ["espeak", english_text],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        print("🔊 Played via espeak (English)")
                    else:
                        raise Exception(result.stderr)
            else:
                raise Exception(f"Unsupported OS: {system}")
                
        except Exception as e:
            print(f"⚠️ Offline TTS failed: {e}")
            raise
    
    def _play_audio(self, filepath: str):
        if not PYGAME_AVAILABLE:
            print(f"⚠️ Cannot play audio: pygame not available")
            return
        
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            pygame.mixer.music.unload()
                
        except Exception as e:
            print(f"⚠️ Audio playback error: {e}")
            try:
                pygame.mixer.music.unload()
            except:
                pass
    
    def start_listening(self):
        if not SR_AVAILABLE:
            print("⚠️ Speech recognition not available")
            return
        
        if not self.listening_enabled:
            print("🔇 Listening not permitted")
            return
        
        if self.is_listening:
            return
        
        self.is_listening = True
        self._stop_listening.clear()
        
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        print("🎤 Started listening...")
    
    def stop_listening(self):
        self._stop_listening.set()
        self.is_listening = False
        print("🔇 Stopped listening")
    
    def _listen_loop(self):
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("🎤 Microphone ready, listening...")
                
                while not self._stop_listening.is_set():
                    try:
                        if self.is_speaking:
                            time.sleep(0.1)
                            continue
                        
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                        
                        text = self.recognizer.recognize_google(audio, language="ar-EG")
                        
                        if text:
                            print(f"🗣️ Heard: {text}")
                            self._process_command(text)
                            
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError as e:
                        print(f"⚠️ Speech recognition error: {e}")
                        time.sleep(1)
                        
        except Exception as e:
            print(f"⚠️ Microphone error: {e}")
            self.is_listening = False
    
    def listen_once(self) -> Optional[str]:
        if not SR_AVAILABLE:
            return None
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("🎤 Listening...")
                
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                text = self.recognizer.recognize_google(audio, language="ar-EG")
                
                print(f"🗣️ Heard: {text}")
                return text
                
        except sr.WaitTimeoutError:
            print("⏱️ Timeout - no speech detected")
            return None
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
            return None
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return None
    
    def _process_command(self, text: str):
        if self.on_speech_callback:
            self.on_speech_callback(text)
    
    def set_command_callback(self, callback: Callable):
        self.on_command_callback = callback
    
    def set_speech_callback(self, callback: Callable):
        self.on_speech_callback = callback
    
    def set_current_screen(self, screen: str):
        self.current_screen = screen
    
    def welcome_message(self):
        message = "مرحباً بك! أنا مريم، الروبوت الطبي الذكي. أنا هنا لمساعدتك ورعايتك."
        self.speak(message)
    
    def ask_permission(self, callback: Callable = None):
        message = "هل تسمح لي بالاستماع إليك والتحدث معك؟"
        self.speak(message)
        
        response = self.listen_once()
        
        if response:
            response_lower = response.lower()
            if any(word in response_lower for word in ["نعم", "اوك", "موافق", "تمام", "ايوه", "اه"]):
                self.set_voice_permission(True)
                self.speak("شكراً لك! أنا مستعد لمساعدتك.")
                if callback:
                    callback(True)
                return True
            else:
                self.set_voice_permission(False)
                self.speak("حسناً، يمكنك تفعيل الصوت في أي وقت من الإعدادات.")
                if callback:
                    callback(False)
                return False
        
        return None
    
    def test(self):
        print("🧪 Testing Voice Assistant...")
        
        if ELEVENLABS_AVAILABLE and self.elevenlabs_client:
            print("✅ ElevenLabs available")
        else:
            print("⚠️ ElevenLabs not available")
        
        if SR_AVAILABLE:
            print("✅ Speech Recognition available")
        else:
            print("⚠️ Speech Recognition not available")
        
        if PYGAME_AVAILABLE:
            print("✅ Pygame audio available")
        else:
            print("⚠️ Pygame audio not available")
        
        return True


voice_assistant = VoiceAssistant()


if __name__ == "__main__":
    voice_assistant.test()
    
    print("\n🔊 Testing TTS...")
    voice_assistant.speak("مرحباً، أنا الروبوت الطبي")
