import customtkinter as ctk
from datetime import date, datetime, timedelta
import threading
from tkinter import filedialog
from plyer import notification

import task_manager
import file_organizer
import agenda_generator
import habits_manager
import shopping_list_manager
import accessibility

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
        self.title("Task Flow")
        self.geometry("1000x660")
        self.minsize(900, 600)
        self.configure(fg_color=BG_DARK)

        # Aplica configurações de acessibilidade antes de construir a UI
        accessibility.get_manager().apply_all()

        self._build_sidebar()
        self._build_frames()
        self._start_habits_loop()
        self._start_task_reminders_loop()
        self._show_frame("tarefas")
        self._accessibility_win = None

    def _start_habits_loop(self):
        def run():
            while True:
                try:
                    habits_manager.check_habits_and_notify(verbose=False)
                except Exception:
                    pass
                # Verifica hábitos uma vez por minuto
                import time
                time.sleep(60)
        threading.Thread(target=run, daemon=True).start()

    def _start_task_reminders_loop(self):
        def run():
            import time
            while True:
                try:
                    due_tasks = task_manager.check_task_reminders()
                    for task in due_tasks:
                        notification.notify(
                            title=f"⏰ Tarefa em breve: {task['title']}",
                            message=(
                                f"Faltam {task.get('remind_before_minutes', 5)} min. "
                                f"Horário: {task.get('reminder_time', '--:--')}"
                            ),
                            app_name="Task Flow",
                            timeout=10,
                        )
                except Exception:
                    pass
                time.sleep(30)

        threading.Thread(target=run, daemon=True).start()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=SIDEBAR_W, fg_color=BG_CARD, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        ctk.CTkLabel(
            self.sidebar, text="⚡ Task Flow", font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        ).pack(pady=(28, 24), padx=16)

        self._nav_buttons = {}
        nav_items = [
            ("tarefas",    "✅  Tarefas"),
            ("downloads",  "📁  Downloads"),
            ("agenda",     "📅  Agenda"),
            ("habitos",    "⏰  Hábitos"),
            ("compras",    "🛒  Compras"),
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

        # Botão de acessibilidade fixado no rodapé da sidebar
        ctk.CTkButton(
            self.sidebar, text="♿  Acessibilidade", anchor="w",
            fg_color="transparent", hover_color="#2d3748",
            font=ctk.CTkFont(size=12), height=36,
            command=self._open_accessibility,
        ).pack(side="bottom", fill="x", padx=10, pady=(0, 12))

    def _highlight_nav(self, active_key: str):
        for key, btn in self._nav_buttons.items():
            btn.configure(fg_color=ACCENT if key == active_key else "transparent")

    # ── Frames ────────────────────────────────────────────────────────────────
    def _build_frames(self):
        self.main_area = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        self.main_area.pack(side="left", fill="both", expand=True)

        self.frames = {
            "tarefas":   TarefasFrame(self.main_area),
            "downloads": DownloadsFrame(self.main_area),
            "agenda":    AgendaFrame(self.main_area),
            "habitos":   HabitosFrame(self.main_area),
            "compras":   ComprasFrame(self.main_area),
        }
        for frame in self.frames.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _open_accessibility(self):
        if self._accessibility_win and self._accessibility_win.winfo_exists():
            self._accessibility_win.focus()
            return
        self._accessibility_win = AccessibilityWindow(self)

    def _show_frame(self, key: str):
        self.frames[key].tkraise()
        self._highlight_nav(key)
        if hasattr(self.frames[key], "on_show"):
            self.frames[key].on_show()
        _section_names = {
            "tarefas": "Tarefas",
            "downloads": "Organizar Downloads",
            "agenda": "Agenda Semanal",
            "habitos": "Lembretes de Hábitos",
            "compras": "Lista de Compras",
        }
        accessibility.get_manager().speak(_section_names.get(key, key))


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


def send_section_reminder(section_name: str) -> bool:
    try:
        notification.notify(
            title=f"🔔 Lembrete: {section_name}",
            message=f"Você tem atividades pendentes em {section_name}.",
            app_name="Task Flow",
            timeout=8,
        )
        return True
    except Exception:
        return False


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
        self._status = status_label(self)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkLabel(controls, text="Filtro:", text_color=TEXT_SEC).pack(side="left", padx=(0, 8))
        self._filter_var = ctk.StringVar(value="Pendentes")
        self._filter_menu = ctk.CTkOptionMenu(
            controls,
            values=["Todas", "Pendentes", "Concluídas", "Sem data", "Vencidas", "Hoje", "Próx. 7 dias"],
            variable=self._filter_var,
            command=lambda _: self._refresh_list(),
            width=150,
        )
        self._filter_menu.pack(side="left", padx=(0, 12))

        self._sort_switch = ctk.CTkSwitch(
            controls,
            text="Ordenar por vencimento",
            command=self._refresh_list,
        )
        self._sort_switch.select()
        self._sort_switch.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            controls,
            text="Atualizar",
            width=90,
            height=30,
            fg_color=ACCENT,
            hover_color="#0b2747",
            command=self._refresh_list,
        ).pack(side="left")

        ctk.CTkButton(
            controls,
            text="🔔 Lembrete",
            width=110,
            height=30,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self._send_reminder,
        ).pack(side="left", padx=(10, 0))

        # Entrada de nova tarefa
        card = card_frame(self)
        card.pack(fill="x", padx=24, pady=(0, 16))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        self._entry = ctk.CTkEntry(row, placeholder_text="Nova tarefa...",
                                   height=36, font=ctk.CTkFont(size=13))
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._due_options = self._build_due_options()
        self._due_var = ctk.StringVar(value=self._due_options[0])
        self._due_menu = ctk.CTkOptionMenu(
            row,
            values=self._due_options,
            variable=self._due_var,
            command=self._on_due_change,
            width=190,
        )
        self._due_menu.pack(side="left", padx=(0, 8))

        self._time_options = ["Sem horario"] + [
            f"{hour:02d}:{minute:02d}"
            for hour in range(24)
            for minute in range(0, 60, 5)
        ]
        self._time_var = ctk.StringVar(value="Sem horario")
        self._time_menu = ctk.CTkOptionMenu(
            row,
            values=self._time_options,
            variable=self._time_var,
            width=120,
            state="disabled",
        )
        self._time_menu.pack(side="left", padx=(0, 8))

        self._add_btn = action_btn(row, "+ Adicionar", self._add_task)
        self._add_btn.pack(side="left")

        # Lista de tarefas
        self._list_frame = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._list_frame.pack(fill="both", expand=True, padx=24)

        self._refresh_list()

    def _build_due_options(self) -> list:
        self._due_label_to_iso = {"Sem data": None}
        options = ["Sem data"]
        for offset in range(0, 15):
            d = date.today() + timedelta(days=offset)
            if offset == 0:
                label = f"Hoje ({d.strftime('%d/%m/%Y')})"
            elif offset == 1:
                label = f"Amanha ({d.strftime('%d/%m/%Y')})"
            else:
                label = f"+{offset} dias ({d.strftime('%d/%m/%Y')})"
            options.append(label)
            self._due_label_to_iso[label] = d.isoformat()
        return options

    def _on_due_change(self, selected: str):
        if self._due_label_to_iso.get(selected) is None:
            self._time_var.set("Sem horario")
            self._time_menu.configure(state="disabled")
        else:
            self._time_menu.configure(state="normal")

    def _refresh_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        selected = self._filter_var.get()
        status_filter = None
        due_filter = None

        if selected == "Pendentes":
            status_filter = "pendente"
        elif selected == "Concluídas":
            status_filter = "concluída"
        elif selected == "Sem data":
            due_filter = "without_due"
        elif selected == "Vencidas":
            due_filter = "overdue"
        elif selected == "Hoje":
            due_filter = "today"
        elif selected == "Próx. 7 dias":
            due_filter = "upcoming7"

        tasks = task_manager.list_tasks(
            status_filter=status_filter,
            due_filter=due_filter,
            sort_by_due=(self._sort_switch.get() == 1),
        )

        if not tasks:
            ctk.CTkLabel(self._list_frame, text="Nenhuma tarefa encontrada para o filtro selecionado.",
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
        if task.get("due_date") and task.get("reminder_time"):
            mins = int(task.get("remind_before_minutes", 5))
            title += f"   [lembrete: {task['reminder_time']} (-{mins}min)]"
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
        due = self._due_label_to_iso.get(self._due_var.get())
        reminder_time = self._time_var.get()
        if reminder_time == "Sem horario":
            reminder_time = None

        if not title:
            self._status.configure(text="Digite um título para a tarefa.")
            return

        if reminder_time and not due:
            self._status.configure(text="Para usar lembrete por hora, preencha também a data.")
            return

        task_manager.add_task(
            title=title,
            due_date=due,
            reminder_time=reminder_time,
            remind_before_minutes=5,
        )
        self._entry.delete(0, "end")
        self._due_var.set(self._due_options[0])
        self._time_var.set("Sem horario")
        self._time_menu.configure(state="disabled")
        self._refresh_list()
        if reminder_time:
            self._status.configure(text="Tarefa adicionada. Lembrete configurado para 5 minutos antes.")
        else:
            self._status.configure(text="Tarefa adicionada com sucesso.")

    def _complete(self, tid):
        task_manager.complete_task(tid)
        self._refresh_list()

    def _delete(self, tid):
        task_manager.delete_task(tid)
        self._refresh_list()

    def _send_reminder(self):
        if send_section_reminder("Tarefas"):
            self._status.configure(text="Lembrete de tarefas enviado.")
        else:
            self._status.configure(text="Não foi possível enviar o lembrete.")


# ── Frame: Downloads ──────────────────────────────────────────────────────────
class DownloadsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)
        self._built = False
        from config import DOWNLOADS_DIR
        self._target_dir = DOWNLOADS_DIR

    def on_show(self):
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        section_title(self, "📁  Organizar Downloads")
        self._status = status_label(self)

        folder_row = ctk.CTkFrame(self, fg_color="transparent")
        folder_row.pack(fill="x", padx=28, pady=(0, 10))
        ctk.CTkLabel(folder_row, text="Pasta selecionada:", text_color=TEXT_SEC).pack(side="left", padx=(0, 8))
        self._folder_var = ctk.StringVar(value=self._target_dir)
        self._folder_entry = ctk.CTkEntry(folder_row, textvariable=self._folder_var, state="readonly")
        self._folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._btn_pick_folder = ctk.CTkButton(
            folder_row,
            text="Escolher pasta",
            width=130,
            height=32,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._pick_folder,
        )
        self._btn_pick_folder.pack(side="left")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(anchor="w", padx=28, pady=(0, 16))
        self._btn_preview = action_btn(btns, "👁  Pré-visualizar", self._preview, color=ACCENT)
        self._btn_preview.pack(side="left", padx=(0, 10))
        self._btn_organize = action_btn(btns, "🚀  Organizar agora", self._organize)
        self._btn_organize.pack(side="left")
        self._btn_reminder = action_btn(btns, "🔔 Lembrete", self._send_reminder, color="#7c3aed")
        self._btn_reminder.pack(side="left", padx=(10, 0))

        self._log = ctk.CTkTextbox(self, state="disabled", fg_color=BG_CARD,
                                    font=ctk.CTkFont(family="Consolas", size=12),
                                    corner_radius=10)
        self._log.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    def _log_write(self, text):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _set_busy(self, is_busy: bool):
        state = "disabled" if is_busy else "normal"
        self._btn_preview.configure(state=state)
        self._btn_organize.configure(state=state)
        self._btn_reminder.configure(state=state)
        self._btn_pick_folder.configure(state=state)

    def _pick_folder(self):
        selected = filedialog.askdirectory(initialdir=self._target_dir)
        if not selected:
            return
        self._target_dir = selected
        self._folder_var.set(selected)
        self._status.configure(text="Pasta atualizada para organização.")

    def _preview(self):
        self._set_busy(True)
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")
        self._status.configure(text="Simulando...")
        def run():
            import io, sys
            buf = io.StringIO()
            old = sys.stdout
            try:
                sys.stdout = buf
                file_organizer.organize_downloads(dry_run=True, target_dir=self._target_dir)
            finally:
                sys.stdout = old
            output = buf.getvalue()
            self.after(0, lambda: self._log_write(output))
            self.after(0, lambda: self._status.configure(text="Pré-visualização concluída."))
            self.after(0, lambda: self._set_busy(False))
        threading.Thread(target=run, daemon=True).start()

    def _organize(self):
        self._set_busy(True)
        self._status.configure(text="Organizando...")
        def run():
            import io, sys
            buf = io.StringIO()
            old = sys.stdout
            try:
                sys.stdout = buf
                file_organizer.organize_downloads(dry_run=False, target_dir=self._target_dir)
            finally:
                sys.stdout = old
            output = buf.getvalue()
            self.after(0, lambda: self._log_write(output))
            self.after(0, lambda: self._status.configure(text="Concluído."))
            self.after(0, lambda: self._set_busy(False))
        threading.Thread(target=run, daemon=True).start()

    def _send_reminder(self):
        if send_section_reminder("Downloads"):
            self._status.configure(text="Lembrete de downloads enviado.")
        else:
            self._status.configure(text="Não foi possível enviar o lembrete.")


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
        action_btn(row, "🔔 Lembrete", self._send_reminder, color="#7c3aed").pack(side="left", padx=(10, 0))

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

    def _send_reminder(self):
        if send_section_reminder("Agenda"):
            self._status.configure(text="Lembrete de agenda enviado.")
        else:
            self._status.configure(text="Não foi possível enviar o lembrete.")


# ── Frame: Hábitos ───────────────────────────────────────────────────────────
class HabitosFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        section_title(self, "⏰  Lembretes de Hábitos")
        self._status = status_label(self)

        card = card_frame(self)
        card.pack(fill="x", padx=24, pady=(0, 16))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        self._title = ctk.CTkEntry(row, placeholder_text="Hábito (água, remédio, alongar)",
                                   height=36, font=ctk.CTkFont(size=13))
        self._title.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._interval = ctk.CTkEntry(row, placeholder_text="Intervalo min", width=120,
                                      height=36, font=ctk.CTkFont(size=13))
        self._interval.insert(0, "120")
        self._interval.pack(side="left", padx=(0, 8))

        action_btn(row, "+ Adicionar", self._add).pack(side="left")
        action_btn(row, "🔔 Lembrete", self._send_general_reminder, color="#7c3aed").pack(side="left", padx=(8, 0))

        self._list = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._list.pack(fill="both", expand=True, padx=24)

        self._refresh()

    def _refresh(self):
        for w in self._list.winfo_children():
            w.destroy()

        habits = habits_manager.list_habits()
        if not habits:
            ctk.CTkLabel(self._list, text="Nenhum hábito cadastrado.", text_color=TEXT_SEC).pack(pady=20)
            return

        for h in habits:
            row = ctk.CTkFrame(self._list, fg_color=BG_CARD, corner_radius=8, height=52)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)

            state_txt = "Ativo" if h.get("enabled", True) else "Pausado"
            state_color = "#4ade80" if h.get("enabled", True) else "#f59e0b"

            ctk.CTkLabel(row, text=h["title"], text_color="white",
                         font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(12, 8))
            ctk.CTkLabel(row, text=f"a cada {h.get('interval_minutes', 120)} min",
                         text_color=TEXT_SEC, font=ctk.CTkFont(size=12)).pack(side="left")
            ctk.CTkLabel(row, text=state_txt, text_color=state_color,
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=8)

            ctk.CTkButton(
                row, text="Lembrar agora", width=95, height=28,
                fg_color=ACCENT, hover_color="#0b2747", font=ctk.CTkFont(size=11),
                command=lambda hid=h["id"]: self._remind_now(hid),
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                row, text="Ativar/Pausar", width=95, height=28,
                fg_color="#374151", hover_color="#4b5563", font=ctk.CTkFont(size=11),
                command=lambda hid=h["id"]: self._toggle(hid),
            ).pack(side="right", padx=4)

            ctk.CTkButton(
                row, text="✕", width=30, height=28,
                fg_color="#374151", hover_color="#6b7280", font=ctk.CTkFont(size=11),
                command=lambda hid=h["id"]: self._delete(hid),
            ).pack(side="right", padx=4)

    def _add(self):
        title = self._title.get().strip()
        interval_raw = self._interval.get().strip() or "120"
        if not title:
            self._status.configure(text="Digite o nome do hábito.")
            return
        try:
            interval = int(interval_raw)
            if interval <= 0:
                raise ValueError
        except ValueError:
            self._status.configure(text="Intervalo inválido. Use minutos (ex: 120).")
            return

        habits_manager.add_habit(title=title, interval_minutes=interval)
        self._title.delete(0, "end")
        self._interval.delete(0, "end")
        self._interval.insert(0, "120")
        self._status.configure(text="Hábito adicionado.")
        self._refresh()

    def _toggle(self, hid):
        habits_manager.toggle_habit(hid)
        self._status.configure(text="Estado do hábito atualizado.")
        self._refresh()

    def _delete(self, hid):
        habits_manager.delete_habit(hid)
        self._status.configure(text="Hábito removido.")
        self._refresh()

    def _remind_now(self, hid):
        if habits_manager.send_habit_reminder_now(hid):
            self._status.configure(text="Lembrete manual enviado.")
        else:
            self._status.configure(text="Não foi possível enviar o lembrete.")
        self._refresh()

    def _send_general_reminder(self):
        if send_section_reminder("Hábitos"):
            self._status.configure(text="Lembrete de hábitos enviado.")
        else:
            self._status.configure(text="Não foi possível enviar o lembrete.")


# ── Frame: Compras ───────────────────────────────────────────────────────────
class ComprasFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BG_DARK, corner_radius=0)

    def on_show(self):
        for w in self.winfo_children():
            w.destroy()
        self._build()

    def _build(self):
        section_title(self, "🛒  Lista de Compras")
        self._status = status_label(self)

        card = card_frame(self)
        card.pack(fill="x", padx=24, pady=(0, 16))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=14)

        self._name = ctk.CTkEntry(row, placeholder_text="Item (arroz, leite, sabão)",
                                  height=36, font=ctk.CTkFont(size=13))
        self._name.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._qty = ctk.CTkEntry(row, placeholder_text="Qtd", width=100,
                                 height=36, font=ctk.CTkFont(size=13))
        self._qty.insert(0, "1")
        self._qty.pack(side="left", padx=(0, 8))

        self._price = ctk.CTkEntry(row, placeholder_text="Valor (R$)", width=120,
                       height=36, font=ctk.CTkFont(size=13))
        self._price.insert(0, "0,00")
        self._price.pack(side="left", padx=(0, 8))

        action_btn(row, "+ Adicionar", self._add).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row, text="Limpar comprados", width=130, height=36,
            fg_color=ACCENT, hover_color="#0b2747", command=self._clear_checked,
        ).pack(side="left")

        self._list = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, corner_radius=0)
        self._list.pack(fill="both", expand=True, padx=24)

        self._total_label = ctk.CTkLabel(
            self,
            text="Total estimado: R$ 0,00",
            text_color="#4ade80",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._total_label.pack(anchor="e", padx=28, pady=(8, 16))

        self._refresh()

    def _to_float(self, raw_value: str, default: float) -> float:
        txt = (str(raw_value or "").strip()
               .replace("R$", "")
               .replace(" ", "")
               .replace(".", "")
               .replace(",", "."))
        try:
            value = float(txt)
            return value if value >= 0 else default
        except ValueError:
            return default

    def _format_brl(self, value: float) -> str:
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _refresh(self):
        for w in self._list.winfo_children():
            w.destroy()

        items = shopping_list_manager.list_items()
        total = 0.0
        if not items:
            self._total_label.configure(text="Total estimado: R$ 0,00")
            ctk.CTkLabel(self._list, text="Sua lista está vazia.", text_color=TEXT_SEC).pack(pady=20)
            return

        # Não comprados primeiro
        items.sort(key=lambda i: (i.get("checked", False), i.get("name", "").lower()))

        for item in items:
            row = ctk.CTkFrame(self._list, fg_color=BG_CARD, corner_radius=8, height=48)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)

            qty_value = self._to_float(item.get("quantity", "1"), 1.0)
            price_value = self._to_float(item.get("price", "0,00"), 0.0)
            total += qty_value * price_value

            checked = item.get("checked", False)
            icon = "✓" if checked else "○"
            color = "#4ade80" if checked else "white"

            ctk.CTkLabel(row, text=icon, text_color=color,
                         font=ctk.CTkFont(size=16, weight="bold"), width=30).pack(side="left", padx=(12, 0))
            ctk.CTkLabel(row, text=f"{item['name']}  (x{item.get('quantity', '1')})  -  R$ {item.get('price', '0,00')}",
                         text_color=color if checked else "white",
                         font=ctk.CTkFont(size=13)).pack(side="left", padx=10, fill="x", expand=True)

            ctk.CTkButton(
                row, text="Marcar", width=70, height=28,
                fg_color="#16a34a", hover_color="#15803d", font=ctk.CTkFont(size=11),
                command=lambda iid=item["id"]: self._toggle(iid),
            ).pack(side="left", padx=4)

            ctk.CTkButton(
                row, text="✕", width=30, height=28,
                fg_color="#374151", hover_color="#6b7280", font=ctk.CTkFont(size=11),
                command=lambda iid=item["id"]: self._delete(iid),
            ).pack(side="left", padx=(0, 10))

        self._total_label.configure(text=f"Total estimado: R$ {self._format_brl(total)}")

    def _add(self):
        name = self._name.get().strip()
        qty = self._qty.get().strip() or "1"
        price = self._price.get().strip() or "0,00"
        if not name:
            self._status.configure(text="Digite o nome do item.")
            return
        shopping_list_manager.add_item(name=name, quantity=qty, price=price)
        self._name.delete(0, "end")
        self._qty.delete(0, "end")
        self._qty.insert(0, "1")
        self._price.delete(0, "end")
        self._price.insert(0, "0,00")
        self._status.configure(text="Item adicionado.")
        self._refresh()

    def _toggle(self, iid):
        shopping_list_manager.toggle_item(iid)
        self._status.configure(text="Item atualizado.")
        self._refresh()

    def _delete(self, iid):
        shopping_list_manager.delete_item(iid)
        self._status.configure(text="Item removido.")
        self._refresh()

    def _clear_checked(self):
        removed = shopping_list_manager.clear_checked()
        self._status.configure(text=f"{removed} item(ns) comprado(s) removido(s).")
        self._refresh()


# ── Janela: Acessibilidade ───────────────────────────────────────────────────
class AccessibilityWindow(ctk.CTkToplevel):
    """Janela flutuante de configurações de acessibilidade."""

    _FONT_SCALES = [0.8, 1.0, 1.25, 1.5, 2.0]

    def __init__(self, master):
        super().__init__(master)
        self.title("♿ Acessibilidade")
        self.geometry("440x460")
        self.resizable(False, False)
        self.grab_set()
        self._mgr = accessibility.get_manager()
        # Cópia de trabalho dos settings para edição
        self._work = dict(self._mgr.settings)
        self._build()

    def _build(self):
        pad = {"padx": 28, "pady": (14, 0)}

        ctk.CTkLabel(
            self, text="Configurações de Acessibilidade",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(**pad)

        # ── Alto contraste ────────────────────────────────────────────────────
        sep1 = ctk.CTkFrame(self, height=1, fg_color="gray30")
        sep1.pack(fill="x", padx=20, pady=(16, 0))

        row_hc = ctk.CTkFrame(self, fg_color="transparent")
        row_hc.pack(fill="x", **pad)
        ctk.CTkLabel(
            row_hc, text="Alto Contraste",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            row_hc,
            text="Tema claro com alto contraste para baixa visão",
            text_color=TEXT_SEC, font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(10, 0))
        self._hc_var = ctk.BooleanVar(value=self._work["high_contrast"])
        ctk.CTkSwitch(
            self, text="", variable=self._hc_var,
            onvalue=True, offvalue=False,
        ).pack(anchor="w", padx=28, pady=(6, 0))

        # ── Escala de fonte ───────────────────────────────────────────────────
        sep2 = ctk.CTkFrame(self, height=1, fg_color="gray30")
        sep2.pack(fill="x", padx=20, pady=(14, 0))

        ctk.CTkLabel(
            self, text="Tamanho da Fonte",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", **pad)

        scale_row = ctk.CTkFrame(self, fg_color="transparent")
        scale_row.pack(fill="x", padx=28, pady=(6, 0))

        current_idx = 1  # padrão 1.0×
        cur = self._work["font_scale"]
        for i, v in enumerate(self._FONT_SCALES):
            if abs(v - cur) < 0.01:
                current_idx = i
                break

        self._scale_label = ctk.CTkLabel(
            scale_row,
            text=f"{self._work['font_scale']:.2f}×",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=50,
        )
        self._scale_label.pack(side="right")

        self._scale_slider = ctk.CTkSlider(
            scale_row,
            from_=0, to=len(self._FONT_SCALES) - 1,
            number_of_steps=len(self._FONT_SCALES) - 1,
            command=self._on_scale_change,
        )
        self._scale_slider.set(current_idx)
        self._scale_slider.pack(side="left", fill="x", expand=True, padx=(0, 12))

        ctk.CTkLabel(
            self,
            text="  ".join([f"{v:.2f}×" for v in self._FONT_SCALES]),
            text_color=TEXT_SEC, font=ctk.CTkFont(size=10),
        ).pack(anchor="w", padx=28)

        # ── Leitor de tela ────────────────────────────────────────────────────
        sep3 = ctk.CTkFrame(self, height=1, fg_color="gray30")
        sep3.pack(fill="x", padx=20, pady=(14, 0))

        row_tts = ctk.CTkFrame(self, fg_color="transparent")
        row_tts.pack(fill="x", **pad)
        ctk.CTkLabel(
            row_tts, text="Leitor de Tela (TTS)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            row_tts, text="Lê seções e avisos em voz alta",
            text_color=TEXT_SEC, font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=(10, 0))
        self._tts_var = ctk.BooleanVar(value=self._work["tts_enabled"])
        ctk.CTkSwitch(
            self, text="", variable=self._tts_var,
            onvalue=True, offvalue=False,
        ).pack(anchor="w", padx=28, pady=(6, 0))

        # Velocidade da fala
        speed_row = ctk.CTkFrame(self, fg_color="transparent")
        speed_row.pack(fill="x", padx=28, pady=(8, 0))
        ctk.CTkLabel(speed_row, text="Velocidade da fala:", text_color=TEXT_SEC,
                     font=ctk.CTkFont(size=12)).pack(side="left")
        self._rate_label = ctk.CTkLabel(
            speed_row,
            text=f"{self._work['tts_rate']} WPM",
            font=ctk.CTkFont(size=12, weight="bold"), width=70,
        )
        self._rate_label.pack(side="right")
        self._rate_slider = ctk.CTkSlider(
            speed_row, from_=80, to=280,
            number_of_steps=40,
            command=self._on_rate_change,
        )
        self._rate_slider.set(self._work["tts_rate"])
        self._rate_slider.pack(side="left", fill="x", expand=True, padx=(10, 12))

        # ── Botões ────────────────────────────────────────────────────────────
        sep4 = ctk.CTkFrame(self, height=1, fg_color="gray30")
        sep4.pack(fill="x", padx=20, pady=(14, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(14, 20))

        ctk.CTkButton(
            btn_row, text="🔊 Testar fala",
            fg_color=ACCENT, hover_color="#0b2747",
            font=ctk.CTkFont(size=13), height=36,
            command=self._test_speech,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_row, text="Aplicar e Salvar",
            fg_color=ACCENT2, hover_color="#c73652",
            font=ctk.CTkFont(size=13, weight="bold"), height=36,
            command=self._apply,
        ).pack(side="left")

        self._status = ctk.CTkLabel(
            self, text="", text_color=TEXT_SEC,
            font=ctk.CTkFont(size=11),
        )
        self._status.pack(pady=(0, 10))

    def _on_scale_change(self, val):
        idx = round(float(val))
        scale = self._FONT_SCALES[idx]
        self._work["font_scale"] = scale
        self._scale_label.configure(text=f"{scale:.2f}×")

    def _on_rate_change(self, val):
        rate = int(float(val))
        self._work["tts_rate"] = rate
        self._rate_label.configure(text=f"{rate} WPM")

    def _test_speech(self):
        self._mgr.settings["tts_enabled"] = True
        self._mgr.update_tts_rate(self._work["tts_rate"])
        self._mgr.speak("Teste de leitura completo. Se você ouvir esta frase inteira, o leitor de tela está funcionando corretamente.")
        self._status.configure(text="Fala de teste enviada.")

    def _apply(self):
        self._mgr.settings["high_contrast"] = self._hc_var.get()
        self._mgr.settings["font_scale"] = self._work["font_scale"]
        self._mgr.settings["tts_enabled"] = self._tts_var.get()
        self._mgr.settings["tts_rate"] = self._work["tts_rate"]
        self._mgr.update_tts_rate(self._work["tts_rate"])
        self._mgr.apply_all()
        self._mgr.save()
        self._status.configure(text="✓ Configurações aplicadas e salvas.")
        if self._mgr.settings["tts_enabled"]:
            self._mgr.speak("Configurações de acessibilidade aplicadas.")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
