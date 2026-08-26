import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Rename the column
res = sup.table("kanban_colunas").update({"nome": "Prontos para OLX Chat (Script 1)"}).eq("nome", "Extração de Telefone").execute()
if res.data:
    print(f"✅ Coluna renomeada com sucesso: {res.data[0]['nome']}")
else:
    print("⚠️ Coluna 'Extração de Telefone' não encontrada. Talvez já tenha sido renomeada?")
