import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# get col names
cols = sup.table('kanban_colunas').select('id, nome, ordem').execute()
col_map = {c['id']: c['nome'] for c in cols.data}

print("Últimos 20 cartões modificados:")
res = sup.table('imoveis').select('id, titulo, kanban_coluna_id, url').order('id', desc=True).limit(20).execute()
for r in res.data:
    col = col_map.get(r['kanban_coluna_id'], str(r['kanban_coluna_id']))
    print(f"ID {r['id']} - {r['titulo'][:30]}... -> Kanban: {col}")

