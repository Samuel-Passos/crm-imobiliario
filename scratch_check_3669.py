import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv("scraper/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

KANBAN_EXTRACAO = "9cfb9d98-89cb-4169-88e1-db399f3ce877"

res = supabase.table("imoveis").select("*").eq("id", 3669).execute()
if res.data:
    imv = res.data[0]
    print(f"Estado atual ID 3669: Coluna={imv.get('kanban_coluna_id')}, Expirado={imv.get('anuncio_expirado')}, Título={imv.get('titulo')}")
    
    # Forçar a restauração
    supabase.table("imoveis").update({
        "kanban_coluna_id": KANBAN_EXTRACAO,
        "anuncio_expirado": False
    }).eq("id", 3669).execute()
    print("Foi restaurado forçadamente para Extração de Telefone.")
else:
    print("Imovel 3669 nao encontrado.")
