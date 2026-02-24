import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = supabase.table("imoveis").select("id, titulo, telefones_extraidos, telefone_pesquisado, anuncio_expirado").eq("telefone_pesquisado", True).order("scraped_at", desc=True).limit(5).execute()
for imovel in res.data:
    print(f"ID: {imovel['id']} | Título: {imovel['titulo']} | Pesquisado: {imovel['telefone_pesquisado']} | Expirado: {imovel['anuncio_expirado']} | Telefones: {imovel['telefones_extraidos']}")
