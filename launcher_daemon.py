#!/usr/bin/env python3
"""
launcher_daemon.py
──────────────────
Servidor HTTP mínimo (ZERO dependências externas — só stdlib do Python).
Fica sempre rodando em segundo plano na porta 8767.
Único trabalho: receber um POST /start e disparar o start_all.sh.

Iniciar manualmente:
    python3 launcher_daemon.py

Parar:
    pkill -f launcher_daemon.py
"""

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 8767
SCRIPT = Path(__file__).parent / "start_all.sh"

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
}


class LauncherHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Silencia o log de acesso padrão (muito verboso)
        pass

    def _send(self, code: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        # Responde ao preflight CORS do browser
        self._send(204, {})

    def do_GET(self):
        if self.path == "/ping":
            self._send(200, {"ok": True, "daemon": "launcher", "port": PORT})
        else:
            self._send(404, {"ok": False})

    def do_POST(self):
        if self.path == "/start":
            if not SCRIPT.exists():
                self._send(500, {"ok": False, "mensagem": f"start_all.sh não encontrado em {SCRIPT}"})
                return
            try:
                subprocess.Popen(
                    ["bash", str(SCRIPT)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                print(f"[Launcher] ✅ start_all.sh disparado!")
                self._send(200, {"ok": True, "mensagem": "Serviços sendo iniciados! Aguarde ~10 segundos."})
            except Exception as e:
                self._send(500, {"ok": False, "mensagem": str(e)})
        else:
            self._send(404, {"ok": False})


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), LauncherHandler)
    print(f"[Launcher] 🚀 Daemon iniciado na porta {PORT} — aguardando comandos...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Launcher] Encerrado.")
        sys.exit(0)
