import asyncio
import edge_tts
import pygame
import threading
import time
import os
import tempfile

import asyncio
import edge_tts
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import pygame
import threading
import time
import tempfile
import queue

class VibeEngine:
    def __init__(self):
        self.enabled = True
        self.voice = "en-US-AriaNeural"
        self.queue = queue.Queue()
        self.running = True
        
        try:
            pygame.mixer.init()
            # Start a dedicated worker thread for speech
            self.thread = threading.Thread(target=self._worker, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"[!] Audio Init Error: {e}")
            self.enabled = False

    def _worker(self):
        """Dedicated worker loop to process speech requests."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            try:
                text = self.queue.get(timeout=1)
                if text is None: break  # Sentinel to stop
                
                # Generate and play
                self._speak_now(text)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Silent fail on shutdown to avoid ugly logs
                pass
        
        loop.close()

    def _speak_now(self, text):
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
                temp_filename = tf.name
            
            communicate = edge_tts.Communicate(text, self.voice)
            asyncio.run(communicate.save(temp_filename))
            
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            pygame.mixer.music.unload()
            os.remove(temp_filename)
        except:
            pass

    def speak(self, text):
        """Add text to the speech queue."""
        if self.enabled:
            self.queue.put(text)

    def alert(self, sound_type="info"):
        if sound_type == "danger":
            self.speak("Critical Alert.")
        elif sound_type == "success":
            self.speak("System Secure.")

    def shutdown(self):
        """Clean shutdown."""
        self.running = False
        # No need to join daemon thread, let it die


if __name__ == "__main__":
    vibe = VibeEngine()
    print("Testing Neural Vibe Engine...")
    vibe.speak("Purple Vibe Security Systems Online.")
    time.sleep(5)
    print("Done.")
