from scraper.config_db import supabase

# Properties with georeferencing
res = supabase.table("imoveis").select("id, cidade, kanban_coluna_id").not_.is_("latitude", "null").not_.is_("longitude", "null").execute()
imoveis = res.data

total = len(imoveis)
print(f"Total de imóveis com georeferenciamento: {total}")

cidades = {}
kanbans = {}

for imovel in imoveis:
    c = imovel.get("cidade")
    k = imovel.get("kanban_coluna_id")
    cidades[c] = cidades.get(c, 0) + 1
    kanbans[k] = kanbans.get(k, 0) + 1

print("\nPor cidade:")
for c, count in cidades.items():
    print(f" - {c}: {count}")

print("\nPor kanban_coluna_id:")
for k, count in kanbans.items():
    print(f" - {k}: {count}")

# Let's map kanban_coluna_id to names
kanban_res = supabase.table("kanban_colunas").select("id, nome").execute()
kanban_map = {k["id"]: k["nome"] for k in kanban_res.data}

print("\nPor kanban (nome):")
for k, count in kanbans.items():
    nome = kanban_map.get(k, "Desconhecido")
    print(f" - {nome}: {count}")

