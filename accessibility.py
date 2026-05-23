import json
import os
import threading
import time
from queue import Empty, Queue

import customtkinter as ctk

from config import ACCESSIBILITY_FILE

_DEFAULT_SETTINGS = {
    "high_contrast": False,
    "font_scale": 1.0,
    "tts_enabled": False,
    "audio_guidance_enabled": True,
    "tts_rate": 150,
}


class AccessibilityManager:
    def __init__(self):
        self.settings = self._load_settings()
        self._engine = None
        self._engine_ready = False
        self._engine_lock = threading.Lock()
        self._speech_queue = Queue(maxsize=1)
        self._speech_worker = None
        self._last_spoken_text = ""
        self._last_speak_time = 0.0
        self._debounce_seconds = 1.2

    def _load_settings(self):
        data = {}
        try:
            with open(ACCESSIBILITY_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = loaded
        except Exception:
            data = {}

        merged = dict(_DEFAULT_SETTINGS)
        merged.update(data)
        return merged

    def _ensure_engine(self):
        if self._engine_ready:
            return

        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("volume", 0.9)
            self._engine.setProperty("rate", int(self.settings.get("tts_rate", 150)))
            self._engine_ready = True
        except Exception:
            self._engine = None
            self._engine_ready = False

    def _speak_fallback_windows(self, text):
        try:
            import win32com.client

            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Rate = self._to_sapi_rate(int(self.settings.get("tts_rate", 150)))
            speaker.Speak(text)
        except Exception:
            pass

    def _to_sapi_rate(self, wpm):
        # SAPI usa faixa aproximada -10..10; mapeamos 80..280 WPM
        wpm = max(80, min(280, int(wpm)))
        return int(round(((wpm - 150) / 130) * 10))

    def _run_speech(self):
        while True:
            text = self._speech_queue.get()
            if not text:
                continue

            try:
                with self._engine_lock:
                    self._ensure_engine()
                    if self._engine_ready and self._engine is not None:
                        self._engine.stop()
                        self._engine.say(text)
                        self._engine.runAndWait()
                    elif os.name == "nt":
                        self._speak_fallback_windows(text)
            except Exception:
                if os.name == "nt":
                    self._speak_fallback_windows(text)

    def _start_worker_if_needed(self):
        if self._speech_worker and self._speech_worker.is_alive():
            return

        self._speech_worker = threading.Thread(target=self._run_speech, daemon=True)
        self._speech_worker.start()

    def stop(self):
        try:
            with self._engine_lock:
                if self._engine_ready and self._engine is not None:
                    self._engine.stop()
        except Exception:
            pass

    def speak(self, text):
        if not text:
            return
        if not self.settings.get("tts_enabled", False):
            return

        now = time.monotonic()
        if text == self._last_spoken_text and now - self._last_speak_time < self._debounce_seconds:
            return

        self._last_spoken_text = text
        self._last_speak_time = now

        # Mantem apenas o anuncio mais recente para evitar fila longa.
        try:
            while True:
                self._speech_queue.get_nowait()
        except Empty:
            pass

        self._start_worker_if_needed()
        try:
            self._speech_queue.put_nowait(text)
        except Exception:
            pass

    def update_tts_rate(self, wpm):
        rate = int(max(80, min(280, float(wpm))))
        self.settings["tts_rate"] = rate

        try:
            with self._engine_lock:
                if self._engine_ready and self._engine is not None:
                    self._engine.setProperty("rate", rate)
        except Exception:
            pass

    def apply_all(self):
        high_contrast = bool(self.settings.get("high_contrast", False))
        font_scale = float(self.settings.get("font_scale", 1.0))

        ctk.set_appearance_mode("light" if high_contrast else "dark")

        safe_scale = min(2.0, max(0.8, font_scale))
        try:
            ctk.set_widget_scaling(safe_scale)
        except Exception:
            pass

        try:
            ctk.set_window_scaling(safe_scale)
        except Exception:
            pass

    def save(self):
        safe = dict(_DEFAULT_SETTINGS)
        safe.update(self.settings)

        try:
            with open(ACCESSIBILITY_FILE, "w", encoding="utf-8") as f:
                json.dump(safe, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


_manager = None
_manager_lock = threading.Lock()


def get_manager():
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = AccessibilityManager()
    return _manager
