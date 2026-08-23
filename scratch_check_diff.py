import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

list_id_to_check = 1527823856

imovel = supabase.table("imoveis").select("id, list_id, url").eq("list_id", list_id_to_check).execute()
print("Imovel:", imovel.data)

link = supabase.table("links_anuncios").select("id, list_id, url").eq("list_id", list_id_to_check).execute()
print("Link:", link.data)
