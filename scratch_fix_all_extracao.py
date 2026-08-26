import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv("scraper/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

KANBAN_EXTRACAO = "9cfb9d98-89cb-4169-88e1-db399f3ce877"

# Busca todos os imóveis na coluna Extração de Telefone que estão marcados como expirados
res = supabase.table("imoveis").select("id, titulo").eq("kanban_coluna_id", KANBAN_EXTRACAO).eq("anuncio_expirado", True).execute()

if res.data:
    print(f"Encontrados {len(res.data)} imóveis na Extração de Telefone com a flag expirado = True.")
    for imv in res.data:
        supabase.table("imoveis").update({
            "anuncio_expirado": False
        }).eq("id", imv["id"]).execute()
        print(f"Corrigido ID: {imv['id']} - {imv['titulo'][:30]}")
    print("Todos corrigidos.")
else:
    print("Nenhum imóvel na Extração de Telefone está com a flag expirada no momento.")
