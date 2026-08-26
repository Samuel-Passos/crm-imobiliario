import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Get all tables
try:
    res = supabase.table("estatisticas_scraper").select("*").limit(1).execute()
    print("estatisticas_scraper cols:", list(res.data[0].keys()) if res.data else "empty")
except Exception as e:
    print("estatisticas_scraper error:", e)

try:
    res = supabase.table("logs_gerente_geral").select("*").limit(1).execute()
    print("logs_gerente_geral cols:", list(res.data[0].keys()) if res.data else "empty")
except Exception as e:
    print("logs_gerente_geral error:", e)

try:
    res = supabase.table("estatisticas_gerente").select("*").limit(1).execute()
    print("estatisticas_gerente cols:", list(res.data[0].keys()) if res.data else "empty")
except Exception as e:
    print("estatisticas_gerente error:", e)

