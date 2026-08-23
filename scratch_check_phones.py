import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

res = supabase.table("imoveis").select("id, telefone_existe, telefone, telefones_extraidos").eq("ativo", True).execute()

com_telefone_existe = 0
com_telefone_campo = 0
com_telefones_extraidos = 0
qualquer_telefone = 0

for im in res.data:
    t_existe = im.get("telefone_existe")
    t_campo = im.get("telefone")
    t_extraidos = im.get("telefones_extraidos")
    
    if t_existe:
        com_telefone_existe += 1
    if t_campo:
        com_telefone_campo += 1
    if t_extraidos and len(t_extraidos) > 0:
        com_telefones_extraidos += 1
        
    if t_existe or t_campo or (t_extraidos and len(t_extraidos) > 0):
        qualquer_telefone += 1

print(f"Total imoveis ativos: {len(res.data)}")
print(f"telefone_existe == True: {com_telefone_existe}")
print(f"telefone (campo) preenchido: {com_telefone_campo}")
print(f"telefones_extraidos com itens: {com_telefones_extraidos}")
print(f"Algum destes verdadeiro: {qualquer_telefone}")
