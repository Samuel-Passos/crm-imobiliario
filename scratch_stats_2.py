from scraper.config_db import supabase

# Properties with georeferencing
res = supabase.table("imoveis").select("id, cidade, kanban_coluna_id").not_.is_("latitude", "null").not_.is_("longitude", "null").neq("cidade", "São José dos Campos").execute()
imoveis = res.data

# Let's map kanban_coluna_id to names
kanban_res = supabase.table("kanban_colunas").select("id, nome").execute()
kanban_map = {k["id"]: k["nome"] for k in kanban_res.data}

# Group by Kanban and City
kanban_counts = {}

for imovel in imoveis:
    c = imovel.get("cidade")
    k = imovel.get("kanban_coluna_id")
    nome_kanban = kanban_map.get(k, "Desconhecido")
    
    if nome_kanban not in kanban_counts:
        kanban_counts[nome_kanban] = {"total": 0, "cidades": {}}
        
    kanban_counts[nome_kanban]["total"] += 1
    if c:
        kanban_counts[nome_kanban]["cidades"][c] = kanban_counts[nome_kanban]["cidades"].get(c, 0) + 1

print(f"Total de imóveis (fora SJC) com georreferenciamento: {len(imoveis)}\n")

for k, data in kanban_counts.items():
    print(f"[{k}] - Total: {data['total']}")
    for c, count in data["cidades"].items():
        print(f"  - {c}: {count}")
    print("")
