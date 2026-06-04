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


# ── Sincronização Supabase ───────────────────────────────────────────────────

def _bg_insert(item):
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("shopping_list").insert(item).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao inserir item de compra: {e}")


def _bg_update(item_id, data):
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("shopping_list").update(data).eq("id", item_id).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao atualizar item de compra: {e}")


def _bg_delete(item_id):
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("shopping_list").delete().eq("id", item_id).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao excluir item de compra: {e}")


def sync_with_supabase():
    """Busca itens do Supabase para atualizar o cache local, ou envia o cache se a nuvem estiver vazia."""
    from supabase_client import supabase, run_in_background
    if not supabase:
        return

    def _sync():
        try:
            res = supabase.table("shopping_list").select("*").execute()
            remote_items = res.data
            if remote_items:
                _save(remote_items)
                print("[Sync Shopping] Sincronizado do Supabase para o cache local.")
            else:
                local_items = _load()
                if local_items:
                    print("[Sync Shopping] Supabase está vazio. Enviando dados locais...")
                    supabase.table("shopping_list").insert(local_items).execute()
                    print("[Sync Shopping] Dados locais enviados com sucesso.")
        except Exception as e:
            print(f"[Sync Shopping] Falha na sincronização: {e}")

    run_in_background(_sync)


# ── CRUD e Métodos ──────────────────────────────────────────────────────────

def add_item(name: str, quantity: str = "1", price: str = "0,00") -> dict:
    items = _load()
    item = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "quantity": quantity,
        "price": price,
        "checked": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items.append(item)
    _save(items)

    from supabase_client import run_in_background
    run_in_background(_bg_insert, item)

    return item


def list_items() -> list:
    return _load()


def toggle_item(item_id: str) -> bool:
    items = _load()
    for i in items:
        if i["id"] == item_id:
            i["checked"] = not i.get("checked", False)
            _save(items)

            from supabase_client import run_in_background
            run_in_background(_bg_update, item_id, {"checked": i["checked"]})
            return True
    return False


def delete_item(item_id: str) -> bool:
    items = _load()
    new_items = [i for i in items if i["id"] != item_id]
    if len(new_items) == len(items):
        return False
    _save(new_items)

    from supabase_client import run_in_background
    run_in_background(_bg_delete, item_id)

    return True


def clear_checked() -> int:
    items = _load()
    checked_items = [i for i in items if i.get("checked", False)]
    new_items = [i for i in items if not i.get("checked", False)]
    removed = len(items) - len(new_items)
    _save(new_items)

    from supabase_client import run_in_background
    for i in checked_items:
        run_in_background(_bg_delete, i["id"])

    return removed

