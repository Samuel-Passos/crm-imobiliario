import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("imoveis").select("id, cidade").in_("id", [3825, 3826, 3827]).execute()
print(res.data)
