from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv("/home/samuel/Desktop/Scraper_antigravity/olx_captacao/.env")
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

ID_EXPIRADOS = "5f01efe9-6531-4259-9927-76c130e2851d"
ID_MERCADO = "e44220d9-97b4-4c3f-935f-7b1b09b92a31"

print("Deletando Expirados...")
res1 = supabase.table("imoveis").delete().eq("kanban_coluna_id", ID_EXPIRADOS).execute()
print(f"Deletados Expirados: {len(res1.data)}")

print("Deletando Anúncios de Mercado...")
res2 = supabase.table("imoveis").delete().eq("kanban_coluna_id", ID_MERCADO).execute()
print(f"Deletados Mercado: {len(res2.data)}")

