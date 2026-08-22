from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv("scraper/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)
res = supabase.table("kanban_colunas").select("*").eq("id", "9cfb9d98-89cb-4169-88e1-db399f3ce877").execute()
if res.data:
    print(json.dumps(res.data[0], ensure_ascii=False))
else:
    print("Col not found")
