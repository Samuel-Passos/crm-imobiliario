import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("/home/samuel/Desktop/Scraper_antigravity/scraper/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

res = supabase.table("imoveis").select("*").eq("id", 3603).execute()
if res.data:
    imovel = res.data[0]
    print(f"Imovel 3603:")
    print(f"List ID: {imovel.get('list_id')}")
    print(f"Kanban Coluna: {imovel.get('kanban_coluna_id')}")
    print(f"Fotos count: {len(imovel.get('fotos', []))}")
else:
    print("Nao encontrado")
