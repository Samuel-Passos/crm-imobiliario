from scraper.config_db import supabase

# Query total count
res_total = supabase.table("imoveis").select("id", count="exact").execute()
total_imoveis = res_total.count if res_total.count is not None else 0

# Query count for authorized
res_auth = supabase.table("imoveis").select("id", count="exact").eq("autorizado", True).execute()
total_autorizados = res_auth.count if res_auth.count is not None else 0

print(f"Total absoluto de imóveis: {total_imoveis}")
print(f"Total de imóveis autorizados: {total_autorizados}")
