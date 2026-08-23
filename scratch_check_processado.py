import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get all imoveis
res_imoveis = supabase.table("imoveis").select("id, list_id, url").execute()
imoveis_list_ids = {item["list_id"] for item in res_imoveis.data if item.get("list_id")}
print(f"Total imoveis: {len(imoveis_list_ids)}")

# Get all links_anuncios that are in imoveis
res_links = supabase.table("links_anuncios").select("id, list_id, status").in_("list_id", list(imoveis_list_ids)).execute()

print(f"Total links correspondentes aos imoveis: {len(res_links.data)}")

not_processado = [link for link in res_links.data if link.get("status") != "processado"]
print("Links dos imóveis que NÃO estão como 'processado':", not_processado)

# Let's also check if any imovel doesn't have a corresponding link_anuncios AT ALL
links_list_ids = {item["list_id"] for item in res_links.data if item.get("list_id")}
orphaned = imoveis_list_ids - links_list_ids
print("Imoveis sem link_anuncio correspondente:", orphaned)

