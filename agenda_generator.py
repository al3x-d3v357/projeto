import os
import csv
from datetime import date, datetime, timedelta
from task_manager import list_tasks
from config import BILLS_FILE, AGENDA_DIR

WEEKDAYS_PT = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def _week_range(reference: date) -> tuple[date, date]:
    """Retorna (segunda, domingo) da semana que contém `reference`."""
    start = reference - timedelta(days=reference.weekday())
    end = start + timedelta(days=6)
    return start, end


def _load_bills_this_week(start: date, end: date) -> list:
    bills = []
    try:
        with open(BILLS_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    due = datetime.strptime(row["vencimento"].strip(), "%Y-%m-%d").date()
                    if start <= due <= end:
                        bills.append({**row, "due_date": due})
                except ValueError:
                    pass
    except FileNotFoundError:
        pass
    return bills


def generate_agenda(reference: date = None) -> str:
    """
    Gera o arquivo de agenda semanal em AGENDA_DIR.
    Retorna o caminho do arquivo gerado.
    """
    if reference is None:
        reference = date.today()

    start, end = _week_range(reference)
    year, week_num, _ = start.isocalendar()
    filename = f"agenda_{year}-W{week_num:02d}.txt"
    filepath = os.path.join(AGENDA_DIR, filename)

    # Agrupa tarefas pendentes com due_date na semana
    tasks = list_tasks(status_filter="pendente")
    tasks_by_day: dict[date, list] = {}
    tasks_no_date = []

    for task in tasks:
        if task.get("due_date"):
            try:
                due = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
                if start <= due <= end:
                    tasks_by_day.setdefault(due, []).append(task)
                elif due < start:
                    tasks_no_date.append(task)  # vencidas
            except ValueError:
                tasks_no_date.append(task)
        else:
            tasks_no_date.append(task)

    bills = _load_bills_this_week(start, end)
    bills_by_day: dict[date, list] = {}
    for bill in bills:
        bills_by_day.setdefault(bill["due_date"], []).append(bill)

    lines = []
    lines.append("=" * 60)
    lines.append(f"  AGENDA SEMANAL — Semana {week_num}/{year}")
    lines.append(f"  {start.strftime('%d/%m/%Y')}  a  {end.strftime('%d/%m/%Y')}")
    lines.append("=" * 60)

    current = start
    while current <= end:
        day_name = WEEKDAYS_PT[current.weekday()]
        lines.append(f"\n{'─'*60}")
        lines.append(f"  {day_name.upper()} — {current.strftime('%d/%m/%Y')}")
        lines.append(f"{'─'*60}")

        day_tasks = tasks_by_day.get(current, [])
        day_bills = bills_by_day.get(current, [])

        if not day_tasks and not day_bills:
            lines.append("  (sem itens agendados)")
        else:
            if day_tasks:
                lines.append("  TAREFAS:")
                for t in day_tasks:
                    lines.append(f"    ○ [{t['id']}] {t['title']}")
            if day_bills:
                lines.append("  CONTAS A PAGAR:")
                for b in day_bills:
                    lines.append(f"    💳 {b['nome']} — R$ {b['valor']}")

        current += timedelta(days=1)

    if tasks_no_date:
        lines.append(f"\n{'─'*60}")
        lines.append("  TAREFAS SEM DATA / ATRASADAS")
        lines.append(f"{'─'*60}")
        for t in tasks_no_date:
            due_info = f"  [vence: {t['due_date']}]" if t.get("due_date") else ""
            lines.append(f"    ○ [{t['id']}] {t['title']}{due_info}")

    lines.append(f"\n{'='*60}")
    lines.append(f"  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    lines.append("=" * 60)

    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Agenda] Agenda gerada: {filepath}")
    return filepath


if __name__ == "__main__":
    generate_agenda()
