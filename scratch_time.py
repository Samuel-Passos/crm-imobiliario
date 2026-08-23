import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

coluna_extracao = "9cfb9d98-89cb-4169-88e1-db399f3ce877"

# Imóveis na fila de extração de telefone que ainda não foram pesquisados
res = supabase.table("imoveis").select("id", count="exact").eq("kanban_coluna_id", coluna_extracao).eq("telefone_pesquisado", False).execute()
restantes = res.count

print(f"Faltam: {restantes}")
