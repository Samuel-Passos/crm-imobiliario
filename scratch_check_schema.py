import os
from dotenv import load_dotenv
from supabase import create_client
import json

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    res = sup.table('configuracoes_scraper').select('*').limit(1).execute()
    if res.data:
        print("Colunas presentes na tabela:")
        for key, val in res.data[0].items():
            print(f"- {key}: {val}")
    else:
        print("Tabela existe, mas não tem dados.")
except Exception as e:
    print("Erro ao acessar configuracoes:", e)
