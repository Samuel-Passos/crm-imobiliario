from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("imoveis").select("fotos, foto_capa, id").limit(50).execute()
for r in res.data:
    if r.get("fotos"):
        print(r)
        break
