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
                    app_name="Organizador Pessoal",
                    timeout=10,
                )
            except Exception as e:
                print(f"[Lembretes] Erro ao notificar '{bill['nome']}': {e}")
            notified.append({**bill, "days_left": days_left})
            sent_today.add(key)
            print(f"[Lembretes] Notificado: {bill['nome']} — {days_left} dia(s) restante(s).")
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
