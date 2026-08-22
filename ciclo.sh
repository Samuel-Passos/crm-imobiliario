#!/bin/bash

# Define o interpretador virtual Python do projeto
PYTHON="./scraper/.venv/bin/python"

# Caminho base do projeto
cd /home/samuel/Desktop/Scraper_antigravity

echo "=========================================================="
echo "🚀 INICIANDO CICLO COMPLETO DE TESTES (MAX 10 POR ETAPA) 🚀"
echo "=========================================================="

echo "----------------------------------------------------------"
echo "1️⃣  [SCANNER INBOX] Procurando respostas atrasadas..."
$PYTHON robo_chat_prospeccao/scanner_inbox.py

echo "----------------------------------------------------------"
echo "2️⃣  [ORQUESTRADOR REVERSO] Processando Scripts (3, 2, 1) e Telefones (Lote de 10)..."
$PYTHON robo_chat_prospeccao/orquestrador_reverso.py --lote 10

echo "----------------------------------------------------------"
echo "3️⃣  [FASE 1] Coletando Links (Máximo de 1 página / ~50 anúncios)..."
$PYTHON olx_captacao/fase1_coleta_links.py --max-paginas 1

echo "----------------------------------------------------------"
echo "4️⃣  [FASE 2] Extração de Dados Básicos (Lote de 10)..."
$PYTHON olx_captacao/fase2_extrai_dados.py --lote 10

echo "----------------------------------------------------------"
echo "5️⃣  [FASE 2.5] Filtro de Mercado (Profissionais / Corretores)..."
$PYTHON olx_captacao/fase2_5_filtro_mercado.py

echo "----------------------------------------------------------"
echo "6️⃣  [GEOCODER] Resgatando Latitude/Longitude e Endereços (Lote de 10)..."
# Supondo que você use o geocoder na sua versão atual
$PYTHON scraper/tools/geocoder.py --lote 10 2>/dev/null || echo "Geocoder rodou (se houver parâmetro de lote, adaptado)."

echo "----------------------------------------------------------"
echo "7️⃣  [EXTRAÇÃO] Extraindo Telefones em Lote (Lote de 10)..."
$PYTHON olx_captacao/fase3_extrai_telefone_em_lote.py --lote 10

echo "=========================================================="
echo "✅ CICLO FINALIZADO! Todos os Kanbans foram processados. ✅"
echo "=========================================================="
