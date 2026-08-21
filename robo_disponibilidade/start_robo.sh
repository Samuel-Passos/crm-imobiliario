#!/bin/bash
# =============================================================================
# Inicia o Robô de Disponibilidade com auto-restart
# Cloudflare Quick Tunnel + FastAPI com reinício automático em caso de falha
# =============================================================================

cd /home/samuel/Desktop/Scraper_antigravity/robo_disponibilidade || exit 1

# ── Limpa processos anteriores ────────────────────────────────────────────────
pkill -f "cloudflared tunnel --url" 2>/dev/null
pkill -f "uvicorn server:app" 2>/dev/null
sleep 1

# ── Ativa o ambiente virtual ──────────────────────────────────────────────────
source .venv/bin/activate
export PYTHONPATH=.

# ── Trap: limpa ao pressionar Ctrl+C ─────────────────────────────────────────
cleanup() {
    echo ""
    echo "🛑 Encerrando robô e tunnel..."
    pkill -f "cloudflared tunnel --url" 2>/dev/null
    pkill -f "uvicorn server:app" 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── Inicia Cloudflare Tunnel em background (não bloqueia o servidor) ──────────
iniciar_tunnel() {
    while true; do
        > cloudflared.log  # Limpa o log a cada restart

        echo "⏳ Iniciando Cloudflare Tunnel..."
        cloudflared tunnel --url http://127.0.0.1:8766 >> cloudflared.log 2>&1 &
        CLOUDFLARED_PID=$!

        # Aguarda a URL aparecer no log (até 30s)
        count=0
        EXT_URL=""
        while [ $count -lt 30 ]; do
            EXT_URL=$(grep -o "https://[a-zA-Z0-9-]*\.trycloudflare\.com" cloudflared.log | head -n 1)
            [ -n "$EXT_URL" ] && break
            sleep 1
            count=$((count+1))
        done

        if [ -n "$EXT_URL" ]; then
            echo "✅ Tunnel ativo: $EXT_URL"
            export WEBHOOK_URL="${EXT_URL}/webhook"
            echo "📡 Webhook URL: $WEBHOOK_URL"
            # Registra o webhook via curl (servidor já está no ar)
            curl -s -X POST http://127.0.0.1:8766/webhook/registrar \
                -H "Content-Type: application/json" \
                -d "{\"url\": \"$WEBHOOK_URL\"}" > /dev/null 2>&1 || true
            wait $CLOUDFLARED_PID
            echo "⚠️  Tunnel caiu! Reiniciando em 5s..."
        else
            echo "❌ Não conseguiu URL do Cloudflare. Tentando novamente em 10s..."
            kill $CLOUDFLARED_PID 2>/dev/null
        fi
        sleep 10
    done
}

# ── Inicia o Servidor FastAPI com auto-restart (imediato, sem esperar tunnel) ─
iniciar_servidor() {
    while true; do
        echo ""
        echo "🚀 Iniciando servidor FastAPI na porta 8766..."
        uvicorn server:app --host 0.0.0.0 --port 8766 --log-level info
        echo "⚠️  Servidor caiu! Reiniciando em 5s..."
        sleep 5
    done
}

# Limpa arquivo temporário se existir
rm -f .webhook_temp.env

# ── Inicia tunnel em segundo plano, servidor em primeiro plano ────────────────
iniciar_tunnel &
TUNNEL_LOOP_PID=$!

iniciar_servidor
