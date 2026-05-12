import json
import uuid
from datetime import datetime, timedelta
from plyer import notification
from config import HABITS_FILE


def _load() -> list:
    try:
        with open(HABITS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(habits: list) -> None:
    with open(HABITS_FILE, "w", encoding="utf-8") as f:
        json.dump(habits, f, ensure_ascii=False, indent=2)


def add_habit(title: str, interval_minutes: int = 120) -> dict:
    habits = _load()
    habit = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "interval_minutes": int(interval_minutes),
        "enabled": True,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "last_reminder_at": None,
    }
    habits.append(habit)
    _save(habits)
    return habit


def list_habits() -> list:
    return _load()


def delete_habit(habit_id: str) -> bool:
    habits = _load()
    new_habits = [h for h in habits if h["id"] != habit_id]
    if len(new_habits) == len(habits):
        return False
    _save(new_habits)
    return True


def toggle_habit(habit_id: str) -> bool:
    habits = _load()
    for h in habits:
        if h["id"] == habit_id:
            h["enabled"] = not h.get("enabled", True)
            _save(habits)
            return True
    return False


def _is_due(habit: dict, now: datetime) -> bool:
    if not habit.get("enabled", True):
        return False

    interval = int(habit.get("interval_minutes", 120))
    last_raw = habit.get("last_reminder_at")

    if not last_raw:
        return True

    try:
        last = datetime.fromisoformat(last_raw)
    except ValueError:
        return True

    return (now - last) >= timedelta(minutes=interval)


def check_habits_and_notify(verbose: bool = True) -> list:
    """Dispara lembretes dos hábitos vencidos. Retorna lista de hábitos notificados."""
    habits = _load()
    now = datetime.now()
    notified = []

    for h in habits:
        if not _is_due(h, now):
            continue

        try:
            notification.notify(
                title=f"⏰ Hábito: {h['title']}",
                message=f"Hora de cumprir seu hábito (a cada {h['interval_minutes']} min).",
                app_name="Organizador Pessoal",
                timeout=8,
            )
        except Exception as e:
            if verbose:
                print(f"[Hábitos] Erro ao notificar '{h['title']}': {e}")
            continue

        h["last_reminder_at"] = now.isoformat(timespec="seconds")
        notified.append(h)
        if verbose:
            print(f"[Hábitos] Lembrete enviado: {h['title']}")

    if notified:
        _save(habits)
    elif verbose:
        print("[Hábitos] Nenhum hábito para lembrar agora.")

    return notified


def send_habit_reminder_now(habit_id: str) -> bool:
    habits = _load()
    now = datetime.now().isoformat(timespec="seconds")
    for h in habits:
        if h["id"] == habit_id:
            try:
                notification.notify(
                    title=f"⏰ Hábito: {h['title']}",
                    message="Lembrete manual enviado.",
                    app_name="Organizador Pessoal",
                    timeout=8,
                )
                h["last_reminder_at"] = now
                _save(habits)
                return True
            except Exception:
                return False
    return False
