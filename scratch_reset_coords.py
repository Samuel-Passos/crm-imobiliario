import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Pega os 2 ultimos imoveis que tem latitude
res = supabase.table("imoveis").select("id, titulo").not_.is_("latitude", "null").order("id", desc=True).limit(2).execute()

for imovel in res.data:
    print(f"Limpando coordenadas do imovel: [{imovel['id']}] {imovel['titulo']}")
    supabase.table("imoveis").update({"latitude": None, "longitude": None}).eq("id", imovel['id']).execute()

print("Pronto! 2 imoveis agora estao sem coordenadas.")
