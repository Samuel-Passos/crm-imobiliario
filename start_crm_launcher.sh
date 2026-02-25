#!/bin/bash

# Script para iniciar o CRM Imobiliário e o Scraper
# Caminho base do projeto
PROJECT_ROOT="/home/samuel/Desktop/Scraper_antigravity"

# 1. Carregar NVM se existir para garantir que o npm/node funcionem
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Adicionar caminhos comuns ao PATH por segurança
export PATH="$HOME/.local/bin:$PATH"

echo "🚀 Iniciando CRM Imobiliário..."

# 2. Iniciar o Backend do Scraper (FastAPI)
echo "📦 Iniciando Scraper Backend na porta 8765..."
cd "$PROJECT_ROOT/scraper"
# Tenta usar o python do ambiente virtual ou uv
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python main.py &
elif command -v uv &> /dev/null; then
    uv run python main.py &
else
    python3 main.py &
fi
BACKEND_PID=$!

# 3. Iniciar o Frontend do CRM (Vite)
echo "💻 Iniciando CRM Frontend na porta 5173..."
cd "$PROJECT_ROOT/crm-imobiliario"
npm run dev &
FRONTEND_PID=$!

# 3. Aguardar um pouco para os serviços subirem
sleep 5

# 4. Abrir o navegador
echo "🌐 Abrindo o CRM no navegador..."
xdg-open "http://localhost:5173/kanban"

# Função para encerrar tudo ao fechar o terminal
cleanup() {
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID
    exit
}

trap cleanup SIGINT SIGTERM

# Mantém o script rodando para não matar os processos em background imediatamente
wait
