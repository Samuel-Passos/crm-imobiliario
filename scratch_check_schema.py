import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
res = sup.table('kanban_colunas').select('*').limit(1).execute()
if res.data:
    print(res.data[0].keys())
else:
    print("No data in kanban_colunas")
