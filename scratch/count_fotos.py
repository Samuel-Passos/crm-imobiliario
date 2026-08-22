import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("/home/samuel/Desktop/Scraper_antigravity/scraper/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

res = supabase.table("imoveis").select("id, fotos, fotos_baixadas").eq("fotos_baixadas", True).execute()

total_fotos = 0
imoveis_com_fotos = 0

if res.data:
    imoveis_com_fotos = len(res.data)
    for imovel in res.data:
        fotos = imovel.get("fotos", [])
        if isinstance(fotos, list):
            total_fotos += len(fotos)

print(f"Total de imóveis com fotos baixadas: {imoveis_com_fotos}")
print(f"Total absoluto de fotos (arquivos) salvas: {total_fotos}")
