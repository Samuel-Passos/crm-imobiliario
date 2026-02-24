import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("links_anuncios").select("url").limit(3).execute()
for r in res.data:
    print(r["url"])
