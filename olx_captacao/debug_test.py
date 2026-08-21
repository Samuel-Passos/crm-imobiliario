from supabase_client import supabase

coluna_res = supabase.table("kanban_colunas").select("id").eq("nome", "Aceitou").execute()
coluna_id = coluna_res.data[0]["id"] if coluna_res.data else None
print("ID Aceitou:", coluna_id)

if coluna_id:
    imoveis = supabase.table("imoveis").select("id, list_id, fotos_baixadas").eq("kanban_coluna_id", coluna_id).execute()
    print("Imoveis no Aceitou:", imoveis.data)
