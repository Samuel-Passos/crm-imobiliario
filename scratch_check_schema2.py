import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

res = supabase.table("links_anuncios").select("*").limit(1).execute()
if res.data:
    print("Colunas na tabela links_anuncios:")
    for key in res.data[0].keys():
        print(f" - {key}")
else:
    print("Tabela vazia")
