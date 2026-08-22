from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv("scraper/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

ids = [3642,3643,3644,3645,3646,3647,3648,3649,3650,3651]
for i in ids:
    res = supabase.table("imoveis").update({"telefone_pesquisado": False}).eq("id", i).execute()
print("Reseted telefones_pesquisado for 10 ids")
