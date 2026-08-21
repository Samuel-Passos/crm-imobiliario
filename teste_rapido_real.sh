#!/bin/bash
echo "=== 1. ONDA REVERSA (VALENDO) ==="
scraper/.venv/bin/python robo_chat_prospeccao/orquestrador_reverso.py

echo "=== 2. FASE 1 (1 PAGINA) ==="
scraper/.venv/bin/python olx_captacao/fase1_coleta_links.py --max-paginas 1

echo "=== 3. FASE 2 (1 LOTE) ==="
scraper/.venv/bin/python olx_captacao/fase2_extrai_dados.py --lote 1

echo "=== 4. FASE 2.5 (FILTRO RÁPIDO) ==="
scraper/.venv/bin/python olx_captacao/fase2_5_filtro_mercado.py

echo "=== TESTE REAL CONCLUIDO ==="
