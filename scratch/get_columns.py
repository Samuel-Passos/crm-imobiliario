from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv("/home/samuel/Desktop/Scraper_antigravity/olx_captacao/.env")
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("kanban_colunas").select("id, nome").execute()
for c in res.data:
    print(c)
