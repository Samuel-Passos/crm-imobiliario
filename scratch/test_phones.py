import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Configura paths
ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT / "extrator_cnpj"))
env_path = ROOT / "scraper" / ".env"
load_dotenv(env_path)

from pipeline import enriquecer_cnpj_individual
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def test_10_leads():
    print("🧪 BUSCANDO 10 LEADS PARA TESTE...")
    # Pega leads que estão com tel_opencnpj nulo
    res = supabase.table('empresas_sjc').select('cnpj, tel_opencnpj, telefone_completo_1').or_("tel_opencnpj.is.null,tel_opencnpj.eq.").limit(10).execute()
    leads = res.data
    
    if not leads:
        print("❌ Nenhum lead sem telefone encontrado para o teste.")
        return

    print(f"✅ Encontrados {len(leads)} leads. Iniciando enriquecimento...\n")
    
    for l in leads:
        cnpj = l['cnpj']
        print(f"--- CNPJ: {cnpj} ---")
        print(f"  ANTES  | OpenCNPJ: '{l.get('tel_opencnpj')}' | Contato1: '{l.get('telefone_completo_1')}'")
        
        # Roda o enriquecimento
        enriquecer_cnpj_individual(cnpj)
        
        # Busca como ficou
        pos = supabase.table('empresas_sjc').select('tel_opencnpj, telefone_completo_1').eq('cnpj', cnpj).execute().data[0]
        print(f"  DEPOIS | OpenCNPJ: '{pos.get('tel_opencnpj')}' | Contato1: '{pos.get('telefone_completo_1')}'")
        print("-" * 40)

if __name__ == "__main__":
    test_10_leads()
