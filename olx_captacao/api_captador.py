#!/usr/bin/env python3
"""
api_captador.py
───────────────
API mínima para integrar o CRM (Frontend React) com o módulo olx_captacao.
Usa HTTP nativo (zero dependências) para receber URLs personalizadas
e disparar os scripts em background ou em tempo real.
"""
import json
import subprocess
import sys
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 8768
SCRIPT_DIR = Path(__file__).parent
VENV_PYTHON = str(SCRIPT_DIR / ".venv" / "bin" / "python3")
MAIN_SCRIPT = str(SCRIPT_DIR / "main.py")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
}

class CaptadorAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silencia logs no terminal

    def _send(self, code: int, body: dict):
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body) if body else {}
        except Exception:
            self._send(400, {"ok": False, "mensagem": "JSON inválido"})
            return

        # ROTA: /fase1 (Coleta em massa)
        if self.path == "/fase1":
            url = data.get("url")
            if not url or "olx.com.br" not in url:
                self._send(400, {"ok": False, "mensagem": "URL da OLX inválida."})
                return
            
            try:
                # Roda a fase1 em background usando Popen
                # main.py fase1 --url <URL>
                cmd = [VENV_PYTHON, MAIN_SCRIPT, "fase1", "--url", url]
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(SCRIPT_DIR)
                )
                self._send(200, {"ok": True, "mensagem": "Varredura de links (Fase 1) iniciada com sucesso em background!"})
            except Exception as e:
                self._send(500, {"ok": False, "mensagem": str(e)})

        # ROTA: /fase2-unico (Extrai 1 link específico)
        elif self.path == "/fase2-unico":
            url = data.get("url")
            if not url or "olx.com.br" not in url:
                self._send(400, {"ok": False, "mensagem": "URL do anúncio da OLX inválida."})
                return
            
            try:
                # Para uma URL única, queremos a resposta logo (síncrono)
                # main.py extrair-unico --url <URL>
                cmd = [VENV_PYTHON, MAIN_SCRIPT, "extrair-unico", "--url", url]
                
                # Executa com timeout de 90s (O scraper pode demorar até 45s)
                result = subprocess.run(cmd, cwd=str(SCRIPT_DIR), capture_output=True, text=True, timeout=90)
                
                if result.returncode == 0:
                    # Tenta parsear o resultado customizado
                    acao = "Salvo"
                    for line in result.stdout.split('\n'):
                        if line.startswith("__RESULT__="):
                            try:
                                dados = json.loads(line.replace("__RESULT__=", ""))
                                if dados.get("acao"):
                                    acao = dados["acao"]
                            except: pass
                            
                    msg = f"Imóvel {acao.lower()} com sucesso!" if acao in ["Atualizado", "Salvo"] else "Imóvel processado com sucesso!"
                    if acao == "Existente":
                        msg = "Aviso: Esse imóvel já existe no banco de dados! A extração demorada foi pulada."
                    elif acao == "Atualizado":
                        msg = "Esse imóvel já estava no banco! Os dados foram ATUALIZADOS com as informações mais recentes."
                        
                    self._send(200, {"ok": True, "mensagem": msg})
                else:
                    self._send(500, {"ok": False, "mensagem": "Erro ao extrair o anúncio.", "logs": result.stderr or result.stdout})
            except subprocess.TimeoutExpired:
                self._send(504, {"ok": False, "mensagem": "A extração demorou muito e foi interrompida."})
            except Exception as e:
                self._send(500, {"ok": False, "mensagem": str(e)})
        else:
            self._send(404, {"ok": False, "mensagem": "Rota não encontrada"})

if __name__ == "__main__":
    if not os.path.exists(VENV_PYTHON):
        print("Erro: Ambiente virtual não encontrado em", VENV_PYTHON)
        sys.exit(1)
        
    server = HTTPServer(("0.0.0.0", PORT), CaptadorAPIHandler)
    print(f"🚀 API do Captador rodando na porta {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando API...")
        sys.exit(0)
