import json
import uuid
from datetime import datetime
from config import SHOPPING_FILE


def _load() -> list:
    try:
        with open(SHOPPING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(items: list) -> None:
    with open(SHOPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_item(name: str, quantity: str = "1") -> dict:
    items = _load()
    item = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "quantity": quantity,
        "checked": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items.append(item)
    _save(items)
    return item


def list_items() -> list:
    return _load()


def toggle_item(item_id: str) -> bool:
    items = _load()
    for i in items:
        if i["id"] == item_id:
            i["checked"] = not i.get("checked", False)
            _save(items)
            return True
    return False


def delete_item(item_id: str) -> bool:
    items = _load()
    new_items = [i for i in items if i["id"] != item_id]
    if len(new_items) == len(items):
        return False
    _save(new_items)
    return True


def clear_checked() -> int:
    items = _load()
    new_items = [i for i in items if not i.get("checked", False)]
    removed = len(items) - len(new_items)
    _save(new_items)
    return removed
