import customtkinter as ctk
from datetime import date
import threading

import task_manager
import bill_reminder
import file_organizer
import agenda_generator

# ── Tema global ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SIDEBAR_W = 200
BG_DARK   = "#1a1a2e"
BG_CARD   = "#16213e"
ACCENT    = "#0f3460"
ACCENT2   = "#e94560"
TEXT_SEC  = "#a0aec0"

# ── Janela principal ─────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Organizador Pessoal")
        self.geometry("1000x660")
        self.minsize(900, 600)
        self.configure(fg_color=BG_DARK)

        self._build_sidebar()
        self._build_frames()
        self._show_frame("tarefas")

    # ── Sidebar ──────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=SIDEBAR_W, fg_color=BG_CARD, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar, text="⚡ Organizador", font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        ).pack(pady=(28, 24), padx=16)

        self._nav_buttons = {}
        nav_items = [
            ("tarefas",    "✅  Tarefas"),
            ("contas",     "💳  Contas"),
            ("downloads",  "📁  Downloads"),
            ("emails",     "📧  E-mails"),
            ("agenda",     "📅  Agenda"),
        ]
        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label, anchor="w",
                fg_color="transparent", hover_color=ACCENT,
                font=ctk.CTkFont(size=13), height=40,
                command=lambda k=key: self._show_frame(k),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[key] = btn

    def _highlight_nav(self, active_key: str):
        for key, btn in self._nav_buttons.items():
            btn.configure(fg_color=ACCENT if key == active_key else "transparent")

    # ── Frames ────────────────────────────────────────────────────────────────
    def _build_frames(self):
        self.main_area = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

        self.frames = {
            "tarefas":   TarefasFrame(self.main_area),
            "contas":    ContasFrame(self.main_area),
            "downloads": DownloadsFrame(self.main_area),
            "emails":    EmailsFrame(self.main_area),
            "agenda":    AgendaFrame(self.main_area),
        }
        for frame in self.frames.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _show_frame(self, key: str):
        self.frames[key].tkraise()
        self._highlight_nav(key)
        if hasattr(self.frames[key], "on_show"):
            self.frames[key].on_show()


# ── Componentes reutilizáveis ─────────────────────────────────────────────────
def section_title(parent, text):
    ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=20, weight="bold"),
                 text_color="white").pack(anchor="w", padx=28, pady=(24, 4))

def status_label(parent):
    lbl = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=12), text_color=TEXT_SEC)
    lbl.pack(anchor="w", padx=28, pady=(0, 10))
    return lbl

def action_btn(parent, text, command, color=None):
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=color or ACCENT2, hover_color="#c73652",
        font=ctk.CTkFont(size=13, weight="bold"),
        height=36, corner_radius=8,
    )

def card_frame(parent):
    return ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)


# ── Frame: Tarefas ────────────────────────────────────────────────────────────
class TarefasFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        section_title(self, "✅  Tarefas")

        # Entrada de nova tarefa
        card = card_frame(self)
        card.pack(fill="x", padx=24, pady=(0, 16))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        self._entry = ctk.CTkEntry(row, placeholder_text="Nova tarefa...",
                                   height=36, font=ctk.CTkFont(size=13))
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._due = ctk.CTkEntry(row, placeholder_text="Vencimento (YYYY-MM-DD)",
                                  width=180, height=36, font=ctk.CTkFont(size=13))
        self._due.pack(side="left", padx=(0, 8))

        action_btn(row, "+ Adicionar", self._add_task).pack(side="left")

        # Lista de tarefas
        self._list_frame = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._list_frame.pack(fill="both", expand=True, padx=24)

        self._refresh_list()

    def _refresh_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        tasks = task_manager.list_tasks()
        if not tasks:
            ctk.CTkLabel(self._list_frame, text="Nenhuma tarefa cadastrada.",
                         text_color=TEXT_SEC).pack(pady=20)
            return

        for task in tasks:
            self._task_row(task)

    def _task_row(self, task):
        row = ctk.CTkFrame(self._list_frame, fg_color=BG_CARD, corner_radius=8, height=48)
        row.pack(fill="x", pady=4)
        row.pack_propagate(False)

        done = task["status"] == "concluída"
        color = "#4ade80" if done else ACCENT2
        icon  = "✓" if done else "○"

        ctk.CTkLabel(row, text=icon, text_color=color,
                     font=ctk.CTkFont(size=16, weight="bold"), width=30).pack(side="left", padx=(12, 0))

        title = task["title"]
        if task.get("due_date"):
            title += f"   [vence: {task['due_date']}]"
        ctk.CTkLabel(row, text=title, text_color="white" if not done else TEXT_SEC,
                     font=ctk.CTkFont(size=13), anchor="w").pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkLabel(row, text=task["source"], text_color=TEXT_SEC,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=8)

        if not done:
            ctk.CTkButton(row, text="Concluir", width=70, height=28,
                          fg_color="#16a34a", hover_color="#15803d",
                          font=ctk.CTkFont(size=11),
                          command=lambda tid=task["id"]: self._complete(tid)
                          ).pack(side="left", padx=4)

        ctk.CTkButton(row, text="✕", width=30, height=28,
                      fg_color="#374151", hover_color="#6b7280",
                      font=ctk.CTkFont(size=11),
                      command=lambda tid=task["id"]: self._delete(tid)
                      ).pack(side="left", padx=(0, 10))

    def _add_task(self):
        title = self._entry.get().strip()
        due   = self._due.get().strip() or None
        if not title:
            return
        task_manager.add_task(title=title, due_date=due)
        self._entry.delete(0, "end")
        self._due.delete(0, "end")
        self._refresh_list()

    def _complete(self, tid):
        task_manager.complete_task(tid)
        self._refresh_list()

    def _delete(self, tid):
        task_manager.delete_task(tid)
        self._refresh_list()


# ── Frame: Contas ─────────────────────────────────────────────────────────────
class ContasFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        section_title(self, "💳  Contas a Pagar")
        self._status = status_label(self)

        action_btn(self, "🔔  Verificar e notificar", self._check,
                   color="#7c3aed").pack(anchor="w", padx=28, pady=(0, 16))

        import csv
        from config import BILLS_FILE
        today = date.today()

        scroll = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=24)

        try:
            with open(BILLS_FILE, newline="", encoding="utf-8") as f:
                bills = list(csv.DictReader(f))
        except FileNotFoundError:
            ctk.CTkLabel(scroll, text="bills.csv não encontrado.", text_color=TEXT_SEC).pack()
            return

        from datetime import datetime
        for bill in bills:
            try:
                due = datetime.strptime(bill["vencimento"].strip(), "%Y-%m-%d").date()
            except ValueError:
                continue

            days_left = (due - today).days
            if days_left < 0:
                color, tag = "#ef4444", "VENCIDA"
            elif days_left <= 3:
                color, tag = "#f59e0b", f"{days_left}d restante(s)"
            else:
                color, tag = "#4ade80", f"{days_left}d restante(s)"

            row = ctk.CTkFrame(scroll, fg_color=BG_CARD, corner_radius=8, height=52)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)

            ctk.CTkFrame(row, fg_color=color, width=4, corner_radius=2).pack(side="left", fill="y", padx=(0, 12))
            ctk.CTkLabel(row, text=bill["nome"], font=ctk.CTkFont(size=13, weight="bold"),
                         text_color="white").pack(side="left")
            ctk.CTkLabel(row, text=f"R$ {bill['valor']}", text_color=TEXT_SEC,
                         font=ctk.CTkFont(size=13)).pack(side="left", padx=16)
            ctk.CTkLabel(row, text=due.strftime("%d/%m/%Y"), text_color=TEXT_SEC,
                         font=ctk.CTkFont(size=12)).pack(side="left")
            ctk.CTkLabel(row, text=tag, text_color=color,
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=16)

    def _check(self):
        self._status.configure(text="Verificando...")
        def run():
            notified = bill_reminder.check_bills()
            msg = f"{len(notified)} notificação(ões) enviada(s)." if notified else "Nenhuma conta vencendo em breve."
            self.after(0, lambda: self._status.configure(text=msg))
        threading.Thread(target=run, daemon=True).start()


# ── Frame: Downloads ──────────────────────────────────────────────────────────
class DownloadsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)
        self._built = False

    def on_show(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        section_title(self, "📁  Organizar Downloads")
        self._status = status_label(self)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(anchor="w", padx=28, pady=(0, 16))
        action_btn(btns, "👁  Pré-visualizar", self._preview, color=ACCENT).pack(side="left", padx=(0, 10))
        action_btn(btns, "🚀  Organizar agora", self._organize).pack(side="left")

        self._log = ctk.CTkTextbox(self, state="disabled", fg_color=BG_CARD,
                                    font=ctk.CTkFont(family="Consolas", size=12),
                                    corner_radius=10)
        self._log.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _log_write(self, text):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _preview(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._status.configure(text="Simulando...")
        def run():
            import io, sys
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            file_organizer.organize_downloads(dry_run=True)
            sys.stdout = old
            output = buf.getvalue()
            self.after(0, lambda: self._log_write(output))
            self.after(0, lambda: self._status.configure(text="Pré-visualização concluída."))
        threading.Thread(target=run, daemon=True).start()

    def _organize(self):
        self._status.configure(text="Organizando...")
        def run():
            import io, sys
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            file_organizer.organize_downloads(dry_run=False)
            sys.stdout = old
            output = buf.getvalue()
            self.after(0, lambda: self._log_write(output))
            self.after(0, lambda: self._status.configure(text="Concluído."))
        threading.Thread(target=run, daemon=True).start()


# ── Frame: E-mails ────────────────────────────────────────────────────────────
class EmailsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)
        self._built = False

    def on_show(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        section_title(self, "📧  E-mails (Gmail)")
        self._status = status_label(self)

        info = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=10)
        info.pack(fill="x", padx=24, pady=(0, 16))
        ctk.CTkLabel(
            info,
            text="Coloque credentials.json em  credentials/  para ativar esta função.\n"
                 "Palavras-chave monitoradas: urgente · prazo · confirmar · responder · pendente",
            text_color=TEXT_SEC, font=ctk.CTkFont(size=12), justify="left"
        ).pack(padx=16, pady=12)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(anchor="w", padx=28, pady=(0, 16))
        action_btn(btns, "📬  Ler e-mails", self._read).pack(side="left", padx=(0, 10))
        action_btn(btns, "☁  Upload Drive", self._upload, color="#0369a1").pack(side="left")

        self._log = ctk.CTkTextbox(self, state="disabled", fg_color=BG_CARD,
                                    font=ctk.CTkFont(family="Consolas", size=12),
                                    corner_radius=10)
        self._log.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _log_write(self, text):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _read(self):
        self._status.configure(text="Conectando ao Gmail...")
        def run():
            import io, sys
            buf = io.StringIO()
            old = sys.stdout; sys.stdout = buf
            try:
                import email_reader
                email_reader.read_emails()
            except Exception as e:
                print(f"Erro: {e}")
            sys.stdout = old
            output = buf.getvalue()
            self.after(0, lambda: self._log_write(output))
            self.after(0, lambda: self._status.configure(text="Concluído."))
        threading.Thread(target=run, daemon=True).start()

    def _upload(self):
        self._status.configure(text="Enviando ao Drive...")
        def run():
            import io, sys
            buf = io.StringIO()
            old = sys.stdout; sys.stdout = buf
            try:
                import drive_uploader
                drive_uploader.upload_attachments()
            except Exception as e:
                print(f"Erro: {e}")
            sys.stdout = old
            output = buf.getvalue()
            self.after(0, lambda: self._log_write(output))
            self.after(0, lambda: self._status.configure(text="Concluído."))
        threading.Thread(target=run, daemon=True).start()


# ── Frame: Agenda ─────────────────────────────────────────────────────────────
class AgendaFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)
        self._built = False

    def on_show(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        section_title(self, "📅  Agenda Semanal")
        self._status = status_label(self)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", padx=28, pady=(0, 16))

        action_btn(row, "⚡  Gerar semana atual", self._generate_current).pack(side="left", padx=(0, 10))

        self._date_entry = ctk.CTkEntry(row, placeholder_text="Outra data (YYYY-MM-DD)",
                                         width=200, height=36, font=ctk.CTkFont(size=13))
        self._date_entry.pack(side="left", padx=(0, 8))
        action_btn(row, "Gerar", self._generate_custom, color=ACCENT).pack(side="left")

        self._textbox = ctk.CTkTextbox(self, state="disabled", fg_color=BG_CARD,
                                        font=ctk.CTkFont(family="Consolas", size=12),
                                        corner_radius=10)
        self._textbox.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _show_file(self, filepath: str):
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"Erro ao abrir arquivo: {e}"
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", content)
        self._textbox.configure(state="disabled")
        self._status.configure(text=f"Gerado: {filepath}")

    def _generate_current(self):
        def run():
            path = agenda_generator.generate_agenda()
            self.after(0, lambda: self._show_file(path))
        threading.Thread(target=run, daemon=True).start()

    def _generate_custom(self):
        raw = self._date_entry.get().strip()
        try:
            ref = date.fromisoformat(raw)
        except ValueError:
            self._status.configure(text="Data inválida. Use YYYY-MM-DD.")
            return
        def run():
            path = agenda_generator.generate_agenda(ref)
            self.after(0, lambda: self._show_file(path))
        threading.Thread(target=run, daemon=True).start()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
