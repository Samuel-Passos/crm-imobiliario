import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get all imoveis ids
res_imoveis = supabase.table("imoveis").select("id").execute()
imoveis_ids = {item["id"] for item in res_imoveis.data}

# Get all imovel_id from links_anuncios
res_links = supabase.table("links_anuncios").select("imovel_id").execute()
links_ids = {item["imovel_id"] for item in res_links.data if item.get("imovel_id")}

orphaned_ids = imoveis_ids - links_ids
print("Orphaned imoveis IDs:", orphaned_ids)

if orphaned_ids:
    # let's get the details of the first one
    orphaned_id = list(orphaned_ids)[0]
    details = supabase.table("imoveis").select("*").eq("id", orphaned_id).execute()
    print("Details:", details.data)
