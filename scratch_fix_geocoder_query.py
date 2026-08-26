import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res_col = sup.table("kanban_colunas").select("id").eq("nome", "Caixa de Entrada").execute()
if res_col.data:
    print(res_col.data[0]['id'])
