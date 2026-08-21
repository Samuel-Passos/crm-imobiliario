"""
dispatcher.py
─────────────
Lê os imóveis pendentes do Supabase e envia a mensagem inicial
via Evolution API (WhatsApp).

Critérios de seleção:
  - ultimo_contato IS NULL (nunca contactado), OU
  - proximo_contato <= hoje (follow-up agendado)
  E resposta IS NULL (ainda aguardando)

Uso:
  python dispatcher.py          # roda com configurações padrão do .env
  python dispatcher.py --dry    # simula envio sem chamar a API
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timezone, date
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

from config_manager import config_manager
from adb_client import AdbClient
from evolution_client import EvolutionClient
from buscar_link_imovel import buscar_link_imovel
from templates import mensagem_inicial

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DELAY_S      = int(os.getenv("DELAY_ENTRE_ENVIOS", 60))
LIMITE       = int(os.getenv("LIMITE_DIARIO", 30))
TABELA       = "atualizacao_disponibilidade"

PARAR_ROBO = False

def rodar_dispatcher(dry_run: bool = False, motor: str = "EVOLUTION", limite: int = None) -> dict:
    global PARAR_ROBO
    PARAR_ROBO = False

    config = config_manager.get_all()
    supabase = create_client(
        config.get("SUPABASE_URL") or os.getenv("SUPABASE_URL"),
        config.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY"),
    )
    if motor == "ADB":
        log.info("📱 Inicializando motor de envio: Celular Físico via ADB (WhatsApp)")
        cliente_zap = AdbClient()
    elif motor == "SMS":
        log.info("📨 Inicializando motor de envio: Celular Físico via ADB (SMS)")
        cliente_zap = AdbClient()
    else:
        log.info("⚡ Inicializando motor de envio: Evolution API (Background)")
        cliente_zap = EvolutionClient()
    
    # ── Buscar imóveis pendentes ────────────────────────────────────────
    log.info("Buscando imóveis pendentes...")
    
    # Pega configs dinâmicas
    default_delay = int(config.get("DELAY_ENTRE_ENVIOS", 60))
    default_limit = int(config.get("LIMITE_DIARIO", 30))
    
    # Se for SMS, podemos carregar limites específicos de SMS se necessário
    if motor == "SMS":
        default_limit = int(config.get("SMS_LIMIT_DAILY", 50))
    
    hoje = date.today().isoformat()
    resultado = (
        supabase.table(TABELA)
        .select("referencia, proprietario, telefone, preco, status, ultimo_contato, proximo_contato")
        .or_(f"ultimo_contato.is.null,proximo_contato.lte.{hoje}")
        .is_("resposta", "null")
        .limit(limite if limite else default_limit)
        .execute()
    )
    imoveis = resultado.data or []
    log.info(f"{len(imoveis)} imóvel(is) elegível(is) para contato hoje")

    resultados = {"enviados": 0, "sem_telefone": 0, "erros": 0}

    for idx, imovel in enumerate(imoveis):
        ref       = imovel["referencia"]
        prop      = imovel.get("proprietario") or ""
        telefone  = imovel.get("telefone") or ""

        # Pula sem telefone
        if not telefone:
            log.warning(f"[{ref}] Sem telefone — pulando")
            resultados["sem_telefone"] += 1
            continue

        if PARAR_ROBO:
            log.warning("🔴 Disparo interrompido manualmente pelo usuário.")
            break

        try:
            # 1. Buscar link do imóvel no site
            log.info(f"[{ref}] Buscando link no site...")
            link = buscar_link_imovel(ref)

            if link == "NOT_FOUND":
                log.info(f"[{ref}] Imóvel não consta no site. Marcando como indisponível no banco...")
                if not dry_run:
                    supabase.table(TABELA).update({
                        "status": "Indisponível (Removido do Site)",
                        "resposta": "NÃO",
                        "data_resposta": datetime.now(timezone.utc).isoformat(),
                    }).eq("referencia", ref).execute()
                continue

            # 2. Montar mensagem personalizada
            msg = mensagem_inicial(
                proprietario=prop,
                referencia=ref,
                link_imovel=link,
            )

            log.info(f"[{ref}] → {prop} ({telefone})")

            if dry_run:
                log.info(f"[DRY RUN] Mensagem que seria enviada:\n{msg}\n{'─'*60}")
            else:
                # 3. Enviar via motor escolhido
                if motor == "SMS":
                    cliente_zap.send_sms(telefone, msg)
                else:
                    # WhatsApp via Evolution API: Verificar se há mídias no texto
                    import re
                    # Procura padrões ![label](url), [video](url), [pdf](url)
                    media_patterns = [
                        (r'!\[.*?\]\((https?://.*?)\)', 'image'),
                        (r'\[video\]\((https?://.*?)\)', 'video'),
                        (r'\[pdf\]\((https?://.*?)\)', 'document'),
                    ]
                    
                    attachments = []
                    clean_msg = msg
                    for pattern, mtype in media_patterns:
                        matches = re.finditer(pattern, msg)
                        for m in matches:
                            attachments.append((m.group(1), mtype))
                            clean_msg = clean_msg.replace(m.group(0), "")

                    clean_msg = clean_msg.strip()
                    
                    if attachments:
                        # Envia o texto primeiro (ou como legenda se for só um, mas vamos enviar separado para garantir)
                        cliente_zap.send_text(telefone, clean_msg)
                        for url, mtype in attachments:
                            cliente_zap.send_media(telefone, url, mediatype=mtype)
                    else:
                        cliente_zap.send_text(telefone, msg)

                # 4. Atualizar ultimo_contato no banco
                supabase.table(TABELA).update({
                    "ultimo_contato": datetime.now(timezone.utc).isoformat(),
                }).eq("referencia", ref).execute()

            resultados["enviados"] += 1

        except Exception as e:
            log.error(f"[{ref}] Erro: {e}")
            resultados["erros"] += 1
            continue

        # Delay entre envios (menos no último)
        if idx < len(imoveis) - 1:
            delay_calculado = default_delay
            if motor == "SMS":
                 # Opcional: usar delay randômico do config_manager para SMS
                 min_d = int(config.get("SMS_DELAY_MIN", 60))
                 max_d = int(config.get("SMS_DELAY_MAX", 180))
                 import random
                 delay_calculado = random.randint(min_d, max_d)
            
            log.info(f"Aguardando {delay_calculado}s antes do próximo envio...")
            time.sleep(delay_calculado)

    # ── Resumo ──────────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"  RESUMO DO DISPATCHER{' (DRY RUN)' if dry_run else ''}")
    print(f"{'='*50}")
    print(f"  Mensagens enviadas  : {resultados['enviados']}")
    print(f"  Sem telefone        : {resultados['sem_telefone']}")
    print(f"  Erros               : {resultados['erros']}")
    print(f"{'='*50}\n")

    return resultados


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dispatcher do Robô de Disponibilidade")
    parser.add_argument("--dry", action="store_true", help="Simula sem enviar mensagens reais")
    parser.add_argument("--motor", default="EVOLUTION", choices=["EVOLUTION", "ADB", "SMS"], help="Motor de envio (EVOLUTION, ADB ou SMS)")
    parser.add_argument("--limit", type=int, help="Limite de mensagens para este disparo")
    args = parser.parse_args()
    
    rodar_dispatcher(dry_run=args.dry, motor=args.motor, limite=args.limit)
