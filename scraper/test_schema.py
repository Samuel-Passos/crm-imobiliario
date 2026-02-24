from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv(".env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
if url and key:
    supabase: Client = create_client(url, key)
    res = supabase.table("imoveis").select("id, titulo, telefone_pesquisado, anuncio_expirado").limit(1).execute()
    print("Record matches URL:", res.data)
else:
    print("Could not find SUPABASE env logic.")
