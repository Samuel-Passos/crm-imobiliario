import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = sup.table("kanban_colunas").update({"nome": "Extração de Telefone"}).eq("nome", "Prontos para OLX Chat (Script 1)").execute()
if res.data:
    print(f"✅ Coluna revertida com sucesso: {res.data[0]['nome']}")
