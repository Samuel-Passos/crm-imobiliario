import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get total count
res_all = supabase.table("imoveis").select("id, ativo, list_id, url").execute()
print(f"Total imoveis: {len(res_all.data)}")

inativos = [item for item in res_all.data if not item.get("ativo")]

print(f"Total inativos: {len(inativos)}")
if inativos:
    print("Imovel inativo:", inativos[0])
