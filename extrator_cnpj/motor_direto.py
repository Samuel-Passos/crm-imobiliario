import sys
import os
import time
import re
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Caminho do projeto
PROJECT_ROOT = Path("/home/samuel/Desktop/Scraper_antigravity")
sys.path.append(str(PROJECT_ROOT / "extrator_cnpj"))

from pipeline import enriquecer_receitaws_individual
from supabase import create_client

# Carrega env
load_dotenv(PROJECT_ROOT / "extrator_cnpj" / ".env")

def run_motor_direto(limit=180, delay=21):
    """
    Executa o enriquecimento direto (sem proxy) com limite de 3 req/min (delay de ~20s).
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase = create_client(url, key)

    print(f"\n--- [MOTOR DIRETO] INICIADO ---")
    print(f"Objetivo: {limit} leads | Ritmo: 1 req a cada {delay}s (~3/min)")
    print(f"Início: {datetime.now().strftime('%H:%M:%S')}")
    
    # Busca CNPJs pendentes
    try:
        res = supabase.table("empresas_sjc") \
            .select("cnpj") \
            .neq("status", "enriquecido_premium") \
            .limit(limit) \
            .execute()
        cnpjs = [d['cnpj'] for d in res.data]
    except Exception as e:
        print(f"Erro ao buscar leads no Supabase: {e}")
        return

    if not cnpjs:
        print("Nenhum lead pendente encontrado.")
        return

    print(f"Total de Leads para processar: {len(cnpjs)}")

    # Log file
    log_file = PROJECT_ROOT / "extrator_cnpj" / "output" / "motor_direto.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    success = 0
    errors = 0
    start_time = time.time()

    with open(log_file, "a") as f_log:
        f_log.write(f"\n--- Sessão do Motor Direto iniciada em {datetime.now().isoformat()} ---\n")

        for i, cnpj in enumerate(cnpjs):
            cnpj_clean = re.sub(r"\D", "", str(cnpj))
            
            progresso = ((i+1)/len(cnpjs)) * 100
            print(f"[{i+1}/{len(cnpjs)}] {cnpj_clean} ({progresso:.1f}%) ...", end="", flush=True)
            
            try:
                # Chama com ignore_proxy=True
                enriquecer_receitaws_individual(cnpj_clean, ignore_proxy=True)
                print(" OK", flush=True)
                success += 1
                f_log.write(f"{datetime.now().strftime('%H:%M:%S')} | {cnpj_clean}: SUCESSO\n")
            except Exception as e:
                print(f" ERRO -> {str(e)[:40]}", flush=True)
                errors += 1
                f_log.write(f"{datetime.now().strftime('%H:%M:%S')} | {cnpj_clean}: ERRO -> {str(e)}\n")
                
                # Se for 429 (Too Many Requests), vamos ser gentis e esperar mais
                if "429" in str(e):
                    print("!!! Limite da API atingido. Aguardando 60s extras...")
                    time.sleep(60)

            # Pausa obrigatória para manter os 3 req/min
            if i < len(cnpjs) - 1:
                time.sleep(delay)

    duration = time.time() - start_time
    summary = f"""
==================================================
MOTOR DIRETO FINALIZADO
Sucessos: {success}
Erros: {errors}
Duração: {duration/60:.2f} min
==================================================
"""
    print(summary)
    with open(log_file, "a") as f_log:
        f_log.write(summary)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Motor Direto de Enriquecimento ReceitaWS")
    parser.add_argument("--limit", type=int, default=180, help="Limite de empresas")
    parser.add_argument("--delay", type=int, default=21, help="Intervalo entre requisições (s)")
    args = parser.parse_args()
    
    run_motor_direto(limit=args.limit, delay=args.delay)

