import os
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv("scraper/.env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("imoveis").select("cidade").execute()

if res.data:
    cidades = [im.get("cidade") for im in res.data if im.get("cidade")]
    contagem = Counter(cidades)
    
    print("🏙️ Cidades encontradas no banco de dados:")
    print("-" * 40)
    for cidade, qtde in contagem.most_common():
        print(f"{cidade:<30} | {qtde} imóveis")
else:
    print("Nenhum imóvel encontrado no banco.")
