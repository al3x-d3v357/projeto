"""Gerenciador de acessibilidade: TTS (pyttsx3) + alto contraste + escala de fonte."""

import json
import queue
import threading

import customtkinter as ctk

from config import ACCESSIBILITY_FILE

_DEFAULTS: dict = {
    "tts_enabled": False,
    "tts_rate": 165,
    "high_contrast": False,
    "font_scale": 1.0,
}


class AccessibilityManager:
    def __init__(self):
        self.settings: dict = dict(_DEFAULTS)
        self._tts_queue: queue.Queue = queue.Queue()
        self._tts_engine = None
        self._tts_ready = threading.Event()
        self.load()
        self._start_tts_thread()

    # ── Persistência ─────────────────────────────────────────────────────────

    def load(self) -> None:
        try:
            with open(ACCESSIBILITY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, default in _DEFAULTS.items():
                self.settings[k] = data.get(k, default)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = dict(_DEFAULTS)

    def save(self) -> None:
        try:
            with open(ACCESSIBILITY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── TTS ──────────────────────────────────────────────────────────────────

    def _start_tts_thread(self) -> None:
        t = threading.Thread(target=self._tts_worker, daemon=True)
        t.start()

    def _tts_worker(self) -> None:
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", int(self.settings["tts_rate"]))
            # Prefere voz em português se disponível
            voices = engine.getProperty("voices")
            for v in voices:
                if "pt" in v.id.lower() or "portuguese" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            self._tts_engine = engine
            self._tts_ready.set()
            while True:
                text = self._tts_queue.get()
                if text is None:
                    break
                if self.settings["tts_enabled"] and text:
                    try:
                        engine.say(text)
                        engine.runAndWait()
                    except Exception:
                        pass
        except Exception:
            self._tts_ready.set()

    def speak(self, text: str) -> None:
        """Fala o texto em background se TTS estiver ativado."""
        if not self.settings["tts_enabled"]:
            return
        # Descarta itens pendentes para evitar acúmulo de fala
        while not self._tts_queue.empty():
            try:
                self._tts_queue.get_nowait()
            except queue.Empty:
                break
        self._tts_queue.put(text)

    def update_tts_rate(self, rate: int) -> None:
        self.settings["tts_rate"] = int(rate)
        if self._tts_engine:
            try:
                self._tts_engine.setProperty("rate", int(rate))
            except Exception:
                pass

    # ── Aparência ─────────────────────────────────────────────────────────────

    def apply_font_scale(self) -> None:
        scale = float(self.settings["font_scale"])
        ctk.set_widget_scaling(scale)
        ctk.set_window_scaling(scale)

    def apply_appearance(self) -> None:
        if self.settings["high_contrast"]:
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

    def apply_all(self) -> None:
        self.apply_font_scale()
        self.apply_appearance()


# ── Singleton ─────────────────────────────────────────────────────────────────

_manager: "AccessibilityManager | None" = None


def get_manager() -> AccessibilityManager:
    global _manager
    if _manager is None:
        _manager = AccessibilityManager()
    return _manager
