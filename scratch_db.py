import os
from dotenv import load_dotenv
from supabase import create_client
load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
res = sup.table('imoveis').select('id, telefone_pesquisado, telefone_existe, contato').eq('id', 3631).execute()
print(res.data)
