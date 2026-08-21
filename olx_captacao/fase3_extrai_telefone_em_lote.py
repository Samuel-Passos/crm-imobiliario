#!/usr/bin/env python3
# =============================================================================
# fase3_extrai_telefone_em_lote.py
# Casca para invocar o motor de extração de telefones do backend
# sem alterar sua lógica original.
# =============================================================================

import sys
import argparse
import asyncio
import os

# Adiciona a raiz do scraper ao sys.path para importar os módulos
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPER_DIR = os.path.join(ROOT_DIR, "scraper")
if SCRAPER_DIR not in sys.path:
    sys.path.append(SCRAPER_DIR)

from tools.browser_manager import start_browser, close_browser
from orchestrator import process_batch_phone_extraction

async def main(lote: int):
    print("=" * 60)
    print(f"🚀 INICIANDO FASE 3: EXTRAÇÃO DE TELEFONE EM LOTE (Limite: {lote})")
    print("=" * 60)
    
    print("Ligando o motor do navegador...")
    await start_browser()
    
    try:
        await process_batch_phone_extraction(lote=lote)
    except Exception as e:
        print(f"❌ Erro durante a extração: {e}")
    finally:
        print("Desligando o motor do navegador...")
        await close_browser()
        
    print("=" * 60)
    print("🏁 FASE 3 CONCLUÍDA")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extrator de telefones em massa.")
    parser.add_argument("--lote", type=int, default=10, help="Quantidade máxima de imóveis para processar por vez.")
    args = parser.parse_args()

    asyncio.run(main(args.lote))
