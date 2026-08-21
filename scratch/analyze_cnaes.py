import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Configura paths
ROOT = Path(__file__).parent.parent
env_path = ROOT / "scraper" / ".env"
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def analyze():
    res = supabase.table('empresas_sjc').select('cnae, cnae_descricao').execute()
    stats = {}
    for r in res.data:
        cnae = r.get('cnae')
        desc = r.get('cnae_descricao') or 'Descrição não carregada'
        key = f"{cnae} | {desc}"
        stats[key] = stats.get(key, 0) + 1
    
    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:15]
    print("\n📊 TOP 15 ATIVIDADES NO BANCO DE DADOS:\n")
    for k, v in top:
        print(f"[{v:5} leads] - {k}")

if __name__ == "__main__":
    analyze()
