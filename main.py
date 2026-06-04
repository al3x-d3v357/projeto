import schedule
import time
import threading
import agenda_generator
import habits_manager
import task_manager
import shopping_list_manager
import bill_reminder
from ui import App


# ─── Scheduler em background ────────────────────────────────────────────────

def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)


def _setup_scheduler():
    """Define jobs automáticos periódicos."""
    schedule.every(30).minutes.do(lambda: habits_manager.check_habits_and_notify(verbose=False))
    schedule.every().monday.at("07:00").do(agenda_generator.generate_agenda)
    t = threading.Thread(target=_run_scheduler, daemon=True)
    t.start()
    print("[Scheduler] Agendador iniciado em background.")


def main():
    # Sincronização inicial com o Supabase (roda em background thread internamente)
    print("[Supabase] Iniciando sincronização global...")
    task_manager.sync_with_supabase()
    habits_manager.sync_with_supabase()
    shopping_list_manager.sync_with_supabase()
    bill_reminder.sync_with_supabase()

    _setup_scheduler()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
