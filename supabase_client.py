# supabase_client.py
import threading
from supabase import create_client, Client

SUPABASE_URL = "https://ikknxtvmdoykppnmnryx.supabase.co"
SUPABASE_KEY = "sb_publishable_aA_Bm7tCXzMynYZ5u4nSjw_wjAzHt8L"

supabase: Client = None

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[Supabase] Cliente inicializado com sucesso!")
except Exception as e:
    print(f"[Supabase] Erro ao inicializar o cliente: {e}")
    supabase = None


def run_in_background(target, *args, **kwargs):
    """Executa uma função em background thread para evitar travar a UI."""
    t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t
