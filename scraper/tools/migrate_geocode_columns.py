"""
Cria as colunas geocode_strategy e geocode_needs_review na tabela imoveis (se não existirem).
Execute apenas uma vez.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Supabase SDK não tem DDL, então usamos RPC ou simplesmente testamos via update em um campo existente.
# Vamos usar a API de configuração para adicionar as colunas via SQL (rpc).
sql_add_columns = """
ALTER TABLE imoveis 
  ADD COLUMN IF NOT EXISTS geocode_strategy TEXT,
  ADD COLUMN IF NOT EXISTS geocode_needs_review BOOLEAN DEFAULT FALSE;
"""

try:
    result = supabase.rpc('exec_sql', {'sql': sql_add_columns}).execute()
    print("✅ Colunas criadas via RPC.")
    print(result)
except Exception as e:
    print(f"RPC não disponível ou erro: {e}")
    print()
    print("📋 Execute o seguinte SQL diretamente no Supabase SQL Editor:")
    print("-" * 60)
    print(sql_add_columns)
    print("-" * 60)
    print("Depois rode novamente: .venv/bin/python tools/geocoder_reprocess.py")
