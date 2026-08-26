import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    res = sup.table('configuracoes_scraper').select('*').execute()
    print("Dados em configuracoes_scraper:", res.data)
except Exception as e:
    print("Erro ao acessar configuracoes:", e)
