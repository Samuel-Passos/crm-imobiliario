import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = sup.table('imoveis').select('id, kanban_coluna_id').in_('id', [3845, 3847, 3846]).execute()
print("Imoveis:", res.data)

res_colunas = sup.table('kanban_colunas').select('id, nome').execute()
print("Colunas:", res_colunas.data)
