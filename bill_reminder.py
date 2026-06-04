import csv
import json
import os
from datetime import date, datetime
from plyer import notification
from config import BILLS_FILE, BILL_REMINDER_DAYS, REMINDER_HISTORY_FILE


def _read_bills() -> list:
    bills = []
    try:
        with open(BILLS_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bills.append(row)
    except FileNotFoundError:
        print(f"[Lembretes] Arquivo não encontrado: {BILLS_FILE}")
    return bills


def _load_history() -> dict:
    try:
        with open(REMINDER_HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {}


def _save_history(history: dict) -> None:
    with open(REMINDER_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _bill_key(bill: dict) -> str:
    return f"{bill.get('nome', '')}|{bill.get('valor', '')}|{bill.get('vencimento', '')}"


# ── Tradução de Modelos ──────────────────────────────────────────────────────

def _to_local(remote: dict) -> dict:
    val = float(remote.get("value") or 0.0)
    return {
        "id": str(remote["id"]),
        "nome": remote["name"],
        "valor": f"{val:.2f}",
        "vencimento": str(remote["due_date"])
    }


def _to_remote(local: dict) -> dict:
    val_str = local.get("valor", "0.00").replace(",", ".")
    try:
        val = float(val_str)
    except ValueError:
        val = 0.0
    return {
        "name": local["nome"],
        "value": val,
        "due_date": local["vencimento"]
    }


# ── Sincronização Supabase ───────────────────────────────────────────────────

def _bg_insert_history(notified_date, bill_id):
    from supabase_client import supabase
    if supabase:
        try:
            supabase.table("reminder_history").insert({
                "notified_date": notified_date,
                "bill_id": bill_id
            }).execute()
        except Exception as e:
            print(f"[Supabase Error] Falha ao registrar histórico de lembrete: {e}")


def sync_with_supabase():
    """Busca as contas e o histórico de lembretes do Supabase para atualizar o cache local, ou faz upload se estiver vazio."""
    from supabase_client import supabase, run_in_background
    if not supabase:
        return

    def _sync():
        try:
            # 1. Sincroniza Contas (bills)
            res_bills = supabase.table("bills").select("*").execute()
            remote_bills = res_bills.data
            if remote_bills:
                fieldnames = ["id", "nome", "valor", "vencimento"]
                with open(BILLS_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for b in remote_bills:
                        row = _to_local(b)
                        writer.writerow(row)
                print("[Sync Bills] Contas sincronizadas do Supabase para bills.csv.")
            else:
                local_bills = _read_bills()
                if local_bills:
                    print("[Sync Bills] Supabase está vazio. Enviando contas locais...")
                    upload_list = [_to_remote(b) for b in local_bills]
                    res_insert = supabase.table("bills").insert(upload_list).execute()
                    if res_insert.data:
                        fieldnames = ["id", "nome", "valor", "vencimento"]
                        with open(BILLS_FILE, "w", newline="", encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            for i, b in enumerate(local_bills):
                                if i < len(res_insert.data):
                                    b["id"] = str(res_insert.data[i]["id"])
                                writer.writerow(b)
                    print("[Sync Bills] Contas locais enviadas com sucesso.")

            # 2. Sincroniza Histórico de Lembretes (reminder_history) com JOIN
            res_hist = supabase.table("reminder_history").select("notified_date, bills(name, value, due_date)").execute()
            remote_hist = res_hist.data
            if remote_hist:
                local_history = {}
                for h in remote_hist:
                    date_key = h.get("notified_date")
                    bill_info = h.get("bills")
                    if date_key and bill_info:
                        if isinstance(bill_info, dict):
                            val = float(bill_info.get("value") or 0.0)
                            b_key = f"{bill_info.get('name', '')}|{val:.2f}|{bill_info.get('due_date', '')}"
                            local_history.setdefault(date_key, []).append(b_key)
                _save_history(local_history)
                print("[Sync Bills] Histórico de lembretes sincronizado do Supabase.")
            else:
                local_history = _load_history()
                if local_history:
                    print("[Sync Bills] Histórico remoto vazio. Enviando histórico local...")
                    local_bills = _read_bills()
                    key_to_id = {}
                    for b in local_bills:
                        if b.get("id"):
                            try:
                                val = float(b["valor"])
                                val_str = f"{val:.2f}"
                            except ValueError:
                                val_str = b["valor"]
                            k = f"{b['nome']}|{val_str}|{b['vencimento']}"
                            key_to_id[k] = int(b["id"])

                    upload_hist = []
                    for date_key, keys in local_history.items():
                        for k in keys:
                            parts = k.split("|")
                            if len(parts) == 3:
                                try:
                                    val = float(parts[1])
                                    parts[1] = f"{val:.2f}"
                                except ValueError:
                                    pass
                                normalized_k = "|".join(parts)
                            else:
                                normalized_k = k

                            bid = key_to_id.get(normalized_k)
                            if bid:
                                upload_hist.append({
                                    "notified_date": date_key,
                                    "bill_id": bid
                                })
                    if upload_hist:
                        supabase.table("reminder_history").insert(upload_hist).execute()
                        print("[Sync Bills] Histórico local enviado com sucesso.")
        except Exception as e:
            print(f"[Sync Bills] Falha na sincronização: {e}")

    run_in_background(_sync)


# ── CRUD e Métodos ──────────────────────────────────────────────────────────

def check_bills() -> list:
    """
    Verifica as contas próximas do vencimento e dispara notificações desktop.
    Retorna lista de contas que foram notificadas.
    """
    bills = _read_bills()
    today = date.today()
    today_key = today.isoformat()
    history = _load_history()
    sent_today = set(history.get(today_key, []))
    notified = []

    for bill in bills:
        try:
            due = datetime.strptime(bill["vencimento"].strip(), "%Y-%m-%d").date()
        except ValueError:
            print(f"[Lembretes] Data inválida para '{bill['nome']}': {bill['vencimento']}")
            continue

        days_left = (due - today).days

        if 0 <= days_left <= BILL_REMINDER_DAYS:
            key = _bill_key(bill)
            if key in sent_today:
                print(f"[Lembretes] Já notificado hoje: {bill['nome']}")
                continue

            msg = (
                f"Vence em {days_left} dia(s): {due.strftime('%d/%m/%Y')}\n"
                f"Valor: R$ {bill['valor']}"
            )
            try:
                notification.notify(
                    title=f"💳 Conta: {bill['nome']}",
                    message=msg,
                    app_name="Task Flow",
                    timeout=10,
                )
            except Exception as e:
                print(f"[Lembretes] Erro ao notificar '{bill['nome']}': {e}")
            notified.append({**bill, "days_left": days_left})
            sent_today.add(key)
            print(f"[Lembretes] Notificado: {bill['nome']} — {days_left} dia(s) restante(s).")
            
            # Sincroniza em background
            bill_id = bill.get("id")
            if bill_id and bill_id.isdigit():
                from supabase_client import run_in_background
                run_in_background(_bg_insert_history, today_key, int(bill_id))
        elif days_left < 0:
            print(f"[Lembretes] VENCIDA: {bill['nome']} ({abs(days_left)} dias atrás)")

    if not notified:
        print("[Lembretes] Nenhuma conta vencendo nos próximos "
              f"{BILL_REMINDER_DAYS} dias.")

    # Mantém apenas o histórico dos últimos 30 dias para não crescer indefinidamente.
    history[today_key] = sorted(sent_today)
    cutoff = today.toordinal() - 30
    compact_history = {}
    for day, keys in history.items():
        try:
            if date.fromisoformat(day).toordinal() >= cutoff:
                compact_history[day] = keys
        except ValueError:
            continue
    _save_history(compact_history)

    return notified


if __name__ == "__main__":
    check_bills()

