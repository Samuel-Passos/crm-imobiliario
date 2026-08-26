from scraper.config_db import supabase

res = supabase.table("imoveis").select("*").limit(1).execute()
if res.data:
    print("Campos na tabela imoveis:")
    for k in res.data[0].keys():
        print(f" - {k}")
