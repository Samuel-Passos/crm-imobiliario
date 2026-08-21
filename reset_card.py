import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("scraper/.env")
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Move o cartao 1525441605 de volta para "Extracao de Telefone" para teste do chat
supabase.table("imoveis").update({
    "anuncio_expirado": False,
    "kanban_coluna_id": "9cfb9d98-89cb-4169-88e1-db399f3ce877"
}).eq("list_id", 1525441605).execute()
print("Card resetado com sucesso!")
