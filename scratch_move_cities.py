import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res_colunas = sup.table('kanban_colunas').select('id, nome').execute()
coluna_mercado = next((c['id'] for c in res_colunas.data if c['nome'] == 'Anúncios de Mercado'), None)

if coluna_mercado:
    sup.table('imoveis').update({'kanban_coluna_id': coluna_mercado}).in_('id', [3839, 3840, 3842]).execute()
    print("Movidos para Anúncios de Mercado!")
