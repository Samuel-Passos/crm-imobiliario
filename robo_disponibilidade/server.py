"""
server.py
─────────
FastAPI para gerenciar o Robô de Disponibilidade.
 - Recebe os webhooks da Evolution API
 - Permite acionar o dispatcher via HTTP

Uso:
  uvicorn server:app --host 0.0.0.0 --port 8766 --reload
"""

import os
import re
import socket
import asyncio
import logging
import threading
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, BackgroundTasks, Header, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import json

from webhook_handler import processar_evento_mensagem
from dispatcher import rodar_dispatcher
from evolution_client import EvolutionClient
from adb_client import AdbClient
from config_manager import config_manager

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Ciclo de Vida ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 1. Registrar Webhook na Evolution API ─────────────────────────────
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        try:
            evo = EvolutionClient()
            evo.configurar_webhook(webhook_url)
            log.info("Webhook registrado com sucesso na Evolution API!")
        except Exception as e:
            log.error(f"Erro ao registrar webhook na Evolution API: {e}")
    else:
        log.warning("WEBHOOK_URL não configurado no .env. Webhook NÃO registrado na Evolution API.")

    # ── 2. Auto-reconectar ADB Wi-Fi se houver host salvo ─────────────────
    cfg = config_manager.get_all()
    wifi_host = str(cfg.get("ADB_WIFI_HOST", "")).strip()
    if wifi_host and re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", wifi_host):
        try:
            res = subprocess.run(["adb", "connect", wifi_host],
                                 capture_output=True, text=True, timeout=8)
            saida = res.stdout.strip()
            if "connected" in saida.lower() or "already" in saida.lower():
                log.info(f"[ADB] Auto-conectado via Wi-Fi a {wifi_host}: {saida}")
            else:
                log.warning(f"[ADB] Auto-connect Wi-Fi falhou ({wifi_host}): {saida}")
        except Exception as e:
            log.warning(f"[ADB] Auto-connect Wi-Fi erro: {e}")
    else:
        log.info("[ADB] Nenhum host Wi-Fi salvo para auto-connect.")

    yield

app = FastAPI(title="Robô CRM SJC - Disponibilidade", lifespan=lifespan)

# Libera chamadas do CRM (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar para a URL do CRM em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir imagens geradas
STATIC_DIR = Path(__file__).parent / "generated_images"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static/generated", StaticFiles(directory=str(STATIC_DIR)), name="static_generated")


@app.get("/")
def health_check():
    return {"status": "online", "robot": "Robô de Disponibilidade SJC"}


@app.get("/status")
def get_status():
    """Retorna o estado atual do robô para o CRM, separando USB de Wi-Fi."""
    usb_device = None
    wifi_devices = []
    all_online = False

    try:
        res = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, timeout=5)
        lines = res.stdout.strip().split("\n")
        for line in lines[1:]:
            line = line.strip()
            if not line or "offline" in line:
                continue
            if "device" not in line:
                continue
            # Dispositivo USB: contém "usb:" no identificador
            if "usb:" in line:
                parts = line.split()
                serial = parts[0]
                model = next((p.replace("model:", "") for p in parts if p.startswith("model:")), serial)
                usb_device = {"serial": serial, "model": model}
                all_online = True
            # Dispositivo Wi-Fi: serial é um IP:porta (ex: 192.168.1.96:5555)
            elif re.match(r"\d+\.\d+\.\d+\.\d+:\d+", line.split()[0]):
                parts = line.split()
                ip_porta = parts[0]
                model = next((p.replace("model:", "") for p in parts if p.startswith("model:")), ip_porta)
                wifi_devices.append({"ip_porta": ip_porta, "model": model})
                all_online = True
    except Exception:
        pass

    return {
        "online":      True,
        "executando":  is_running,
        "adb_online":  all_online,
        "usb_device":  usb_device,
        "wifi_devices": wifi_devices,
    }


@app.get("/adb/diagnostico")
def adb_diagnostico():
    """
    Diagnóstico completo da conexão ADB.
    Verifica hardware USB e dispositivos Wi-Fi separadamente.
    """
    resultado = {
        "usb": {"hardware_detectado": False, "adb_autorizado": False, "dispositivo": None},
        "wifi": {"dispositivos": [], "conectado": False},
        "dica": "",
    }

    # ── 1. Verificar hardware USB via lsusb ─────────────────────────────────
    try:
        lsusb_res = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
        android_vendors = ["2717", "18d1", "04e8", "22b8", "0bb4", "12d1", "2ae5", "19d2", "05c6"]
        for line in lsusb_res.stdout.splitlines():
            if any(v in line for v in android_vendors):
                resultado["usb"]["hardware_detectado"] = True
                resultado["usb"]["hardware_info"] = line.strip()
                break
    except Exception as e:
        resultado["usb"]["erro_lsusb"] = str(e)

    # ── 2. Verificar dispositivos via adb devices -l ─────────────────────────
    try:
        adb_res = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, timeout=5)
        for line in adb_res.stdout.splitlines()[1:]:
            line = line.strip()
            if not line or "offline" in line:
                continue
            if "device" not in line:
                continue
            parts = line.split()
            serial = parts[0]
            model = next((p.replace("model:", "") for p in parts if p.startswith("model:")), serial)
            transport = next((p for p in parts if p.startswith("usb:")), "")

            if "usb:" in line:
                resultado["usb"]["adb_autorizado"] = True
                resultado["usb"]["dispositivo"] = {"serial": serial, "model": model, "transporte": transport}
            elif re.match(r"\d+\.\d+\.\d+\.\d+:\d+", serial):
                resultado["wifi"]["conectado"] = True
                resultado["wifi"]["dispositivos"].append({"ip_porta": serial, "model": model})
    except Exception as e:
        resultado["erro_adb"] = str(e)

    # ── 3. Gerar dica de diagnóstico ─────────────────────────────────────────
    usb_hw = resultado["usb"]["hardware_detectado"]
    usb_adb = resultado["usb"]["adb_autorizado"]
    wifi_ok = resultado["wifi"]["conectado"]

    if usb_hw and not usb_adb:
        resultado["dica"] = "Hardware USB detectado, mas ADB não autorizado. Verifique a tela do celular: deve aparecer um popup 'Permitir depuração USB?'. Toque em OK."
    elif not usb_hw:
        resultado["dica"] = "Nenhum hardware Android detectado via USB. Verifique o cabo e a porta USB."
    elif usb_adb and not wifi_ok:
        resultado["dica"] = "USB conectado e funcionando. Wi-Fi não conectado — use o botão Conectar Wi-Fi informando IP e porta do celular."
    elif usb_adb and wifi_ok:
        resultado["dica"] = "Tudo conectado! USB e Wi-Fi funcionando normalmente."
    else:
        resultado["dica"] = "Nenhum dispositivo conectado. Conecte o cabo USB primeiro."

    return {"ok": True, "diagnostico": resultado}


# ── Webhook da Evolution API ──────────────────────────────────────────────
@app.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Recebe eventos da Evolution API"""
    try:
        body = await request.json()
        evento = body.get("event", "")
        log.info(f"👉 [Webhook] Recebeu evento: {evento}")

        # Filtra apenas o evento de nova mensagem ignorando maiúsculas
        if evento.lower() == "messages.upsert" or evento.lower() == "messages-upsert":
            log.info("Processando evento UPSERT em background...")
            background_tasks.add_task(processar_evento_mensagem, body)
            
        return {"ok": True}
    except Exception as e:
        log.error(f"Erro no endpoint do webhook: {e}")
        return {"ok": False, "error": str(e)}


# ── Disparo (Dispatcher) ──────────────────────────────────────────────────
is_running = False

@app.post("/disparo")
async def iniciar_disparo(request: Request, background_tasks: BackgroundTasks):
    """
    Acionado manualmente (ex: botão no CRM) para iniciar a rodada de contatos.
    """
    global is_running
    if is_running:
        return {"status": "ocupado", "mensagem": "O robô já está em execução!"}
        
    try:
        body = await request.json()
        motor = body.get("motor", "EVOLUTION")
    except Exception:
        motor = "EVOLUTION"

    is_running = True
    import dispatcher
    dispatcher.PARAR_ROBO = False
    
    def run_wrapper(m: str):
        global is_running
        try:
            dispatcher.rodar_dispatcher(False, m)
        finally:
            is_running = False

    background_tasks.add_task(run_wrapper, motor)
    return {"status": "iniciado", "mensagem": f"Disparo iniciado em background (Motor: {motor}). Verifique os logs."}


@app.post("/parar")
def parar_disparo():
    """
    Sinaliza ao dispatcher que ele deve parar no próximo ciclo do loop.
    """
    import dispatcher
    dispatcher.PARAR_ROBO = True
    return {"status": "parado", "mensagem": "Sinal de parada enviado."}


# ── Gerenciador ADB (Scrcpy e Pareamento Wi-Fi) ──────────────────────────

@app.post("/adb/parear")
async def adb_parear(request: Request):
    try:
        body = await request.json()
        ip_porta = body.get("ip_porta")
        codigo = body.get("codigo")
        if not ip_porta or not codigo:
            return {"ok": False, "mensagem": "IP:Porta ou Código ausentes."}
            
        log.info(f"[ADB] Tentando parear com {ip_porta} usando código {codigo}")
        res = subprocess.run(
            ["adb", "pair", str(ip_porta), str(codigo)],
            capture_output=True, text=True, timeout=15
        )
        saida = (res.stdout + res.stderr).lower()

        # ADB às vezes retorna código 0 mas imprime erro no stdout
        erros_conhecidos = ["failed", "unable", "error", "cannot", "refused"]
        if any(e in saida for e in erros_conhecidos):
            dica = ""
            if "unable to start pairing" in saida:
                dica = " O popup no celular pode ter expirado — gere um novo código e tente novamente."
            return {"ok": False, "mensagem": f"Falha no pareamento.{dica}", "log": res.stdout.strip()}

        if res.returncode == 0:
            return {"ok": True, "mensagem": "Pareamento autorizado com sucesso! ✅", "log": res.stdout.strip()}
        else:
            return {"ok": False, "mensagem": f"Falha ao parear: {res.stderr.strip()}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "mensagem": "Tempo esgotado. O popup do celular expirou — gere um novo código."}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}


@app.get("/adb/gerar-qr")
async def adb_gerar_qr():
    """
    Gera um QR code para pareamento ADB via Wi-Fi.
    Fluxo correto:
      - COMPUTADOR gera e exibe o QR code
      - CELULAR escaneia o QR (Depuração sem fio → Emparelhar com QR Code)
      - O Android encontra o serviço via mDNS e pareia automaticamente

    O QR usa o formato padrão Android:
      WIFI:T:ADB;S:<service-name>;P:<password>;;
    """
    import secrets
    import base64
    from io import BytesIO

    try:
        import qrcode
    except ImportError:
        return {"ok": False, "mensagem": "qrcode não instalado. Rode: pip install qrcode pillow"}

    try:
        from zeroconf import Zeroconf, ServiceInfo
    except ImportError:
        return {"ok": False, "mensagem": "zeroconf não instalado. Rode: pip install zeroconf"}

    # ── 1. Gerar credenciais ──────────────────────────────────────────────────
    service_name = f"adbpair_{secrets.token_hex(4)}"
    password = secrets.token_hex(6)
    qr_content = f"WIFI:T:ADB;S:{service_name};P:{password};;"
    log.info(f"[ADB-QR] Gerando QR — Serviço: {service_name}")

    # ── 2. Registrar serviço mDNS para o Android encontrar ───────────────────
    try:
        # Tenta pegar o IP real da interface de rede (mais robusto que gethostname)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = socket.gethostbyname(socket.gethostname())
        finally:
            s.close()
            
        port = 37000 + secrets.randbelow(1000)  # Porta aleatória no range 37000-38000

        info = ServiceInfo(
            type_="_adb-tls-pairing._tcp.local.",
            name=f"{service_name}._adb-tls-pairing._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"password": password}
        )
        zc = Zeroconf()
        zc.register_service(info)
        log.info(f"[ADB-QR] Serviço mDNS registrado: {service_name} em {local_ip}:{port}")

        # Cancela o serviço mDNS após 90s (tempo limite do QR no Android)
        def cancelar_mdns():
            import time
            time.sleep(90)
            try:
                zc.unregister_service(info)
                zc.close()
                log.info("[ADB-QR] Serviço mDNS cancelado (90s expirado)")
            except Exception:
                pass

        threading.Thread(target=cancelar_mdns, daemon=True).start()

    except Exception as e:
        log.warning(f"[ADB-QR] Aviso mDNS: {e} — QR ainda será gerado")

    # ── 3. Gerar imagem QR ────────────────────────────────────────────────────
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "ok": True,
        "qr_image": f"data:image/png;base64,{img_b64}",
        "qr_content": qr_content,
        "servico": service_name,
        "mensagem": "QR gerado! Aponte o celular → Depuração sem fio → Emparelhar com QR Code"
    }



@app.post("/adb/conectar")
async def adb_conectar(request: Request):
    try:
        body = await request.json()
        ip_porta = body.get("ip_porta", "").strip()
        if not ip_porta or not re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", ip_porta):
            return {"ok": False, "mensagem": "IP:Porta inválido. Use o formato 192.168.1.x:porta"}

        log.info(f"[ADB] Tentando conectar via Wi-Fi a {ip_porta}")
        res = subprocess.run(["adb", "connect", ip_porta], capture_output=True, text=True, timeout=10)
        saida = res.stdout.lower()
        if "failed" in saida or "cannot" in saida or "unable" in saida:
            return {"ok": False, "mensagem": "Falha de conexão. Verifique se a porta mudou no celular e se a Depuração Sem Fio está ativa.", "log": res.stdout}

        # ── Salvar host para auto-connect futuro ────────────────────────────────
        config_manager.save_key("ADB_WIFI_HOST", ip_porta)
        log.info(f"[ADB] Host Wi-Fi salvo: {ip_porta}")

        return {"ok": True, "mensagem": f"Conectado via Wi-Fi a {ip_porta}!", "log": res.stdout}
    except subprocess.TimeoutExpired:
        return {"ok": False, "mensagem": "Tempo esgotado. O celular não respondeu — verifique se está na mesma rede."}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}


@app.post("/adb/desconectar")
async def adb_desconectar(request: Request):
    """Desconecta um dispositivo ADB Wi-Fi pelo IP:porta e limpa o host salvo."""
    try:
        body = await request.json()
        ip_porta = body.get("ip_porta", "").strip()
        if not ip_porta:
            res = subprocess.run(["adb", "disconnect"], capture_output=True, text=True, timeout=10)
        else:
            res = subprocess.run(["adb", "disconnect", ip_porta], capture_output=True, text=True, timeout=10)

        # Limpar host salvo
        config_manager.save_key("ADB_WIFI_HOST", "")
        log.info("[ADB] Host Wi-Fi removido do config.")

        return {"ok": True, "mensagem": f"Dispositivo desconectado.", "log": res.stdout}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}


@app.get("/adb/wifi-host")
def adb_get_wifi_host():
    """Retorna o host Wi-Fi salvo (IP:porta) para o frontend pré-preencher os campos."""
    cfg = config_manager.get_all()
    host = str(cfg.get("ADB_WIFI_HOST", "")).strip()
    if host and ":" in host:
        ip, porta = host.rsplit(":", 1)
        return {"ok": True, "host": host, "ip": ip, "porta": porta}
    return {"ok": True, "host": "", "ip": "", "porta": ""}


@app.post("/adb/descobrir-wifi")
async def adb_descobrir_wifi(request: Request):
    """
    Varre as portas do range ADB sem fio (37000-45000) em paralelo
    para encontrar automaticamente a nova porta após ela mudar.
    Retorna o primeiro host encontrado e já salva no config.
    """
    import concurrent.futures, socket as sock

    try:
        body = await request.json()
        ip = body.get("ip", "").strip()
    except Exception:
        ip = ""

    # Se não foi passado IP, tenta usar o do host salvo
    if not ip:
        cfg = config_manager.get_all()
        host_salvo = str(cfg.get("ADB_WIFI_HOST", "")).strip()
        if host_salvo and ":" in host_salvo:
            ip = host_salvo.rsplit(":", 1)[0]

    if not ip or not re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
        return {"ok": False, "mensagem": "IP inválido ou não encontrado. Informe o IP do celular."}

    log.info(f"[ADB] Varrendo portas ADB sem fio em {ip} (37000-45000)...")

    def checar_porta(porta: int) -> int | None:
        try:
            s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            s.settimeout(0.3)
            resultado = s.connect_ex((ip, porta))
            s.close()
            return porta if resultado == 0 else None
        except Exception:
            return None

    porta_encontrada = None
    # Varre em lotes paralelos para ser rápido (~3-5s total)
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futuros = {executor.submit(checar_porta, p): p for p in range(37000, 45001)}
        for futuro in concurrent.futures.as_completed(futuros):
            resultado = futuro.result()
            if resultado:
                porta_encontrada = resultado
                # Cancela o resto assim que achar a primeira
                break

    if not porta_encontrada:
        return {
            "ok": False,
            "mensagem": f"Nenhuma porta ADB encontrada em {ip}. Verifique se a Depuração Sem Fio está ativa no celular.",
            "ip": ip
        }

    novo_host = f"{ip}:{porta_encontrada}"
    log.info(f"[ADB] Porta ADB encontrada: {novo_host}. Tentando conectar...")

    # Tenta conectar automaticamente
    try:
        res = subprocess.run(["adb", "connect", novo_host], capture_output=True, text=True, timeout=10)
        saida = res.stdout.strip()
        if "failed" in saida.lower() or "cannot" in saida.lower():
            return {"ok": False, "mensagem": f"Porta {porta_encontrada} encontrada mas ADB recusou a conexão: {saida}", "ip": ip, "porta": str(porta_encontrada)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "mensagem": f"Porta {porta_encontrada} encontrada mas o ADB não respondeu no tempo limite. Tente novamente.", "ip": ip, "porta": str(porta_encontrada)}
    except Exception as e:
        return {"ok": False, "mensagem": str(e), "ip": ip, "porta": str(porta_encontrada)}

    # Salva o novo host
    config_manager.save_key("ADB_WIFI_HOST", novo_host)
    log.info(f"[ADB] Novo host Wi-Fi salvo: {novo_host}")

    return {
        "ok": True,
        "mensagem": f"✅ Conectado automaticamente a {novo_host}",
        "host": novo_host,
        "ip": ip,
        "porta": str(porta_encontrada),
        "log": saida
    }


@app.post("/adb/scrcpy")
def iniciar_scrcpy():
    try:
        log.info("[ADB] Iniciando scrcpy...")

        # Busca um dispositivo que não seja offline
        res = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        linhas = res.stdout.strip().split("\n")[1:]
        
        serial_ativo = None
        for linha in linhas:
            linha = linha.strip()
            if linha and "offline" not in linha and "device" in linha:
                serial_ativo = linha.split()[0]
                break
        
        cmd = ["scrcpy"]
        if serial_ativo:
            cmd.extend(["-s", serial_ativo])
            log.info(f"[ADB] Scrcpy direcionado para o dispositivo: {serial_ativo}")
        else:
            log.warning("[ADB] Nenhum dispositivo ativo encontrado para o Scrcpy, tentando comando genérico.")

        # Usa Popen para rodar o scrcpy desacoplado.
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "mensagem": "Espelhamento iniciado no seu monitor principal."}
    except Exception as e:
        log.error(f"Erro no Scrcpy: {e}")
        return {"ok": False, "mensagem": "Falha ao iniciar scrcpy. Verifique se o aparelho celular está conectado."}
    

@app.post("/adb/dial")
async def adb_dial(request: Request):
    try:
        body = await request.json()
        telefone = body.get("telefone")
        if not telefone:
            return {"ok": False, "mensagem": "Telefone ausente."}
            
        adb = AdbClient()
        adb.abrir_discador(telefone)
        return {"ok": True, "mensagem": f"Chamada iniciada para {telefone}"}
    except Exception as e:
        log.error(f"Erro no discador: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/adb/whatsapp-call")
async def adb_whatsapp_call(request: Request):
    try:
        body = await request.json()
        telefone = body.get("telefone")
        if not telefone:
            return {"ok": False, "mensagem": "Telefone ausente."}
            
        adb = AdbClient()
        adb.whatsapp_call(telefone)
        return {"ok": True, "mensagem": f"Iniciando chamada WhatsApp para {telefone}"}
    except Exception as e:
        log.error(f"Erro na ligação Whats: {e}")
        return {"ok": False, "mensagem": str(e)}


@app.post("/adb/whatsapp-msg")
async def adb_whatsapp_msg(request: Request):
    """Abre o WhatsApp no celular com mensagem pré-preenchida via ADB."""
    try:
        body = await request.json()
        telefone = body.get("telefone")
        mensagem = body.get("mensagem", "")
        
        # Se a mensagem não vier pronta, o backend formata de acordo com o tipo
        if not mensagem:
            nome = body.get("nome", "")
            tipo = body.get("tipo_campanha", "").upper()
            metadata = body.get("metadata", {})
            
            from config_manager import config_manager
            cfg = config_manager.get_all()
            remetente = cfg.get("REMETENTE_NOME", "Samuel")
            
            if "ATUALIZA" in tipo:
                from templates import mensagem_inicial
                from buscar_link_imovel import buscar_link_imovel
                import asyncio
                
                # Busca a referência de forma case-insensitive e ignorando acentos comuns
                ref = ""
                for k, v in metadata.items():
                    k_lower = k.lower().replace("ê", "e")
                    if "referencia" in k_lower or k_lower == "ref":
                        ref = str(v).strip()
                        break

                proprietario = metadata.get("proprietario_mapeado", nome)
                link = ""
                if ref:
                    link = await asyncio.to_thread(buscar_link_imovel, ref)
                    link = link or ""
                
                mensagem = mensagem_inicial(proprietario, ref, link)
            else:
                tpl = cfg.get("TEMPLATE_WHATSAPP_CAMPANHA", "Olá {nome}, tudo bem? Sou o {remetente}, vi seu interesse...")
                mensagem = tpl.replace("{nome}", nome).replace("{remetente}", remetente)

        if not telefone:
            return {"ok": False, "mensagem": "Telefone ausente."}

        adb = AdbClient()
        adb.send_text(telefone, mensagem)
        return {"ok": True, "mensagem": f"WhatsApp aberto para {telefone}"}
    except Exception as e:
        log.error(f"Erro ao abrir WhatsApp msg: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/adb/sms/send")
async def adb_sms_send(request: Request):
    try:
        body = await request.json()
        telefone = body.get("telefone")
        mensagem = body.get("mensagem")
        if not telefone or not mensagem:
            return {"ok": False, "mensagem": "Telefone ou Mensagem ausentes."}
            
        adb = AdbClient()
        adb.send_sms(telefone, mensagem)
        return {"ok": True, "mensagem": f"SMS disparado para {telefone}"}
    except Exception as e:
        log.error(f"Erro no envio de SMS: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.get("/adb/settings")
async def adb_get_settings():
    try:
        settings = config_manager.get_all()
        return {"ok": True, "settings": settings}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}

@app.get("/scraper/config")
async def get_scraper_config():
    try:
        import sys, os
        scraper_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scraper"))
        if scraper_dir not in sys.path:
            sys.path.append(scraper_dir)
        from config_db import get_config
        _cfg = get_config()
        return {"ok": True, "config": _cfg}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}

@app.post("/scraper/config")
async def update_scraper_config(request: Request):
    try:
        config = await request.json()
        import sys, os
        scraper_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scraper"))
        if scraper_dir not in sys.path:
            sys.path.append(scraper_dir)
        from config_db import supabase
        if not supabase:
            return {"ok": False, "mensagem": "Supabase not configured in backend"}
        supabase.table("configuracoes_scraper").update(config).eq("id", 1).execute()
        return {"ok": True, "message": "Updated successfully"}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}

@app.post("/adb/settings")
async def adb_save_settings(request: Request):
    try:
        body = await request.json()
        new_settings = body.get("settings")
        if not new_settings:
            return {"ok": False, "mensagem": "Configurações ausentes."}
            
        success = config_manager.save(new_settings)
        if success:
            return {"ok": True, "mensagem": "Configurações salvas com sucesso!"}
        else:
            return {"ok": False, "mensagem": "Erro ao salvar no servidor."}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}


# ── Gerenciador do Sistema ────────────────────────────────────────────────────

@app.post("/system/start")
def system_start():
    """
    Inicia todos os serviços do sistema (start_all.sh) a partir do botão do CRM.
    Roda em background para não bloquear a resposta.
    """
    script = Path(__file__).parent.parent / "start_all.sh"
    if not script.exists():
        return {"ok": False, "mensagem": "Script start_all.sh não encontrado."}
    try:
        log.info("[Sistema] Iniciando todos os serviços via start_all.sh...")
        subprocess.Popen(
            ["bash", str(script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True   # desacopla do processo do servidor
        )
        return {"ok": True, "mensagem": "Serviços sendo iniciados em background!"}
    except Exception as e:
        log.error(f"Erro ao iniciar serviços: {e}")
        return {"ok": False, "mensagem": str(e)}


@app.post("/webhook/registrar")
async def registrar_webhook(request: Request):
    """
    Chamado pelo start_all.sh quando o tunnel Cloudflare obtém sua URL pública.
    Registra a URL na Evolution API.
    """
    try:
        body = await request.json()
        webhook_url = body.get("url")
        if not webhook_url:
            return {"ok": False}
        evo = EvolutionClient()
        evo.configurar_webhook(webhook_url)
        log.info(f"Webhook registrado dinamicamente: {webhook_url}")
        return {"ok": True}
    except Exception as e:
        log.error(f"Erro ao registrar webhook: {e}")
        return {"ok": False}


# ── Extrator de CNPJ ─────────────────────────────────────────────────────────

@app.post("/extrator/iniciar")
async def extrator_iniciar(request: Request, background_tasks: BackgroundTasks):
    """
    Inicia o pipeline do extrator de CNPJ em background.
    """
    try:
        body = await request.json()
        municipio = body.get("municipio", "SAO JOSE DOS CAMPOS")
        passo = body.get("step", "all")
        limit = body.get("limit", 0)
        all_cnaes = body.get("all_cnaes", False)
        test_condo = body.get("test_condo", False)
    except Exception:
        municipio = "SAO JOSE DOS CAMPOS"
        passo = "all"
        limit = 0
        all_cnaes = False
        test_condo = False

    script_path = Path(__file__).parent.parent / "extrator_cnpj" / "pipeline.py"
    if not script_path.exists():
        return {"ok": False, "mensagem": "Script do extrator não encontrado."}

    def run_pipeline():
        cmd = [
            "python3", str(script_path),
            "--municipio", municipio,
            "--step", passo,
            "--limit", str(limit)
        ]
        if all_cnaes:
            cmd.append("--all_cnaes")
        if test_condo:
            cmd.append("--test_condo")
            
        log.info(f"[Extrator] Iniciando: {' '.join(cmd)}")
        try:
            # Roda o processo e deixa no background
            subprocess.run(cmd, check=True)
        except Exception as e:
            log.error(f"[Extrator] Erro na execução: {e}")

    background_tasks.add_task(run_pipeline)
    return {"ok": True, "mensagem": f"Pipeline iniciado para {municipio} (Teste Condomínio: {test_condo})."}


@app.get("/extrator/status")
async def extrator_status():
    """Retorna o progresso atual do extrator lido do arquivo de status."""
    status_file = Path(__file__).parent.parent / "extrator_cnpj" / "output" / "current_status.json"
    if not status_file.exists():
        return {"ok": False, "mensagem": "Nenhum processo em execução ou finalizado recentemente."}
    
    try:
        import json
        return {"ok": True, "status": json.loads(status_file.read_text())}
    except Exception as e:
        return {"ok": False, "mensagem": f"Erro ao ler status: {e}"}


@app.get("/extrator/logs")
async def extrator_logs():
    """Retorna as últimas 50 linhas do log do extrator."""
    log_file = Path(__file__).parent.parent / "extrator_cnpj" / "output" / "pipeline.log"
    if not log_file.exists():
        return {"ok": False, "mensagem": "Arquivo de log não encontrado."}
    
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
            return {"ok": True, "logs": lines[-50:]}
    except Exception as e:
        log.error(f"Erro ao ler logs: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/extrator/enriquecer-individual")
async def extrator_enriquecer_individual(request: Request):
    """
    Enriquece um único CNPJ via OpenCNPJ.
    """
    try:
        body = await request.json()
        cnpj = body.get("cnpj")
        if not cnpj:
            return {"ok": False, "mensagem": "CNPJ ausente."}

        import sys
        sys.path.append(str(Path(__file__).parent.parent / "extrator_cnpj"))
        from pipeline import enriquecer_cnpj_individual
        
        resultado = enriquecer_cnpj_individual(str(cnpj).replace(".", "").replace("-", "").replace("/", ""))
        if resultado:
            return {"ok": True, "dados": resultado}
        else:
            return {"ok": False, "mensagem": "Falha no enriquecimento básico."}
    except Exception as e:
        log.error(f"Erro no enriquecimento individual: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/extrator/enriquecer-receitaws")
async def extrator_enriquecer_receitaws(request: Request):
    """
    Enriquece via ReceitaWS (Premium ou Free).
    """
    try:
        body = await request.json()
        cnpj = body.get("cnpj")
        if not cnpj:
            return {"ok": False, "mensagem": "CNPJ ausente."}

        import sys
        sys.path.append(str(Path(__file__).parent.parent / "extrator_cnpj"))
        from pipeline import enriquecer_receitaws_individual
        
        resultado = enriquecer_receitaws_individual(str(cnpj))
        if resultado:
            return {"ok": True, "dados": resultado}
        else:
            return {"ok": False, "mensagem": "Falha no enriquecimento via ReceitaWS."}
    except Exception as e:
        log.error(f"Erro no enriquecimento ReceitaWS: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/extrator/jucesp-auto")
async def extrator_jucesp_auto(request: Request, background_tasks: BackgroundTasks):
    """
    Aciona o robô automático da JUCESP para o CNPJ selecionado.
    """
    try:
        body = await request.json()
        cnpj = body.get("cnpj")
        if not cnpj:
            return {"ok": False, "mensagem": "CNPJ ausente."}

        def run_robot(target_cnpj):
            import sys
            p = str(Path(__file__).parent.parent / "extrator_cnpj")
            if p not in sys.path: sys.path.append(p)
            try:
                from jucesp_robot import rodar_automacao_jucesp
                rodar_automacao_jucesp(target_cnpj)
            except Exception as e:
                log.error(f"Erro fatal no processo do Robô JUCESP: {e}")

        # Roda em background para não travar o CRM enquanto o navegador está aberto
        background_tasks.add_task(run_robot, str(cnpj))
        
        return {
            "ok": True, 
            "mensagem": "Robô JUCESP iniciado! Procure a janela do navegador que abriu e faça o Login Gov.br para continuar."
        }
    except Exception as e:
        log.error(f"Erro ao disparar robô JUCESP: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/extrator/lote-direto")
async def extrator_lote_direto(request: Request, background_tasks: BackgroundTasks):
    """
    Aciona o enriquecimento em lote (Motor Direto) via ReceitaWS.
    """
    try:
        body = await request.json()
        limit = body.get("limit", 1000)
        
        def run_lote(l_limit):
            proj_root = Path(__file__).parent.parent
            script = proj_root / "extrator_cnpj" / "motor_direto.py"
            python_bin = proj_root / "extrator_cnpj" / ".venv" / "bin" / "python3"
            log_stdout = proj_root / "extrator_cnpj" / "output" / "motor_direto_stdout.log"
            
            # Garante que o diretório de output existe
            log_stdout.parent.mkdir(parents=True, exist_ok=True)
            
            log.info(f"[Extrator] Iniciando lote de {l_limit} empresas via Motor Direto...")
            
            # Comando nohup-style via Popen para garantir independência
            with open(log_stdout, "w") as f:
                subprocess.Popen(
                    [str(python_bin), str(script), "--limit", str(l_limit), "--delay", "21"],
                    stdout=f, stderr=subprocess.STDOUT,
                    cwd=str(proj_root)
                )

        background_tasks.add_task(run_lote, limit)
        
        return {
            "ok": True,
            "mensagem": f"Lote de {limit} empresas iniciado em segundo plano!"
        }
    except Exception as e:
        log.error(f"Erro ao disparar lote: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/extrator/test-gemini")
async def extrator_test_gemini(request: Request):
    """
    Testa a conexão com a API do Gemini usando a chave salva.
    """
    try:
        from config_manager import config_manager
        cfg = config_manager.get_all()
        api_key = cfg.get("GEMINI_API_KEY")
        model = cfg.get("GEMINI_MODEL", "gemini-1.5-flash")
        
        if not api_key:
            return {"ok": False, "mensagem": "API Key do Gemini não configurada."}

        # Teste simples via requests para evitar dependência de biblioteca pesada no server principal por enquanto
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": "Olá, responda apenas 'CONECTADO'"}]}]
        }
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()

        if resp.status_code == 200:
            text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            return {"ok": True, "mensagem": f"Conexão com Gemini sussedida! Resposta: {text.strip()}"}
        else:
            msg = data.get("error", {}).get("message", "Erro desconhecido")
            return {"ok": False, "mensagem": f"Falha na API: {msg}"}
            
    except Exception as e:
        log.error(f"Erro ao testar Gemini: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.post("/api/designer/agents/{agente_id}/upload")
async def api_designer_agent_upload(agente_id: str, file: UploadFile = File(...)):
    """Upload de arquivos de referência para a base de conhecimento do agente."""
    try:
        from config_manager import config_manager
        from supabase import create_client, Client
        import shutil
        import os

        # 1. Configurar caminhos
        KNOWLEDGE_DIR = Path("knowledge_base") / agente_id
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        
        file_path = KNOWLEDGE_DIR / file.filename
        
        # 2. Salvar arquivo localmente
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. Registrar no Supabase para rastreamento
        cfg = config_manager.get_all()
        supabase: Client = create_client(cfg["SUPABASE_URL"], cfg["SUPABASE_KEY"])
        
        file_info = {
            "agente_id": agente_id,
            "nome_arquivo": file.filename,
            "caminho_local": str(file_path),
            "tamanho_bytes": os.path.getsize(file_path),
            "tipo_mime": file.content_type
        }
        
        supabase.table("agente_arquivos").insert(file_info).execute()
        
        return {"ok": True, "mensagem": f"Arquivo {file.filename} salvo com sucesso."}
    except Exception as e:
        log.error(f"Erro no upload de arquivo: {e}")
        return {"ok": False, "mensagem": str(e)}

@app.get("/api/designer/agents/{agente_id}/files")
async def api_designer_agent_files(agente_id: str):
    """Lista os arquivos de referência de um agente."""
    try:
        from config_manager import config_manager
        from supabase import create_client, Client
        
        cfg = config_manager.get_all()
        supabase: Client = create_client(cfg["SUPABASE_URL"], cfg["SUPABASE_KEY"])
        
        res = supabase.table("agente_arquivos").select("*").eq("agente_id", agente_id).execute()
        return {"ok": True, "arquivos": res.data}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}

@app.delete("/api/designer/agents/files/{file_id}")
async def api_designer_file_delete(file_id: str):
    """Exclui um arquivo de referência."""
    try:
        from config_manager import config_manager
        from supabase import create_client, Client
        import os
        
        cfg = config_manager.get_all()
        supabase: Client = create_client(cfg["SUPABASE_URL"], cfg["SUPABASE_KEY"])
        
        # 1. Busca info do arquivo
        res = supabase.table("agente_arquivos").select("*").eq("id", file_id).execute()
        if not res.data:
            return {"ok": False, "mensagem": "Arquivo não encontrado."}
            
        file_path = res.data[0]["caminho_local"]
        
        # 2. Remove do disco
        if os.path.exists(file_path):
            os.remove(file_path)
            
        # 3. Remove do banco
        supabase.table("agente_arquivos").delete().eq("id", file_id).execute()
        
        return {"ok": True, "mensagem": "Arquivo removido."}
    except Exception as e:
        return {"ok": False, "mensagem": str(e)}

@app.post("/api/designer/chat")
async def api_designer_chat(request: Request):
    """
    Interface unificada para o Designer IA (Gemini 1.5 Pro + Nano Banana).
    Suporta agentes customizados, base de conhecimento, texto e análise de imagem.
    """
    try:
        from creative_engine import CreativeEngine, base64_to_bytes
        from config_manager import config_manager
        from supabase import create_client, Client
        
        cfg = config_manager.get_all()
        body = await request.json()
        
        prompt = body.get("prompt")
        history = body.get("history", [])
        image_b64 = body.get("image")
        agente_id = body.get("agente_id")
        model_name = body.get("model") # Novo parâmetro do modelo
        
        if not prompt:
            return {"ok": False, "mensagem": "Prompt ausente."}

        # 0. Busca instrução de sistema e ARQUIVOS DE REFERÊNCIA
        system_instruction = None
        reference_files = []
        if agente_id:
            try:
                supabase: Client = create_client(cfg["SUPABASE_URL"], cfg["SUPABASE_KEY"])
                
                # Instrução
                res_ag = supabase.table("agentes_ia").select("instrucao_sistema").eq("id", agente_id).execute()
                if res_ag.data:
                    system_instruction = res_ag.data[0]["instrucao_sistema"]
                
                # Arquivos (Normalizar para caminhos absolutos)
                res_files = supabase.table("agente_arquivos").select("caminho_local").eq("agente_id", agente_id).execute()
                base_path = Path(__file__).parent
                reference_files = [str(base_path / f["caminho_local"]) for f in res_files.data]
            except Exception as e:
                log.error(f"Erro ao buscar contexto do agente: {e}")

        # 1. Configura engine com instrução e arquivos (Grounding)
        engine = CreativeEngine(cfg.get("GEMINI_API_KEY"), system_instruction=system_instruction)
        
        # 2. Se tem imagem, é análise multimodal
        if image_b64:
            log.info(f"[Designer] Analisando imagem multimodal (Agente: {agente_id}, Modelo: {model_name})...")
            image_bytes = base64_to_bytes(image_b64)
            res_dict = engine.analyze_image(prompt, image_bytes, reference_files=reference_files, model_name=model_name)
            return {
                "ok": True, 
                "resposta": res_dict.get("text"), 
                "image_url": res_dict.get("image_url")
            }
            
        # 3. Chat normal de texto + Tools Nativas
        # Agora o generate_copy gerencia internamente as chamadas de função (ex: generate_image)
        res_dict = engine.generate_copy(
            prompt, 
            history, 
            reference_files=reference_files, 
            model_name=model_name,
            output_dir=str(STATIC_DIR)
        )
        
        return {
            "ok": True, 
            "resposta": res_dict.get("text"),
            "image_url": res_dict.get("image_url")
        }


    except Exception as e:
        log.error(f"Erro no Designer Chat: {e}")
        return {"ok": False, "mensagem": str(e)}



