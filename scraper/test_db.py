from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv(".env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
if url and key:
    supabase: Client = create_client(url, key)
    res = supabase.table("imoveis").select("id", "url", "telefone", "telefones_extraidos").eq("url", "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/apartamento-condominio-santa-isabel-1479955272").execute()
    print("Record matches URL:", res.data)
else:
    print("Could not find SUPABASE env logic.")
