# test_supabase.py
import sys
from supabase_client import supabase

if not supabase:
    print("Erro: Cliente Supabase não pôde ser inicializado.")
    sys.exit(1)

print("Cliente Supabase inicializado com sucesso.")

test_task = {
    "id": "test-123",
    "title": "Tarefa de Teste do Supabase",
    "source": "manual",
    "status": "pendente"
}

try:
    print("Tentando inserir linha de teste na tabela 'tasks'...")
    res = supabase.table("tasks").insert(test_task).execute()
    print("Inserção realizada. Resposta:", res.data)
    
    print("Tentando buscar a linha...")
    res_select = supabase.table("tasks").select("*").eq("id", "test-123").execute()
    print("Busca realizada. Resposta:", res_select.data)
    
    print("Tentando excluir a linha de teste...")
    res_delete = supabase.table("tasks").delete().eq("id", "test-123").execute()
    print("Exclusão realizada. Resposta:", res_delete.data)
    
    print("--- Teste concluído com sucesso! ---")
except Exception as e:
    print("Ocorreu um erro durante o teste:", e)
    print("\nCertifique-se de que rodou o script SQL de criação das tabelas no console do Supabase.")
