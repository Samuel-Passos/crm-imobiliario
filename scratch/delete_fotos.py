import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("/home/samuel/Desktop/Scraper_antigravity/scraper/.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)
BUCKET_NAME = "imoveis_fotos"

# Busca todos os imoveis que tem fotos baixadas, exceto o 3603
res = supabase.table("imoveis").select("id, list_id, fotos").eq("fotos_baixadas", True).neq("id", 3603).execute()

imoveis_para_limpar = res.data or []
print(f"Encontrados {len(imoveis_para_limpar)} imóveis para limpar as fotos.")

for imovel in imoveis_para_limpar:
    list_id = imovel["list_id"]
    id_banco = imovel["id"]
    
    # 1. Apagar os arquivos do Storage
    # Primeiro listamos os arquivos na pasta do imovel
    try:
        lista_arquivos = supabase.storage.from_(BUCKET_NAME).list(list_id)
        if lista_arquivos:
            arquivos_para_apagar = [f"{list_id}/{arq['name']}" for arq in lista_arquivos if arq['name'] != '.emptyFolderPlaceholder']
            if arquivos_para_apagar:
                supabase.storage.from_(BUCKET_NAME).remove(arquivos_para_apagar)
                print(f"[{list_id}] Apagados {len(arquivos_para_apagar)} arquivos do Storage.")
    except Exception as e:
        print(f"[{list_id}] Erro ao apagar do Storage: {e}")

    # 2. Atualizar o banco de dados
    try:
        supabase.table("imoveis").update({
            "fotos": [],
            "foto_capa": None,
            "fotos_baixadas": False
        }).eq("id", id_banco).execute()
        print(f"[{list_id}] Banco de dados resetado (fotos removidas).")
    except Exception as e:
        print(f"[{list_id}] Erro ao atualizar o banco: {e}")

print("Concluído!")
