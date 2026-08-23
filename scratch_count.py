import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

print("=== PROGRESSO DA FASE 3 ===")
res_total = supabase.table("imoveis").select("id").execute()
print(f"Total de imóveis na base: {len(res_total.data)}")

res_pesquisados = supabase.table("imoveis").select("id, titulo, telefones_extraidos").eq("telefone_pesquisado", True).order("id", desc=True).limit(10).execute()
print(f"Últimos 10 pesquisados:")
for imovel in res_pesquisados.data:
    tels = len(imovel.get('telefones_extraidos') or [])
    print(f"ID {imovel['id']}: {imovel['titulo'][:30]}... -> Achou {tels} telefones")
