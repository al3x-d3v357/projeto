import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import (
    CREDENTIALS_FILE, TOKEN_DRIVE_FILE,
    DRIVE_SCOPES, DRIVE_FOLDER_NAME, ATTACHMENTS_DIR,
)


def _get_drive_service():
    creds = None
    if os.path.exists(TOKEN_DRIVE_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_DRIVE_FILE, DRIVE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, DRIVE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_DRIVE_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, folder_name: str) -> str:
    """Retorna o ID da pasta no Drive, criando-a se não existir."""
    query = (
        f"name='{folder_name}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_attachments(file_paths: list = None) -> list:
    """
    Envia arquivos para a pasta DRIVE_FOLDER_NAME no Google Drive.
    Se file_paths for None, envia todos os arquivos da pasta local de anexos.
    Retorna lista de dicts com nome e link de cada arquivo enviado.
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print("[Drive] credentials.json não encontrado em credentials/.")
        return []

    if file_paths is None:
        file_paths = [
            os.path.join(ATTACHMENTS_DIR, f)
            for f in os.listdir(ATTACHMENTS_DIR)
            if os.path.isfile(os.path.join(ATTACHMENTS_DIR, f))
        ]

    if not file_paths:
        print("[Drive] Nenhum arquivo para enviar.")
        return []

    service = _get_drive_service()
    folder_id = _get_or_create_folder(service, DRIVE_FOLDER_NAME)
    uploaded = []

    for filepath in file_paths:
        if not os.path.isfile(filepath):
            print(f"[Drive] Arquivo não encontrado, ignorado: {filepath}")
            continue

        filename = os.path.basename(filepath)
        media = MediaFileUpload(filepath, resumable=True)
        metadata = {"name": filename, "parents": [folder_id]}

        file = service.files().create(
            body=metadata,
            media_body=media,
            fields="id, name, webViewLink",
        ).execute()

        link = file.get("webViewLink", "link não disponível")
        uploaded.append({"name": filename, "link": link})
        print(f"[Drive] Enviado: {filename}  →  {link}")

    print(f"[Drive] {len(uploaded)} arquivo(s) enviado(s) para '{DRIVE_FOLDER_NAME}'.")
    return uploaded


if __name__ == "__main__":
    upload_attachments()
