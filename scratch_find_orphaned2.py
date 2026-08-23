import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get all imoveis
res_imoveis = supabase.table("imoveis").select("*").execute()
if not res_imoveis.data:
    print("Nenhum imovel encontrado")
else:
    print("Colunas de imoveis:", list(res_imoveis.data[0].keys()))

imoveis_list_ids = {item.get("list_id") for item in res_imoveis.data if item.get("list_id")}

# Get all links_anuncios
res_links = supabase.table("links_anuncios").select("list_id").execute()
links_list_ids = {item.get("list_id") for item in res_links.data if item.get("list_id")}

orphaned_ids = imoveis_list_ids - links_list_ids
print(f"Total imoveis: {len(imoveis_list_ids)}")
print(f"Total links: {len(links_list_ids)}")
print("Orphaned list_ids (in imoveis but not in links):", orphaned_ids)

if orphaned_ids:
    missing = list(orphaned_ids)[0]
    # details of missing
    imovel_missing = next(item for item in res_imoveis.data if item.get("list_id") == missing)
    print("Imovel missing details:", imovel_missing.get("id"), imovel_missing.get("url"))
    
    # Check what columns to insert into links_anuncios
    res_links_all = supabase.table("links_anuncios").select("*").limit(1).execute()
    print("Colunas de links_anuncios:", list(res_links_all.data[0].keys()))

    # Insert into links_anuncios
    # data_to_insert = { "list_id": missing, "url": imovel_missing.get("url"), "status": "ativo" } # something like that
