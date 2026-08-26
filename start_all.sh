#!/bin/bash
# =============================================================================
# start_all.sh — Sobe todos os serviços do sistema CRM Imobiliário
#   1. Scraper Backend  (FastAPI porta 8765)
#   2. Robô Disponibilidade (FastAPI + Cloudflare, porta 8766)
#   3. API do Captador OLX (porta 8768)
#   4. CRM Frontend  (Vite porta 5173)
# =============================================================================

PROJECT_ROOT="/home/samuel/Desktop/Scraper_antigravity"

# ── Cores para o terminal ────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Carrega NVM/node ─────────────────────────────────────────────────────────
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║     🏠  CRM Imobiliário — Iniciando Tudo     ║${NC}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Encerra processos anteriores ─────────────────────────────────────────────
echo -e "${YELLOW}🔄 Encerrando serviços anteriores...${NC}"
pkill -f "uvicorn main:app"       2>/dev/null
pkill -f "uvicorn server:app"     2>/dev/null
pkill -f "cloudflared tunnel"     2>/dev/null
pkill -f "api_captador.py"      2>/dev/null
pkill -f "fase3_baixar_fotos_aceitou.py" 2>/dev/null
pkill -f "orquestrador_reverso.py"        2>/dev/null
pkill -f "vite"                   2>/dev/null
# Libera portas
for PORT in 8765 8766 8768 5173; do
    PIDS=$(lsof -ti :$PORT 2>/dev/null)
    [ -n "$PIDS" ] && kill -9 $PIDS 2>/dev/null
done
sleep 1
echo -e "${GREEN}   ✅ Portas liberadas (8765, 8766, 8768, 5173)${NC}"

# ── Trap: encerra tudo ao pressionar Ctrl+C ───────────────────────────────────
cleanup() {
    echo ""
    echo -e "${RED}🛑 Encerrando todos os serviços...${NC}"
    pkill -f "uvicorn main:app"   2>/dev/null
    pkill -f "uvicorn server:app" 2>/dev/null
    pkill -f "cloudflared tunnel" 2>/dev/null
    pkill -f "vite"               2>/dev/null
    pkill -f "api_captador.py"    2>/dev/null
    pkill -f "fase3_baixar_fotos_aceitou.py" 2>/dev/null
    echo -e "${GREEN}   Tudo encerrado. Até logo!${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── 1. Scraper Backend (porta 8765) ──────────────────────────────────────────
echo ""
echo -e "${CYAN}📦 [1/3] Iniciando Scraper Backend (porta 8765)...${NC}"
cd "$PROJECT_ROOT/scraper"
if [ -f ".venv/bin/uvicorn" ]; then
    .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8765 --no-access-log > /tmp/scraper.log 2>&1 &
elif command -v uv &> /dev/null; then
    uv run uvicorn main:app --host 0.0.0.0 --port 8765 --no-access-log > /tmp/scraper.log 2>&1 &
else
    python3 -m uvicorn main:app --host 0.0.0.0 --port 8765 --no-access-log > /tmp/scraper.log 2>&1 &
fi
SCRAPER_PID=$!
echo -e "${GREEN}   ✅ Scraper iniciado (PID: $SCRAPER_PID)${NC}"

# ── 2. Robô Disponibilidade (porta 8766) ─────────────────────────────────────
echo ""
echo -e "${CYAN}🤖 [2/3] Iniciando Robô de Disponibilidade (porta 8766)...${NC}"
cd "$PROJECT_ROOT/robo_disponibilidade"
source .venv/bin/activate
export PYTHONPATH=.

# Inicia tunnel em background
iniciar_tunnel_bg() {
    while true; do
        > cloudflared.log
        cloudflared tunnel --url http://127.0.0.1:8766 >> cloudflared.log 2>&1 &
        CFPID=$!
        count=0; EXT_URL=""
        while [ $count -lt 30 ]; do
            EXT_URL=$(grep -o "https://[a-zA-Z0-9-]*\.trycloudflare\.com" cloudflared.log | head -n 1)
            [ -n "$EXT_URL" ] && break
            sleep 1; count=$((count+1))
        done
        if [ -n "$EXT_URL" ]; then
            curl -s -X POST http://127.0.0.1:8766/webhook/registrar \
                -H "Content-Type: application/json" \
                -d "{\"url\": \"${EXT_URL}/webhook\"}" > /dev/null 2>&1 || true
            wait $CFPID
        else
            kill $CFPID 2>/dev/null
        fi
        sleep 10
    done
}

iniciar_tunnel_bg &

uvicorn server:app --host 0.0.0.0 --port 8766 --log-level warning > /tmp/robo.log 2>&1 &
ROBO_PID=$!
echo -e "${GREEN}   ✅ Robô iniciado (PID: $ROBO_PID)${NC}"
deactivate 2>/dev/null || true

# ── 3. API Captador OLX (porta 8768) ──────────────────────────────────────────
echo ""
echo -e "${CYAN}🤖 [3/4] Iniciando API Captador OLX (porta 8768)...${NC}"
cd "$PROJECT_ROOT/olx_captacao"
nohup ./api_captador.py > /tmp/api_captador.log 2>&1 &
CAPTADOR_PID=$!
echo -e "${GREEN}   ✅ Captador iniciado (PID: $CAPTADOR_PID)${NC}"

# ── Robô de Download de Fotos ────────────────────────────────────────────────
echo ""
echo -e "${CYAN}📸 Iniciando Robô de Download de Fotos (Background)...${NC}"
nohup .venv/bin/python -u fase3_baixar_fotos_aceitou.py > /tmp/robo_fotos.log 2>&1 &
ROBO_FOTOS_PID=$!
echo -e "${GREEN}   ✅ Robô de Fotos iniciado (PID: $ROBO_FOTOS_PID)${NC}"

# ── Monitor de Chat OLX (Drip Campaign) ──────────────────────────────────────
echo ""
echo -e "${CYAN}💬 Iniciando Monitor de Chat (Workspace 3)...${NC}"
cd "$PROJECT_ROOT/robo_chat_prospeccao"
nohup python3 -u orquestrador_reverso.py > /tmp/robo_chat.log 2>&1 &
MONITOR_CHAT_PID=$!
echo -e "${GREEN}   ✅ Monitor de Chat iniciado (PID: $MONITOR_CHAT_PID)${NC}"

# ── 4. CRM Frontend (porta 5173) ─────────────────────────────────────────────
echo ""
echo -e "${CYAN}💻 [4/4] Iniciando CRM Frontend (porta 5173)...${NC}"
cd "$PROJECT_ROOT/crm-imobiliario"
npm run dev > /tmp/crm_frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}   ✅ Frontend iniciado (PID: $FRONTEND_PID)${NC}"

# ── 5. Tunnel loca.lt (acesso remoto fixo) ───────────────────────────────────
echo ""
echo -e "${CYAN}🌐 [4/4] Iniciando tunnel remoto (samuel.loca.lt)...${NC}"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
pkill -f "lt --port 5173" 2>/dev/null
sleep 1
nohup lt --port 5173 --subdomain samuel > /tmp/tunnel_crm.log 2>&1 &
TUNNEL_PID=$!
sleep 3
TUNNEL_URL=$(grep -o 'https://[^ ]*' /tmp/tunnel_crm.log | head -1)
if [ -n "$TUNNEL_URL" ]; then
    echo -e "${GREEN}   ✅ Tunnel ativo: ${BOLD}${TUNNEL_URL}${NC}"
    echo -e "${YELLOW}   ℹ️  Senha de bypass (primeira visita): $(curl -s https://loca.lt/mytunnelpassword)${NC}"
else
    echo -e "${YELLOW}   ⚠️  Tunnel ainda iniciando — verifique /tmp/tunnel_crm.log${NC}"
fi

# ── Aguarda subir e verifica ──────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}⏳ Aguardando serviços subirem...${NC}"
sleep 15

echo ""
echo -e "${BOLD}📋 Status dos serviços:${NC}"

check_service() {
    local name=$1
    local url=$2
    if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ $name — online${NC}"
    else
        echo -e "   ${RED}❌ $name — não respondeu (verifique /tmp/$3.log)${NC}"
    fi
}

check_service "Scraper Backend  (8765)" "http://localhost:8765/status" "scraper"
check_service "Robô Disponibil. (8766)" "http://localhost:8766/status" "robo"
check_service "API Captador OLX (8768)" "http://localhost:8768"         "api_captador"
check_service "CRM Frontend     (5173)" "http://localhost:5173"         "crm_frontend"

# ── Abre o navegador ──────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}🌐 Abrindo o CRM no navegador...${NC}"
sleep 2
xdg-open "http://localhost:5173/kanban" 2>/dev/null || true

echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║   🚀 Sistema no ar! Ctrl+C para encerrar.   ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Mantém rodando (Ctrl+C encerra tudo via trap)
wait $ROBO_PID
