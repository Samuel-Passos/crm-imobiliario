import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

res = supabase.table("imoveis").select("aceita_permuta, tipo_negocio").eq("ativo", True).execute()

permuta_counts = {}
negocio_counts = {}

for im in res.data:
    p = im.get("aceita_permuta")
    n = im.get("tipo_negocio")
    permuta_counts[p] = permuta_counts.get(p, 0) + 1
    negocio_counts[n] = negocio_counts.get(n, 0) + 1

print("Valores de aceita_permuta:", permuta_counts)
print("Valores de tipo_negocio:", negocio_counts)
