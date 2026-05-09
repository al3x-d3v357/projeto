import csv
from datetime import date, datetime
from plyer import notification
from config import BILLS_FILE, BILL_REMINDER_DAYS


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


def check_bills() -> list:
    """
    Verifica as contas próximas do vencimento e dispara notificações desktop.
    Retorna lista de contas que foram notificadas.
    """
    bills = _read_bills()
    today = date.today()
    notified = []

    for bill in bills:
        try:
            due = datetime.strptime(bill["vencimento"].strip(), "%Y-%m-%d").date()
        except ValueError:
            print(f"[Lembretes] Data inválida para '{bill['nome']}': {bill['vencimento']}")
            continue

        days_left = (due - today).days

        if 0 <= days_left <= BILL_REMINDER_DAYS:
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
            print(f"[Lembretes] Notificado: {bill['nome']} — {days_left} dia(s) restante(s).")
        elif days_left < 0:
            print(f"[Lembretes] VENCIDA: {bill['nome']} ({abs(days_left)} dias atrás)")

    if not notified:
        print("[Lembretes] Nenhuma conta vencendo nos próximos "
              f"{BILL_REMINDER_DAYS} dias.")
    return notified


if __name__ == "__main__":
    check_bills()
