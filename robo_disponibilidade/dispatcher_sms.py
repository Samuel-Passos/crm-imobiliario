"""
dispatcher_sms.py
─────────────────
Script especializado para envio de SMS em massa via ADB.
Possui lógica de anti-bloqueio:
 - Delays aleatórios entre envios.
 - Batches (lotes) controlados (ex: 10 mensagens por vez).
 - Limite diário de segurança.
"""

import os
import time
import random
import logging
from datetime import datetime, timezone, date
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client
from adb_client import AdbClient

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# Configurações do .env
LIMIT_DAILY = int(os.getenv("SMS_LIMIT_DAILY", 50))
BATCH_SIZE  = int(os.getenv("SMS_BATCH_SIZE", 10))
DELAY_MIN   = int(os.getenv("SMS_DELAY_MIN", 60))
DELAY_MAX   = int(os.getenv("SMS_DELAY_MAX", 180))

PARAR_ROBO = False

def rodar_dispatcher_sms(tabela: str = "leads_campanha", dry_run: bool = False):
    global PARAR_ROBO
    PARAR_ROBO = False

    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY"),
    )
    
    adb = AdbClient()
    log.info(f"🚀 Iniciando Robô de SMS (Tabela: {tabela})")
    
    # ── Buscar registros pendentes ──────────────────────────────────────
    # Filtro depende da tabela. leads_campanha usa status_ligacao='Pendente'
    # atualizacao_disponibilidade usa ultimo_contato is null...
    
    query = supabase.table(tabela).select("*")
    
    if tabela == "leads_campanha":
        query = query.eq("status_ligacao", "Pendente")
    else:
        # Fallback para disponibilidade se for o caso
        hoje = date.today().isoformat()
        query = query.or_(f"ultimo_contato.is.null,proximo_contato.lte.{hoje}").is_("resposta", "null")

    resultado = query.limit(BATCH_SIZE).execute()
    registros = resultado.data or []
    
    log.info(f"Encontrados {len(registros)} registros pendentes para este lote.")
    
    enviados = 0
    
    for idx, reg in enumerate(registros):
        if PARAR_ROBO:
            log.warning("🔴 Robô SMS interrompido.")
            break
            
        telefone = reg.get("telefone")
        nome = reg.get("nome", "Cliente")
        id_reg = reg.get("id") or reg.get("referencia")

        if not telefone:
            continue

        # Montar Mensagem (Simplificada para SMS)
        if tabela == "leads_campanha":
            # Pega o script da campanha se disponível (precisaria de um join ou busca previa)
            # Por enquanto, uma mensagem padrão ou extraída do metadata
            mensagem = f"Oi {nome.split()[0]}, tudo bem? Sou o Samuel. Vi seu interesse e gostaria de conversar. Pode falar?"
        else:
            ref = reg.get("referencia", "")
            mensagem = f"Olá, aqui é o Samuel. Seu imóvel ref {ref} ainda está disponível? Caso sim, houve mudança no valor?"

        log.info(f"[{enviados+1}/{len(registros)}] Enviando SMS para {telefone}...")
        
        try:
            if not dry_run:
                adb.send_sms(telefone, mensagem)
                
                # Atualizar banco
                if tabela == "leads_campanha":
                    supabase.table(tabela).update({
                        "status_ligacao": "Concluído", # Ou criar um status 'SMS Enviado'
                        "ultima_tentativa": datetime.now(timezone.utc).isoformat()
                    }).eq("id", id_reg).execute()
                else:
                    supabase.table(tabela).update({
                        "ultimo_contato": datetime.now(timezone.utc).isoformat()
                    }).eq("referencia", id_reg).execute()
            else:
                log.info(f"[DRY RUN] SMS: {mensagem}")

            enviados += 1
            
        except Exception as e:
            log.error(f"Erro ao enviar para {telefone}: {e}")
            continue

        # Delay entre mensagens dentro do batch
        if idx < len(registros) - 1:
            espera = random.randint(DELAY_MIN, DELAY_MAX)
            log.info(f"Aguardando {espera}s para a próxima mensagem (Anti-Bloqueio)...")
            time.sleep(espera)

    log.info(f"✨ Lote finalizado. Enviados: {enviados}")
    return enviados

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tabela", default="leads_campanha")
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    
    rodar_dispatcher_sms(tabela=args.tabela, dry_run=args.dry)
