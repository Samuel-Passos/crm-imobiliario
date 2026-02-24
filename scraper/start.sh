#!/bin/bash
echo "========================================="
echo "   Iniciando OLX Scraper Pro v1.0"
echo "========================================="

# Garante que as dependências existem
# O uv run cuida de instalar o que falta pelo pyproject.toml ou usar o .venv
export PATH="$HOME/.local/bin:$PATH"

# Iniciar o servidor FastAPI em background na porta 8765
echo "-> Iniciando FastAPI na porta 8765..."
uv run python main.py &
FASTAPI_PID=$!

# Aguarda 3 segundos para o servidor subir
sleep 3

# Inicia o Cron Job no terminal atual
echo "-> Iniciando Agendador (Cron) Diário..."
uv run python cron.py

# Se o cron cair ou for parado, mata o servidor FastAPI também
kill $FASTAPI_PID
echo "Scraper encerrado."
