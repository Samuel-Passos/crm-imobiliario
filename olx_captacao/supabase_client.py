"""
supabase_client.py
------------------
Cliente Supabase compartilhado entre todos os módulos de captação OLX.
Inicializa com SUPABASE_URL e SUPABASE_KEY do .env local.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega o .env da pasta olx_captacao (não do /scraper/)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_env_path)

_url = os.getenv("SUPABASE_URL")
_key = os.getenv("SUPABASE_KEY")

if not _url or not _key:
    raise ValueError(
        "SUPABASE_URL e SUPABASE_KEY precisam estar definidos no .env da pasta olx_captacao/"
    )

supabase: Client = create_client(_url, _key)
