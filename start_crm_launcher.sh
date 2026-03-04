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

# 2. Matar processos antigos que possam estar presos na porta 8765
echo "🔄 Verificando processos anteriores na porta 8765..."
OLD_PIDS=$(lsof -ti :8765 2>/dev/null)
if [ -n "$OLD_PIDS" ]; then
    echo "   ⚠️  Processo antigo encontrado (PID: $OLD_PIDS). Encerrando..."
    kill -9 $OLD_PIDS 2>/dev/null
    sleep 1
    echo "   ✅ Processo antigo encerrado."
else
    echo "   ✅ Porta 8765 livre."
fi

# 3. Iniciar o Backend do Scraper (FastAPI)
echo "📦 Iniciando Scraper Backend na porta 8765..."
cd "$PROJECT_ROOT/scraper"
if [ -f ".venv/bin/uvicorn" ]; then
    .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8765 --no-access-log &
elif command -v uv &> /dev/null; then
    uv run uvicorn main:app --host 0.0.0.0 --port 8765 --no-access-log &
else
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8765 --no-access-log &
fi
BACKEND_PID=$!
echo "   ✅ Backend iniciado (PID: $BACKEND_PID)"

# 4. Iniciar o Frontend do CRM (Vite)
echo "💻 Iniciando CRM Frontend na porta 5173..."
cd "$PROJECT_ROOT/crm-imobiliario"
npm run dev &
FRONTEND_PID=$!
echo "   ✅ Frontend iniciado (PID: $FRONTEND_PID)"

# 5. Aguardar os serviços subirem
echo "⏳ Aguardando serviços iniciarem (5s)..."
sleep 5

# 6. Verificar se o backend de fato subiu
if curl -s http://localhost:8765/status > /dev/null 2>&1; then
    echo "   ✅ FastAPI respondendo na porta 8765!"
else
    echo "   ⚠️  FastAPI ainda não respondeu — verifique o log acima."
fi

# 7. Abrir o navegador
echo "🌐 Abrindo o CRM no navegador..."
xdg-open "http://localhost:5173/kanban"

# Função para encerrar tudo ao fechar o terminal
cleanup() {
    echo ""
    echo "🛑 Encerrando serviços..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "   Serviços encerrados. Até logo!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Mantém o script rodando (Ctrl+C encerra tudo)
echo ""
echo "============================================"
echo "  CRM em execução. Pressione Ctrl+C para encerrar tudo."
echo "============================================"
wait
