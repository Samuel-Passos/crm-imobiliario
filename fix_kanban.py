import os
import uuid
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("scraper/.env")
client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# 1. Obter colunas existentes
res = client.table("kanban_colunas").select("*").execute()
colunas = {c["nome"]: c for c in res.data}

# 2. Atualizar ordens
# Expirados é 12
# Aceitou passará para 14
# Qualificação do Cadastro passará para 15
if "Aceitou" in colunas:
    client.table("kanban_colunas").update({"ordem": 14}).eq("id", colunas["Aceitou"]["id"]).execute()
if "Qualificação do Cadastro" in colunas:
    client.table("kanban_colunas").update({"ordem": 15}).eq("id", colunas["Qualificação do Cadastro"]["id"]).execute()

# 3. Criar "Cliente interagiu" na ordem 13
if "Cliente interagiu" not in colunas:
    novo_id = str(uuid.uuid4())
    client.table("kanban_colunas").insert({
        "id": novo_id,
        "nome": "Cliente interagiu",
        "ordem": 13
    }).execute()
    print("✅ Coluna 'Cliente interagiu' criada com sucesso! ID:", novo_id)
else:
    print("✅ Coluna 'Cliente interagiu' já existia. ID:", colunas["Cliente interagiu"]["id"])
