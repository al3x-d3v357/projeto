import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta monitorada pelo organizador de arquivos
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# Pasta onde os anexos de e-mail são salvos localmente antes do upload
ATTACHMENTS_DIR = os.path.join(BASE_DIR, "attachments")

# Arquivo de tarefas
TASKS_FILE = os.path.join(BASE_DIR, "tasks.json")

# Arquivo de contas a pagar
BILLS_FILE = os.path.join(BASE_DIR, "bills.csv")

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

os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
os.makedirs(AGENDA_DIR, exist_ok=True)
os.makedirs(CREDENTIALS_DIR, exist_ok=True)
