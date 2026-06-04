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


# ── Tradução de Modelos ──────────────────────────────────────────────────────

def _to_local(remote: dict) -> dict:
    qty = str(remote.get("quantity") or 1)
    if qty.endswith(".0"):
        qty = qty[:-2]
    price_val = float(remote.get("price") or 0.0)
    price_str = f"{price_val:.2f}".replace(".", ",")
    return {
        "id": str(remote["id"]),
        "name": remote["item_name"],
        "quantity": qty,
        "price": price_str,
        "checked": bool(remote.get("is_bought", False)),
        "created_at": remote.get("created_at") or datetime.now().isoformat(timespec="seconds")
    }


def _to_remote(local: dict) -> dict:
    qty_str = local.get("quantity", "1").replace(",", ".")
    try:
        qty = float(qty_str)
        if qty.is_integer():
            qty = int(qty)
    except ValueError:
        qty = 1

    price_str = local.get("price", "0,00").replace(".", "").replace(",", ".")
    try:
        price = float(price_str)
    except ValueError:
        price = 0.0

    return {
        "item_name": local["name"],
        "quantity": qty,
        "price": price,
        "is_bought": bool(local.get("checked", False)),
        "created_at": local.get("created_at")
    }


# ── Sincronização Supabase ───────────────────────────────────────────────────

def _bg_insert(item, local_id):
    from supabase_client import supabase
    if supabase:
        try:
            row = _to_remote(item)
            res = supabase.table("shopping_list").insert(row).execute()
            if res.data:
                remote_id = str(res.data[0]["id"])
                # Atualiza o ID local
                items = _load()
                for i in items:
                    if i["id"] == local_id:
                        i["id"] = remote_id
                _save(items)
        except Exception as e:
            print(f"[Supabase Error] Falha ao inserir item de compra: {e}")


def _bg_update(item_id, data):
    if not item_id.isdigit():
        return
    from supabase_client import supabase
    if supabase:
        try:
            remote_data = {}
            if "name" in data:
                remote_data["item_name"] = data["name"]
            if "quantity" in data:
                qty_str = str(data["quantity"]).replace(",", ".")
                try:
                    qty = float(qty_str)
                    if qty.is_integer():
                        qty = int(qty)
                except ValueError:
                    qty = 1
                remote_data["quantity"] = qty
            if "price" in data:
                price_str = str(data["price"]).replace(".", "").replace(",", ".")
                try:
                    price = float(price_str)
                except ValueError:
                    price = 0.0
                remote_data["price"] = price
            if "checked" in data:
                remote_data["is_bought"] = bool(data["checked"])
            if remote_data:
                supabase.table("shopping_list").update(remote_data).eq("id", int(item_id)).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao atualizar item de compra: {e}")


def _bg_delete(item_id):
    if not item_id.isdigit():
        return
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("shopping_list").delete().eq("id", int(item_id)).execute()
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
                local_format_items = [_to_local(i) for i in remote_items]
                _save(local_format_items)
                print("[Sync Shopping] Sincronizado do Supabase para o cache local.")
            else:
                local_items = _load()
                if local_items:
                    print("[Sync Shopping] Supabase está vazio. Enviando dados locais...")
                    upload_list = [_to_remote(i) for i in local_items]
                    res_insert = supabase.table("shopping_list").insert(upload_list).execute()
                    if res_insert.data:
                        for i, inserted in enumerate(res_insert.data):
                            if i < len(local_items):
                                local_items[i]["id"] = str(inserted["id"])
                        _save(local_items)
                    print("[Sync Shopping] Dados locais enviados com sucesso.")
        except Exception as e:
            print(f"[Sync Shopping] Falha na sincronização: {e}")

    run_in_background(_sync)


# ── CRUD e Métodos ──────────────────────────────────────────────────────────

def add_item(name: str, quantity: str = "1", price: str = "0,00") -> dict:
    items = _load()
    local_id = str(uuid.uuid4())[:8]
    item = {
        "id": local_id,
        "name": name,
        "quantity": quantity,
        "price": price,
        "checked": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    items.append(item)
    _save(items)

    from supabase_client import run_in_background
    run_in_background(_bg_insert, item, local_id)

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

