import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

print("=== ÚLTIMOS 3 IMÓVEIS (GERAL) ===")
res_recent = supabase.table("imoveis").select("id, titulo, rua, bairro, preco, latitude, longitude").order("id", desc=True).limit(3).execute()
for imovel in res_recent.data:
    print(json.dumps(imovel, indent=2, ensure_ascii=False))

print("\n=== ÚLTIMOS 3 IMÓVEIS COM TELEFONE EXTRAÍDO ===")
res_phones = supabase.table("imoveis").select("id, titulo, telefones_extraidos, telefone").eq("telefone_pesquisado", True).order("id", desc=True).limit(3).execute()
for imovel in res_phones.data:
    if imovel.get("telefones_extraidos") and len(imovel["telefones_extraidos"]) > 0:
        print(json.dumps(imovel, indent=2, ensure_ascii=False))
