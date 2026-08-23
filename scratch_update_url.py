import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

list_id_to_update = 1527823856
clean_url = 'https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/kitnet-1527823856'

print(f"Updating imovel with list_id {list_id_to_update} to have clean url {clean_url}")
res = supabase.table("imoveis").update({"url": clean_url}).eq("list_id", list_id_to_update).execute()

print("Update result:", res.data)
