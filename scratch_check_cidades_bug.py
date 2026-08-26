import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

res = sup.table('imoveis').select('id, cidade, bairro').in_('id', [3845, 3847, 3846]).execute()
print(res.data)
