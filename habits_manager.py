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


# ── Sincronização Supabase ───────────────────────────────────────────────────

def _bg_insert(habit):
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("habits").insert(habit).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao inserir hábito: {e}")


def _bg_update(habit_id, data):
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("habits").update(data).eq("id", habit_id).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao atualizar hábito: {e}")


def _bg_delete(habit_id):
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("habits").delete().eq("id", habit_id).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao excluir hábito: {e}")


def sync_with_supabase():
    """Busca hábitos do Supabase para atualizar o cache local, ou envia o cache se a nuvem estiver vazia."""
    from supabase_client import supabase, run_in_background
    if not supabase:
        return

    def _sync():
        try:
            res = supabase.table("habits").select("*").execute()
            remote_habits = res.data
            if remote_habits:
                _save(remote_habits)
                print("[Sync Habits] Sincronizado do Supabase para o cache local.")
            else:
                local_habits = _load()
                if local_habits:
                    print("[Sync Habits] Supabase está vazio. Enviando dados locais...")
                    supabase.table("habits").insert(local_habits).execute()
                    print("[Sync Habits] Dados locais enviados com sucesso.")
        except Exception as e:
            print(f"[Sync Habits] Falha na sincronização: {e}")

    run_in_background(_sync)


# ── CRUD e Métodos ──────────────────────────────────────────────────────────

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

    from supabase_client import run_in_background
    run_in_background(_bg_insert, habit)

    return habit


def list_habits() -> list:
    return _load()


def delete_habit(habit_id: str) -> bool:
    habits = _load()
    new_habits = [h for h in habits if h["id"] != habit_id]
    if len(new_habits) == len(habits):
        return False
    _save(new_habits)

    from supabase_client import run_in_background
    run_in_background(_bg_delete, habit_id)

    return True


def toggle_habit(habit_id: str) -> bool:
    habits = _load()
    for h in habits:
        if h["id"] == habit_id:
            h["enabled"] = not h.get("enabled", True)
            _save(habits)

            from supabase_client import run_in_background
            run_in_background(_bg_update, habit_id, {"enabled": h["enabled"]})
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
                app_name="Task Flow",
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
        # Sincroniza o last_reminder_at dos hábitos notificados
        from supabase_client import run_in_background
        for h in notified:
            run_in_background(_bg_update, h["id"], {"last_reminder_at": h["last_reminder_at"]})
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
                    app_name="Task Flow",
                    timeout=8,
                )
                h["last_reminder_at"] = now
                _save(habits)

                from supabase_client import run_in_background
                run_in_background(_bg_update, habit_id, {"last_reminder_at": h["last_reminder_at"]})
                return True
            except Exception:
                return False
    return False

