import json
import uuid
from datetime import datetime
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


def add_task(title: str, source: str = "manual", due_date: str = None) -> dict:
    """Adiciona uma nova tarefa. Retorna a tarefa criada."""
    tasks = _load()
    task = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "source": source,
        "status": "pendente",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "due_date": due_date,
    }
    tasks.append(task)
    _save(tasks)
    return task


def complete_task(task_id: str) -> bool:
    """Marca uma tarefa como concluída pelo ID. Retorna True se encontrada."""
    tasks = _load()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "concluída"
            task["completed_at"] = datetime.now().isoformat(timespec="seconds")
            _save(tasks)
            return True
    return False


def delete_task(task_id: str) -> bool:
    """Remove uma tarefa pelo ID. Retorna True se encontrada."""
    tasks = _load()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) == len(tasks):
        return False
    _save(new_tasks)
    return True


def list_tasks(status_filter: str = None) -> list:
    """Lista tarefas. Filtra por status se informado ('pendente' ou 'concluída')."""
    tasks = _load()
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
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
        print(f"  [{status_icon}] ({t['id']}) {t['title']}{due}  — origem: {t['source']}")
