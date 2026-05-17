import schedule
import time
import threading
import bill_reminder
import agenda_generator
import habits_manager
from ui import App


# ─── Scheduler em background ────────────────────────────────────────────────

def _run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)


def _setup_scheduler():
    """Define jobs automáticos periódicos."""
    schedule.every().day.at("08:00").do(bill_reminder.check_bills)
    schedule.every(30).minutes.do(lambda: habits_manager.check_habits_and_notify(verbose=False))
    schedule.every().monday.at("07:00").do(agenda_generator.generate_agenda)
    t = threading.Thread(target=_run_scheduler, daemon=True)
    t.start()
    print("[Scheduler] Agendador iniciado em background.")


def main():
    _setup_scheduler()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
