from scraper.config_db import supabase

res = supabase.table("imoveis").select("id, cidade, autorizado, kanban_coluna_id").neq("cidade", "São José dos Campos").execute()
imoveis = res.data

count_autorizado = sum(1 for i in imoveis if i.get("autorizado") is True)
count_nao_autorizado = sum(1 for i in imoveis if i.get("autorizado") is False)
count_nulo = sum(1 for i in imoveis if i.get("autorizado") is None)

print(f"Total fora SJC: {len(imoveis)}")
print(f"Autorizado (True): {count_autorizado}")
print(f"Não autorizado (False): {count_nao_autorizado}")
print(f"Nulo (None): {count_nulo}")

# Let's also check if there's any property (overall) with autorizado = True outside of SJC
