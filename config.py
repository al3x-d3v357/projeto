import os
import sys
import json

# Em modo executável (PyInstaller), usa a pasta do .exe.
# Em modo desenvolvimento, usa a pasta do projeto.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta monitorada pelo organizador de arquivos
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Pasta onde os anexos de e-mail são salvos localmente antes do upload
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")

# Arquivo de tarefas
TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")

# Arquivo de hábitos
HABITS_FILE = os.path.join(BASE_DIR, "habits.json")

# Arquivo de lista de compras
SHOPPING_FILE = os.path.join(BASE_DIR, "shopping_list.json")

# Arquivo de contas a pagar
BILLS_FILE = os.path.join(BASE_DIR, "bills.csv")

# Histórico de lembretes enviados para evitar duplicidade no mesmo dia
REMINDER_HISTORY_FILE = os.path.join(BASE_DIR, "reminder_history.json")

# Pasta de saída das agendas semanais
AGENDA_DIR = os.path.join(BASE_DIR, "agendas")

# Pasta de credenciais OAuth2 (NÃO versionar)
CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")
CREDENTIALS_FILE = os.path.join(CREDENTIALS_DIR, "credentials.json")
TOKEN_GMAIL_FILE = os.path.join(CREDENTIALS_DIR, "token_gmail.json")
TOKEN_DRIVE_FILE = os.path.join(CREDENTIALS_DIR, "token_drive.json")

# Quantos dias antes do vencimento emitir o lembrete
BILL_REMINDER_DAYS = 3

# Palavras-chave nos e-mails que indicam uma tarefa
TASK_KEYWORDS = ["urgente", "prazo", "confirmar", "responder", "pendente", "deadline", "até quando"]

# Nome da pasta no Google Drive para upload dos anexos
DRIVE_FOLDER_NAME = "Anexos-Emails"

# Mapeamento de extensões para subpastas no organizador
FILE_CATEGORIES = {
    "Imagens":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".heic"],
    "Documentos": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".odt"],
    "Videos":     [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
    "Audio":      [".mp3", ".wav", ".ogg", ".aac", ".flac"],
    "Compactados":[".zip", ".rar", ".7z", ".tar", ".gz"],
    "Codigo":     [".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".csv"],
}

# Escopos OAuth2 necessários
GMAIL_SCOPES  = ["https://www.googleapis.com/auth/gmail.readonly"]
DRIVE_SCOPES  = ["https://www.googleapis.com/auth/drive.file"]

# Flags de integração opcional
EMAIL_AUTOMATION_ENABLED = True
DRIVE_UPLOAD_ENABLED = True

# Intervalo em horas para leitura automática de e-mails no scheduler
SCHEDULER_EMAIL_INTERVAL_HOURS = 1

os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
os.makedirs(AGENDA_DIR, exist_ok=True)
os.makedirs(CREDENTIALS_DIR, exist_ok=True)


def _ensure_default_files() -> None:
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    if not os.path.exists(HABITS_FILE):
        with open(HABITS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    if not os.path.exists(SHOPPING_FILE):
        with open(SHOPPING_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

    if not os.path.exists(BILLS_FILE):
        default_bills = (
            "nome,valor,vencimento\n"
            "Internet,99.90,2026-05-15\n"
            "Energia Elétrica,180.00,2026-05-18\n"
            "Aluguel,1200.00,2026-05-10\n"
        )
        with open(BILLS_FILE, "w", encoding="utf-8") as f:
            f.write(default_bills)


_ensure_default_files()
