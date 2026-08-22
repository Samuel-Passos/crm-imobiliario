import os
from dotenv import load_dotenv
from supabase import create_client
from collections import Counter

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# get col names
cols = sup.table('kanban_colunas').select('id, nome, ordem').execute()
cols_sorted = sorted(cols.data, key=lambda x: x['ordem'])
col_map = {c['id']: c['nome'] for c in cols_sorted}

# count imoveis per col
res = sup.table('imoveis').select('kanban_coluna_id').execute()
counts = Counter([r['kanban_coluna_id'] for r in res.data])

print("Resumo do Kanban (Imóveis por Coluna):")
print("-" * 60)
for c in cols_sorted:
    k_id = c['id']
    title = c['nome']
    count = counts.get(k_id, 0)
    print(f"[{c['ordem']}] {title}: {count} cartões")

# For unknown ones
unknowns = {k: v for k, v in counts.items() if k not in col_map}
for k, v in unknowns.items():
    if k is None:
        print(f"[?] Sem coluna (None): {v} cartões")
    else:
        print(f"[?] Desconhecido ({k}): {v} cartões")
print("-" * 60)
