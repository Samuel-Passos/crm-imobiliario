import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get all imoveis urls
res_imoveis = supabase.table("imoveis").select("id, list_id, url").execute()
imoveis_urls = {item.get("url") for item in res_imoveis.data if item.get("url")}

# Get all links_anuncios urls
res_links = supabase.table("links_anuncios").select("id, list_id, url").execute()
links_urls = {item.get("url") for item in res_links.data if item.get("url")}

orphaned_urls = imoveis_urls - links_urls
print(f"Total imoveis com url: {len(imoveis_urls)}")
print(f"Total links com url: {len(links_urls)}")
print("Orphaned urls (in imoveis but not in links):", orphaned_urls)

if orphaned_urls:
    missing = list(orphaned_urls)[0]
    # details of missing
    imovel_missing = next(item for item in res_imoveis.data if item.get("url") == missing)
    print("Imovel missing details:", imovel_missing)
    
    # insert into links_anuncios
    data = {
        "url": imovel_missing.get("url"),
        "list_id": imovel_missing.get("list_id"),
        "status": "ativo"
    }
    print("Inserting data:", data)
    res_insert = supabase.table("links_anuncios").insert(data).execute()
    print("Insert result:", res_insert.data)
