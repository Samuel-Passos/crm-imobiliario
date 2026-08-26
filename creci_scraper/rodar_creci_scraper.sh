#!/bin/bash
# ============================================================
# CRECI-SP Scraper — Script de Execucao
# ============================================================
# Uso: ./rodar_creci_scraper.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/../scraper/.venv"
SCRAPER="$SCRIPT_DIR/scraper_creci.py"

echo "======================================================"
echo "  CRECI-SP Scraper — Human-in-the-Loop"
echo "======================================================"
echo ""
echo "O navegador sera aberto. Siga as instrucoes na tela."
echo ""

# Ativa o venv e roda o scraper
source "$VENV/bin/activate" && python3 "$SCRAPER"
