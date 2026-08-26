import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res_col = sup.table("kanban_colunas").select("id").eq("nome", "Script 1").execute()
if res_col.data:
    col_id = res_col.data[0]['id']
    res_imoveis = sup.table("imoveis").select("id, titulo").eq("kanban_coluna_id", col_id).execute()
    print("Imóveis no Kanban 'Script 1':")
    for im in res_imoveis.data:
        print(f"[{im['id']}] {im['titulo']}")
else:
    print("Coluna 'Script 1' não encontrada.")
