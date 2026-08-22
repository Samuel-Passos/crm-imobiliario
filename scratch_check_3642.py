from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv("scraper/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)
res = supabase.table("imoveis").select("*").eq("id", 3642).execute()
if res.data:
    print(json.dumps(res.data[0], indent=2, ensure_ascii=False))
else:
    print("Not found")
