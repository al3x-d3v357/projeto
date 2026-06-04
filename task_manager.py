import json
import uuid
from datetime import datetime, date, timedelta
from config import TASKS_FILE


def _load() -> list:
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(tasks: list) -> None:
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


# ── Tradução de Modelos ──────────────────────────────────────────────────────

def _to_local(remote: dict) -> dict:
    return {
        "id": str(remote["id"]),
        "title": remote["title"],
        "source": "manual",
        "status": "concluída" if remote.get("is_completed", False) else "pendente",
        "created_at": remote.get("created_at") or datetime.now().isoformat(timespec="seconds"),
        "due_date": remote.get("due_date") or None,
        "reminder_time": remote.get("reminder_time") or None,
        "remind_before_minutes": remote.get("advance_minutes") or 5,
        "last_reminder_for": None
    }


def _to_remote(local: dict) -> dict:
    return {
        "title": local["title"],
        "due_date": local.get("due_date"),
        "reminder_time": local.get("reminder_time"),
        "advance_minutes": int(local.get("remind_before_minutes", 5)),
        "is_completed": local.get("status") == "concluída"
    }


# ── Sincronização Supabase ───────────────────────────────────────────────────

def _bg_insert(task, local_id):
    from supabase_client import supabase
    if supabase:
        try:
            row = _to_remote(task)
            res = supabase.table("tasks").insert(row).execute()
            if res.data:
                remote_id = str(res.data[0]["id"])
                # Atualiza o ID local no arquivo
                tasks = _load()
                for t in tasks:
                    if t["id"] == local_id:
                        t["id"] = remote_id
                _save(tasks)
        except Exception as e:
            print(f"[Supabase Error] Falha ao inserir tarefa: {e}")


def _bg_update(task_id, data):
    if not task_id.isdigit():
        return
    from supabase_client import supabase
    if supabase:
        try:
            remote_data = {}
            if "status" in data:
                remote_data["is_completed"] = (data["status"] == "concluída")
            if remote_data:
                supabase.table("tasks").update(remote_data).eq("id", int(task_id)).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao atualizar tarefa: {e}")


def _bg_delete(task_id):
    if not task_id.isdigit():
        return
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("tasks").delete().eq("id", int(task_id)).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao excluir tarefa: {e}")


def sync_with_supabase():
    """Busca tarefas do Supabase para atualizar o cache local, ou envia o cache se a nuvem estiver vazia."""
    from supabase_client import supabase, run_in_background
    if not supabase:
        return

    def _sync():
        try:
            res = supabase.table("tasks").select("*").execute()
            remote_tasks = res.data
            if remote_tasks:
                local_format_tasks = [_to_local(t) for t in remote_tasks]
                _save(local_format_tasks)
                print("[Sync Tasks] Sincronizado do Supabase para o cache local.")
            else:
                local_tasks = _load()
                if local_tasks:
                    print("[Sync Tasks] Supabase está vazio. Enviando dados locais...")
                    upload_list = [_to_remote(t) for t in local_tasks]
                    res_insert = supabase.table("tasks").insert(upload_list).execute()
                    if res_insert.data:
                        for i, inserted in enumerate(res_insert.data):
                            if i < len(local_tasks):
                                local_tasks[i]["id"] = str(inserted["id"])
                        _save(local_tasks)
                    print("[Sync Tasks] Dados locais enviados com sucesso.")
        except Exception as e:
            print(f"[Sync Tasks] Falha na sincronização: {e}")

    run_in_background(_sync)


# ── CRUD e Métodos ──────────────────────────────────────────────────────────

def add_task(
    title: str,
    source: str = "manual",
    due_date: str = None,
    reminder_time: str = None,
    remind_before_minutes: int = 5,
) -> dict:
    """Adiciona uma nova tarefa. Retorna a tarefa criada."""
    tasks = _load()
    local_id = str(uuid.uuid4())[:8]
    task = {
        "id": local_id,
        "title": title,
        "source": source,
        "status": "pendente",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "due_date": due_date,
        "reminder_time": reminder_time,
        "remind_before_minutes": int(remind_before_minutes),
        "last_reminder_for": None,
    }
    tasks.append(task)
    _save(tasks)

    # Sincroniza em background
    from supabase_client import run_in_background
    run_in_background(_bg_insert, task, local_id)

    return task


def complete_task(task_id: str) -> bool:
    """Marca uma tarefa como concluída pelo ID. Retorna True se encontrada."""
    tasks = _load()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "concluída"
            task["completed_at"] = datetime.now().isoformat(timespec="seconds")
            _save(tasks)

            # Sincroniza em background
            from supabase_client import run_in_background
            run_in_background(_bg_update, task_id, {
                "status": "concluída"
            })
            return True
    return False


def delete_task(task_id: str) -> bool:
    """Remove uma tarefa pelo ID. Retorna True se encontrada."""
    tasks = _load()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        return False
    _save(new_tasks)

    # Sincroniza em background
    from supabase_client import run_in_background
    run_in_background(_bg_delete, task_id)
    return True


def _parse_due_date(value: str):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def list_tasks(status_filter: str = None, due_filter: str = None, sort_by_due: bool = False) -> list:
    """
    Lista tarefas com filtros opcionais.
    - status_filter: 'pendente' ou 'concluída'
    - due_filter: 'with_due', 'without_due', 'overdue', 'today', 'upcoming7'
    - sort_by_due: ordena por vencimento (sem data vão para o fim)
    """
    tasks = _load()
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]

    if due_filter:
        today = date.today()

        if due_filter == "with_due":
            tasks = [t for t in tasks if _parse_due_date(t.get("due_date")) is not None]
        elif due_filter == "without_due":
            tasks = [t for t in tasks if _parse_due_date(t.get("due_date")) is None]
        elif due_filter == "overdue":
            tasks = [
                t for t in tasks
                if (_parse_due_date(t.get("due_date")) is not None and _parse_due_date(t.get("due_date")) < today)
            ]
        elif due_filter == "today":
            tasks = [t for t in tasks if _parse_due_date(t.get("due_date")) == today]
        elif due_filter == "upcoming7":
            tasks = [
                t for t in tasks
                if (
                    _parse_due_date(t.get("due_date")) is not None
                    and 0 <= (_parse_due_date(t.get("due_date")) - today).days <= 7
                )
            ]

    if sort_by_due:
        tasks.sort(
            key=lambda t: (
                _parse_due_date(t.get("due_date")) is None,
                _parse_due_date(t.get("due_date")) or date.max,
                t.get("created_at") or "",
            )
        )

    return tasks


def print_tasks(status_filter: str = None) -> None:
    """Exibe tarefas formatadas no terminal."""
    tasks = list_tasks(status_filter)
    if not tasks:
        print("  Nenhuma tarefa encontrada.")
        return
    for t in tasks:
        status_icon = "✓" if t["status"] == "concluída" else "○"
        due = f"  [vence: {t['due_date']}]" if t.get("due_date") else ""
        reminder = ""
        if t.get("due_date") and t.get("reminder_time"):
            mins = int(t.get("remind_before_minutes", 5))
            reminder = f"  [lembrete: {t['reminder_time']} (-{mins}min)]"
        print(f"  [{status_icon}] ({t['id']}) {t['title']}{due}{reminder}  — origem: {t['source']}")


def _parse_due_datetime(task: dict):
    due_date = task.get("due_date")
    reminder_time = task.get("reminder_time")
    if not due_date or not reminder_time:
        return None
    try:
        return datetime.strptime(f"{due_date} {reminder_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def check_task_reminders(now: datetime = None) -> list:
    """Retorna tarefas que devem notificar agora e marca para evitar duplicidade."""
    tasks = _load()
    now = now or datetime.now()
    changed = False
    due_now = []

    for task in tasks:
        if task.get("status") != "pendente":
            continue

        due_dt = _parse_due_datetime(task)
        if not due_dt:
            continue

        remind_before = int(task.get("remind_before_minutes", 5) or 5)
        reminder_dt = due_dt - timedelta(minutes=remind_before)
        reminder_key = due_dt.strftime("%Y-%m-%d %H:%M")

        if task.get("last_reminder_for") == reminder_key:
            continue

        if reminder_dt <= now <= due_dt:
            task["last_reminder_for"] = reminder_key
            due_now.append(task)
            changed = True

    if changed:
        _save(tasks)
    return due_now

