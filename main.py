import sys
import schedule
import time
import threading
from datetime import date

import task_manager
import bill_reminder
import file_organizer
import agenda_generator
import habits_manager
import shopping_list_manager
from config import (
    EMAIL_AUTOMATION_ENABLED,
    DRIVE_UPLOAD_ENABLED,
    SCHEDULER_EMAIL_INTERVAL_HOURS,
)


# ─── Scheduler em background ────────────────────────────────────────────────

def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)


def _setup_scheduler():
    """Define jobs automáticos periódicos."""
    schedule.every().day.at("08:00").do(bill_reminder.check_bills)
    schedule.every(30).minutes.do(lambda: habits_manager.check_habits_and_notify(verbose=False))
    if EMAIL_AUTOMATION_ENABLED:
        schedule.every(SCHEDULER_EMAIL_INTERVAL_HOURS).hours.do(_safe_read_emails)
    schedule.every().monday.at("07:00").do(agenda_generator.generate_agenda)
    t = threading.Thread(target=_run_scheduler, daemon=True)
    t.start()
    print("[Scheduler] Agendador iniciado em background.")
    if not EMAIL_AUTOMATION_ENABLED:
        print("[Scheduler] Leitura automática de e-mails desativada por configuração.")


def _safe_read_emails():
    if not EMAIL_AUTOMATION_ENABLED:
        return
    try:
        import email_reader
        result = email_reader.read_emails(verbose=False)
        if result.get("status") != "ok":
            return
        if DRIVE_UPLOAD_ENABLED and result["attachments_saved"]:
            import drive_uploader
            drive_uploader.upload_attachments(result["attachments_saved"])
    except Exception as e:
        print(f"[Scheduler] Erro ao ler e-mails: {e}")


# ─── Menus ────────────────────────────────────────────────────────────────────

def _print_header():
    print("\n" + "=" * 55)
    print("   ORGANIZADOR PESSOAL")
    print("=" * 55)


def _menu_tasks():
    while True:
        print("\n── Tarefas ──────────────────────────────")
        print("  1. Listar tarefas pendentes")
        print("  2. Listar todas as tarefas")
        print("  3. Adicionar tarefa manualmente")
        print("  4. Marcar tarefa como concluída")
        print("  5. Excluir tarefa")
        print("  0. Voltar")
        opt = input("  > ").strip()

        if opt == "1":
            print()
            task_manager.print_tasks("pendente")
        elif opt == "2":
            print()
            task_manager.print_tasks()
        elif opt == "3":
            title = input("  Título da tarefa: ").strip()
            if title:
                due = input("  Data de vencimento (YYYY-MM-DD) ou Enter para pular: ").strip() or None
                task = task_manager.add_task(title=title, due_date=due)
                print(f"  ✓ Tarefa criada: [{task['id']}] {task['title']}")
        elif opt == "4":
            task_manager.print_tasks("pendente")
            tid = input("  ID da tarefa: ").strip()
            if task_manager.complete_task(tid):
                print("  ✓ Tarefa concluída.")
            else:
                print("  Tarefa não encontrada.")
        elif opt == "5":
            task_manager.print_tasks()
            tid = input("  ID da tarefa a excluir: ").strip()
            if task_manager.delete_task(tid):
                print("  ✓ Tarefa excluída.")
            else:
                print("  Tarefa não encontrada.")
        elif opt == "0":
            break


def _menu_bills():
    print("\n── Lembretes de Contas ──────────────────")
    bill_reminder.check_bills()


def _menu_organizer():
    print("\n── Organizar Downloads ──────────────────")
    print("  1. Visualizar o que seria feito (sem mover)")
    print("  2. Organizar agora")
    print("  0. Voltar")
    opt = input("  > ").strip()
    if opt == "1":
        file_organizer.organize_downloads(dry_run=True)
    elif opt == "2":
        confirm = input("  Confirma mover arquivos da pasta Downloads? (s/N): ").strip().lower()
        if confirm == "s":
            file_organizer.organize_downloads()


def _menu_email():
    print("\n── Ler E-mails (Gmail) ──────────────────")
    try:
        import email_reader
        result = email_reader.read_emails()
        if result["attachments_saved"]:
            upload = input("  Enviar anexos ao Google Drive agora? (s/N): ").strip().lower()
            if upload == "s":
                import drive_uploader
                drive_uploader.upload_attachments(result["attachments_saved"])
    except ImportError as e:
        print(f"  Erro ao importar módulo: {e}")
    except Exception as e:
        print(f"  Erro: {e}")


def _menu_drive():
    print("\n── Upload para Google Drive ─────────────")
    try:
        import drive_uploader
        drive_uploader.upload_attachments()
    except Exception as e:
        print(f"  Erro: {e}")


def _menu_agenda():
    print("\n── Agenda Semanal ───────────────────────")
    print("  1. Gerar agenda da semana atual")
    print("  2. Gerar agenda de outra data")
    print("  0. Voltar")
    opt = input("  > ").strip()
    if opt == "1":
        path = agenda_generator.generate_agenda()
        print(f"  Arquivo: {path}")
    elif opt == "2":
        raw = input("  Data de referência (YYYY-MM-DD): ").strip()
        try:
            ref = date.fromisoformat(raw)
            path = agenda_generator.generate_agenda(ref)
            print(f"  Arquivo: {path}")
        except ValueError:
            print("  Data inválida.")


def _menu_habits():
    while True:
        print("\n── Hábitos ─────────────────────────────")
        print("  1. Listar hábitos")
        print("  2. Adicionar hábito")
        print("  3. Ativar/Pausar hábito")
        print("  4. Lembrar agora")
        print("  5. Excluir hábito")
        print("  0. Voltar")
        opt = input("  > ").strip()

        if opt == "1":
            habits = habits_manager.list_habits()
            if not habits:
                print("  Nenhum hábito cadastrado.")
            for h in habits:
                state = "ativo" if h.get("enabled", True) else "pausado"
                print(f"  ({h['id']}) {h['title']} — {h['interval_minutes']} min — {state}")
        elif opt == "2":
            title = input("  Hábito: ").strip()
            interval_raw = input("  Intervalo em minutos (ex: 120): ").strip() or "120"
            try:
                interval = int(interval_raw)
                habits_manager.add_habit(title, interval)
                print("  ✓ Hábito adicionado.")
            except ValueError:
                print("  Intervalo inválido.")
        elif opt == "3":
            hid = input("  ID do hábito: ").strip()
            if habits_manager.toggle_habit(hid):
                print("  ✓ Estado atualizado.")
            else:
                print("  Hábito não encontrado.")
        elif opt == "4":
            hid = input("  ID do hábito: ").strip()
            if habits_manager.send_habit_reminder_now(hid):
                print("  ✓ Lembrete enviado.")
            else:
                print("  Não foi possível enviar o lembrete.")
        elif opt == "5":
            hid = input("  ID do hábito: ").strip()
            if habits_manager.delete_habit(hid):
                print("  ✓ Hábito removido.")
            else:
                print("  Hábito não encontrado.")
        elif opt == "0":
            break


def _menu_shopping():
    while True:
        print("\n── Lista de Compras ────────────────────")
        print("  1. Listar itens")
        print("  2. Adicionar item")
        print("  3. Marcar/Desmarcar item")
        print("  4. Excluir item")
        print("  5. Limpar comprados")
        print("  0. Voltar")
        opt = input("  > ").strip()

        if opt == "1":
            items = shopping_list_manager.list_items()
            if not items:
                print("  Lista vazia.")
            for i in items:
                icon = "✓" if i.get("checked", False) else "○"
                print(f"  [{icon}] ({i['id']}) {i['name']} x{i.get('quantity', '1')}")
        elif opt == "2":
            name = input("  Item: ").strip()
            qty = input("  Quantidade: ").strip() or "1"
            if name:
                shopping_list_manager.add_item(name, qty)
                print("  ✓ Item adicionado.")
        elif opt == "3":
            iid = input("  ID do item: ").strip()
            if shopping_list_manager.toggle_item(iid):
                print("  ✓ Item atualizado.")
            else:
                print("  Item não encontrado.")
        elif opt == "4":
            iid = input("  ID do item: ").strip()
            if shopping_list_manager.delete_item(iid):
                print("  ✓ Item removido.")
            else:
                print("  Item não encontrado.")
        elif opt == "5":
            removed = shopping_list_manager.clear_checked()
            print(f"  ✓ {removed} item(ns) removido(s).")
        elif opt == "0":
            break


# ─── Loop principal ───────────────────────────────────────────────────────────

def main():
    _print_header()
    _setup_scheduler()

    while True:
        print("\n── Menu Principal ───────────────────────")
        print("  1. Tarefas")
        print("  2. Verificar contas a pagar")
        print("  3. Organizar pasta Downloads")
        print("  4. Ler e-mails e criar tarefas")
        print("  5. Upload de anexos para Google Drive")
        print("  6. Gerar agenda semanal")
        print("  7. Lembretes de hábitos")
        print("  8. Lista de compras")
        print("  0. Sair")
        opt = input("  > ").strip()

        if opt == "1":
            _menu_tasks()
        elif opt == "2":
            _menu_bills()
        elif opt == "3":
            _menu_organizer()
        elif opt == "4":
            _menu_email()
        elif opt == "5":
            _menu_drive()
        elif opt == "6":
            _menu_agenda()
        elif opt == "7":
            _menu_habits()
        elif opt == "8":
            _menu_shopping()
        elif opt == "0":
            print("\n  Encerrando. Até logo!")
            sys.exit(0)
        else:
            print("  Opção inválida.")


if __name__ == "__main__":
    main()
