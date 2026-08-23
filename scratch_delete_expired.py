import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get expired property to know its list_id
res_expirados = supabase.table("imoveis").select("id, list_id").eq("anuncio_expirado", True).execute()

for imovel in res_expirados.data:
    imovel_id = imovel["id"]
    list_id = imovel["list_id"]
    print(f"Deleting imovel with id {imovel_id} and list_id {list_id}")
    
    if list_id:
        # Delete from links_anuncios first just in case
        res_link_del = supabase.table("links_anuncios").delete().eq("list_id", list_id).execute()
        print(f"Deleted from links_anuncios: {len(res_link_del.data)} rows")

    # Delete from imoveis
    res_imovel_del = supabase.table("imoveis").delete().eq("id", imovel_id).execute()
    print(f"Deleted from imoveis: {len(res_imovel_del.data)} rows")

print("Done.")
