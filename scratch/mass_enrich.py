import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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

def process_lead(cnpj):
    try:
        res = enriquecer_cnpj_individual(cnpj)
        return True if res else False
    except Exception as e:
        print(f"Erro no CNPJ {cnpj}: {e}")
        return False

def mass_enrich():
    print("🚀 Buscando leads que precisam de atualização...")
    # Busca leads que ainda não têm descrição de CNAE ou sócios processados
    res = supabase.table("empresas_sjc").select("cnpj").or_("tel_opencnpj.is.null,tel_opencnpj.eq.").limit(30000).execute()
    leads = [r['cnpj'] for r in res.data]
    
    total = len(leads)
    if total == 0:
        print("✅ Todos os leads já parecem estar enriquecidos!")
        return

    print(f"📦 Iniciando enriquecimento de {total} leads com 20 threads...")
    
    start_time = time.time()
    success = 0
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(process_lead, cnpj): cnpj for cnpj in leads}
        for i, future in enumerate(as_completed(futures)):
            if future.result():
                success += 1
            
            if i % 50 == 0:
                elapsed = time.time() - start_time
                speed = (i + 1) / elapsed
                eta = (total - i) / speed if speed > 0 else 0
                print(f"🔄 Progresso: {i}/{total} | Sucesso: {success} | Vel: {speed:.2f} leads/s | ETA: {eta/60:.1f} min")

    print(f"🏁 Finalizado! {success} leads atualizados em {time.time() - start_time:.1f} segundos.")

if __name__ == "__main__":
    mass_enrich()
