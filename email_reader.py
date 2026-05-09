import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from config import (
    CREDENTIALS_FILE, TOKEN_GMAIL_FILE,
    GMAIL_SCOPES, TASK_KEYWORDS, ATTACHMENTS_DIR,
)
import task_manager


def _get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_GMAIL_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_GMAIL_FILE, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_GMAIL_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _extract_body(payload: dict) -> str:
    """Extrai o texto do corpo do e-mail recursivamente."""
    body = ""
    if payload.get("body", {}).get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    if payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") in ("text/plain", "text/html"):
                data = part.get("body", {}).get("data", "")
                if data:
                    body += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif part.get("parts"):
                body += _extract_body(part)
    return body


def _save_attachment(service, message_id: str, part: dict) -> str | None:
    """Baixa um anexo e salva localmente. Retorna o caminho do arquivo salvo."""
    filename = part.get("filename")
    if not filename:
        return None

    data = part.get("body", {}).get("data")
    attachment_id = part.get("body", {}).get("attachmentId")

    if not data and attachment_id:
        attachment = service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=attachment_id
        ).execute()
        data = attachment.get("data")

    if not data:
        return None

    filepath = os.path.join(ATTACHMENTS_DIR, filename)
    # Evita sobrescrever
    if os.path.exists(filepath):
        base, ext = os.path.splitext(filename)
        import time
        filepath = os.path.join(ATTACHMENTS_DIR, f"{base}_{int(time.time())}{ext}")

    with open(filepath, "wb") as f:
        f.write(base64.urlsafe_b64decode(data))
    return filepath


def read_emails(max_results: int = 20) -> dict:
    """
    Lê e-mails não lidos do Gmail.
    - Cria tarefas automaticamente quando detecta palavras-chave.
    - Baixa anexos para a pasta local.
    Retorna dict com 'tasks_created' e 'attachments_saved'.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print("[Gmail] credentials.json não encontrado em credentials/.")
        print("[Gmail] Siga as instruções em SETUP.md para configurar o OAuth2.")
        return {"tasks_created": [], "attachments_saved": []}

    service = _get_gmail_service()

    results = service.users().messages().list(
        userId="me", labelIds=["UNREAD"], maxResults=max_results
    ).execute()
    messages = results.get("messages", [])

    tasks_created = []
    attachments_saved = []

    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", messageId=msg_meta["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
        subject = headers.get("Subject", "(sem assunto)")
        sender = headers.get("From", "desconhecido")
        body = _extract_body(msg["payload"])
        content = (subject + " " + body).lower()

        # Detecta palavras-chave e cria tarefa
        matched = [kw for kw in TASK_KEYWORDS if kw in content]
        if matched:
            title = f"[Email] {subject[:80]}"
            task = task_manager.add_task(title=title, source=f"gmail:{sender}")
            tasks_created.append(task)
            print(f"[Gmail] Tarefa criada: {title}  (palavras: {matched})")

        # Baixa anexos
        parts = msg["payload"].get("parts", [])
        for part in parts:
            if part.get("filename") and part["filename"].strip():
                path = _save_attachment(service, msg_meta["id"], part)
                if path:
                    attachments_saved.append(path)
                    print(f"[Gmail] Anexo salvo: {os.path.basename(path)}")

    print(f"[Gmail] {len(messages)} e-mail(s) lido(s). "
          f"{len(tasks_created)} tarefa(s) criada(s). "
          f"{len(attachments_saved)} anexo(s) salvo(s).")
    return {"tasks_created": tasks_created, "attachments_saved": attachments_saved}


if __name__ == "__main__":
    read_emails()
