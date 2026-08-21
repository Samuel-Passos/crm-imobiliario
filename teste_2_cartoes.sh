#!/bin/bash
echo "=== 1. ONDA REVERSA (2 CARTOES) ==="
scraper/.venv/bin/python robo_chat_prospeccao/orquestrador_reverso.py --lote 2

echo "=== 2. FASE 1 (1 PAGINA) ==="
scraper/.venv/bin/python olx_captacao/fase1_coleta_links.py --max-paginas 1

echo "=== 3. FASE 2 (2 CARTOES) ==="
scraper/.venv/bin/python olx_captacao/fase2_extrai_dados.py --lote 2

echo "=== 4. FASE 2.5 (FILTRO RÁPIDO) ==="
scraper/.venv/bin/python olx_captacao/fase2_5_filtro_mercado.py

echo "=== 5. FASE 3 (TELEFONE - 2 CARTOES) ==="
scraper/.venv/bin/python olx_captacao/fase3_extrai_telefone_em_lote.py --lote 2

echo "=== TESTE DE 2 CARTOES CONCLUIDO ==="
