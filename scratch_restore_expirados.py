import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv("scraper/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

KANBAN_EXPIRADOS = "5f01efe9-6531-4259-9927-76c130e2851d"
KANBAN_EXTRACAO = "9cfb9d98-89cb-4169-88e1-db399f3ce877"

res = supabase.table("imoveis").select("id, titulo, anuncio_expirado").eq("kanban_coluna_id", KANBAN_EXPIRADOS).execute()

total = len(res.data) if res.data else 0
print(f"Total em expirados: {total}")

restaurados = 0
for imv in res.data:
    # Apenas como segurança, verifique se a flag foi marcada como true.
    if imv.get("anuncio_expirado") is True:
        supabase.table("imoveis").update({
            "kanban_coluna_id": KANBAN_EXTRACAO,
            "anuncio_expirado": False
        }).eq("id", imv["id"]).execute()
        print(f"Restaurado ID: {imv['id']} - {imv['titulo'][:30]}")
        restaurados += 1

print(f"\nOperação concluída. {restaurados} imóveis voltaram para a coluna Extração de Telefone.")
