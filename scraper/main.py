from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Aqui vamos importar o orquestrador que roda os ciclos de IA
import orchestrator
from orchestrator import (
    run_daily_scraper_cycle, 
    extract_phone_single_lead,
    STOP_SIGNAL, PAUSE_SIGNAL, 
    process_batch_phone_extraction,
    geocode_single_google,
    geocode_full_google,
    send_chat_single_lead,
    process_batch_chat_sending,
)
from tools.phone_extractor import extract_phones_from_olx
from pegar_cookies_nativos import extrair_cookies_do_chrome_ubuntu
import tools.geocoder
import tools.geocoder_reprocess
import tools.geocoder_maps_scraper
import tools.geocoder_google_reprocess
import tools.geocode_signals as geocode_signals
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("scraper")

from contextlib import asynccontextmanager
import tools.browser_manager as browser_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        print("🍪 [STARTUP] Atualizando cookies da OLX do Chrome...")
        extrair_cookies_do_chrome_ubuntu()
        print("🍪 [STARTUP] Cookies atualizados com sucesso!")
    except Exception as e:
        print(f"⚠️ [STARTUP] Falha ao atualizar cookies (não-fatal): {e}")
        
    # Inicializa o browser global persistente
    try:
        await browser_manager.start_browser()
    except Exception as e:
        print(f"⚠️ [STARTUP] Erro ao iniciar browser persistente: {e}")
        
    yield
    
    # Shutdown
    await browser_manager.close_browser()

app = FastAPI(title="OLX Scraper Pro", description="Orquestrador Python com Browser Persistente", lifespan=lifespan)

# Libera CORS para o CRM React no localhost:5173 e 127.0.0.1
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class ImovelRequest(BaseModel):
    imovel_id: int

class UrlRequest(BaseModel):
    url: str

@app.get("/status")
def health_check():
    return {"status": "online", "message": "Scraper FastAPI is running smoothly."}
@app.post("/run")
async def run_full_cycle(background_tasks: BackgroundTasks):
    """
    Acorda o orquestrador e roda o fluxo completo diário.
    """
    # Reseta sinais antes de iniciar
    orchestrator.STOP_SIGNAL = False
    orchestrator.PAUSE_SIGNAL = False
    
    # Jogamos para background task para não travar a UI (pode levar 30+ minutos no browser)
    background_tasks.add_task(run_daily_scraper_cycle)
    return {"status": "started", "message": "Ciclo completo de extração e prospecção iniciado em background."}

@app.post("/stop")
async def stop_cycle():
    """Sinaliza para o orquestrador parar o loop atual."""
    orchestrator.STOP_SIGNAL = True
    orchestrator.PAUSE_SIGNAL = False # Garante que sai da pausa se estiver nela
    return {"status": "stopping", "message": "Sinal de parada enviado. O scraper terminará o item atual e parará."}

@app.post("/pause")
async def pause_cycle():
    """Sinaliza para o orquestrador pausar o loop."""
    orchestrator.PAUSE_SIGNAL = True
    return {"status": "paused", "message": "Sinal de pausa enviado."}

@app.post("/resume")
async def resume_cycle():
    """Sinaliza para o orquestrador retomar o loop."""
    orchestrator.PAUSE_SIGNAL = False
    return {"status": "resumed", "message": "Sinal de retomada enviado."}

@app.get("/status-execution")
async def get_execution_status():
    """Retorna se o robô está executando e se está pausado."""
    return {
        "executing": orchestrator.IS_RUNNING,
        "isPaused": orchestrator.PAUSE_SIGNAL
    }

@app.post("/extract-phone")
async def extract_one_phone(payload: ImovelRequest, background_tasks: BackgroundTasks):
    """
    O usuário abriu o Imóvel no CRM e clicou em "Extrair Telefones Agora".
    """
    background_tasks.add_task(extract_phone_single_lead, payload.imovel_id)
    return {"status": "started", "message": f"Extração de telefones do imóvel {payload.imovel_id} iniciada!"}

@app.post("/extract-phone/batch")
async def extract_phone_batch(background_tasks: BackgroundTasks, lote: int = 10):
    """
    Processa um lote de imóveis pendentes, usando a página persistente do Workspace 2.
    """
    background_tasks.add_task(process_batch_phone_extraction, lote)
    return {"status": "started", "message": f"Extração de telefones em lote ({lote} imóveis) iniciada!"}

@app.post("/test-url")
async def test_url(payload: UrlRequest):
    """
    [TESTE] Roda a extração de telefones diretamente em uma URL OLX,
    sem passar pelo banco. Retorna o resultado completo imediatamente.
    """
    page = browser_manager.get_page()
    lock = browser_manager.get_lock()
    if not page:
        raise HTTPException(status_code=503, detail="Browser não está inicializado!")
    async with lock:
        resultado = await extract_phones_from_olx(payload.url, page)
    return resultado

@app.post("/geocode")
async def run_geocoder(background_tasks: BackgroundTasks):
    """
    Dispara o script de geocodificação para preencher coordenadas faltantes.
    """
    background_tasks.add_task(tools.geocoder.main)
    return {"status": "started", "message": "Geocodificador iniciado em background! O mapa será atualizado assim que os pontos forem encontrados."}

@app.post("/geocode/reprocess")
async def run_geocoder_reprocess(background_tasks: BackgroundTasks):
    """
    Reprocessa imóveis já geocodificados com estratégia imprecisa (Centro do Bairro/Cidade)
    usando o algoritmo v2 para tentar melhorar a precisão para nível de rua.
    """
    background_tasks.add_task(tools.geocoder_reprocess.main)
    return {"status": "started", "message": "Reprocessamento iniciado! Imóveis imprecisos serão corrigidos em background."}

@app.post("/geocode/google")
async def run_geocoder_google(background_tasks: BackgroundTasks):
    """
    Segundo motor: usa a Google Maps Geocoding API para geocodificar
    imóveis que ainda não têm coordenadas (latitude IS NULL).
    """
    background_tasks.add_task(tools.geocoder_maps_scraper.main)
    return {"status": "started", "message": "Geocodificador Google Maps iniciado em background!"}

@app.post("/geocode/google/reprocess")
async def run_geocoder_google_reprocess(background_tasks: BackgroundTasks):
    """
    Reprocessa imóveis com geocode_needs_review=True usando a Google Maps API.
    Esses imóveis foram marcados pelo Nominatim como imprecisos (bairro/cidade).
    """
    background_tasks.add_task(tools.geocoder_google_reprocess.main)
    return {"status": "started", "message": "Reprocessamento Google Maps iniciado! Imóveis com needs_review serão corrigidos."}

@app.post("/geocode/google/single")
async def geocode_one_google(payload: ImovelRequest):
    """
    Geocodifica via Google Maps um único imóvel (revisão pontual).
    """
    logger.info(f"📍 Recebido pedido de geocodificação para ID {payload.imovel_id}")
    return await geocode_single_google(payload.imovel_id)

@app.post("/geocode/google/full")
async def run_geocoder_google_full(background_tasks: BackgroundTasks):
    """
    Novo motor: Reprocessa TODOS os anúncios ativos e não-expirados via Google Maps.
    """
    background_tasks.add_task(geocode_full_google)
    return {"status": "started", "message": "Revisão geral do banco de dados (Google Maps) iniciada em background!"}

@app.post("/geocode/stop")
async def stop_geocoder():
    """Sinaliza para parar qualquer processo de geocodificação."""
    geocode_signals.STOP_SIGNAL = True
    return {"status": "stopping", "message": "Sinal de parada enviado para o geocodificador."}

@app.get("/geocode/status")
async def get_geocode_status():
    """Retorna se o geocodificador está rodando."""
    return {
        "running": geocode_signals.IS_RUNNING
    }

@app.post("/send-chat")
async def send_one_chat(payload: ImovelRequest, background_tasks: BackgroundTasks):
    """
    Envia mensagem de chat OLX para um imóvel específico.
    Dispara em background para não bloquear a interface.
    """
    background_tasks.add_task(send_chat_single_lead, payload.imovel_id)
    return {"status": "started", "message": f"Envio de chat para imóvel {payload.imovel_id} iniciado em background."}

@app.post("/send-chat/batch")
async def send_chat_batch(background_tasks: BackgroundTasks):
    """
    Aciona o disparador (sender.py) dentro do robo_chat_prospeccao isolado.
    """
    def run_sender():
        import subprocess
        import sys
        import os
        # O orquestrador fica na pasta ../robo_chat_prospeccao
        sender_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "robo_chat_prospeccao", "orquestrador_reverso.py"))
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        log_file_path = "/tmp/robo_chat_batch.log"
        try:
            with open(log_file_path, "a") as f:
                subprocess.Popen([python_exec, sender_path], stdout=f, stderr=f)
        except Exception as e:
            print(f"Erro ao disparar sender: {e}")
            
    background_tasks.add_task(run_sender)
    return {"status": "started", "message": "Lote de envio de chat OLX iniciado no Workspace 3."}

scanner_is_running = False

@app.post("/run-scanner")
async def run_scanner_endpoint(background_tasks: BackgroundTasks):
    global scanner_is_running
    if scanner_is_running:
        return {"status": "already_running", "message": "O Scanner já está rodando!"}
        
    scanner_is_running = True
    def run_scanner():
        global scanner_is_running
        import subprocess, os
        scanner_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "robo_chat_prospeccao", "scanner_inbox.py"))
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        log_file_path = "/tmp/scanner_isolado.log"
        try:
            with open(log_file_path, "w") as f:
                subprocess.run([python_exec, "-u", scanner_path], stdout=f, stderr=f)
        except Exception as e:
            print(f"Erro ao disparar scanner isolado: {e}")
        finally:
            scanner_is_running = False
            
    background_tasks.add_task(run_scanner)
    return {"status": "started", "message": "Scanner de Inbox iniciado!"}

@app.get("/status-scanner")
async def get_scanner_status():
    return {"running": scanner_is_running}

@app.post("/run-script3")
async def run_script3_endpoint(background_tasks: BackgroundTasks):
    def run_s3():
        import subprocess, os
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "robo_chat_prospeccao", "orquestrador_reverso.py"))
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        try:
            with open("/tmp/script3_isolado.log", "w") as f:
                subprocess.Popen([python_exec, "-u", script_path, "--coluna", "script3", "--lote", "50"], stdout=f, stderr=f)
        except Exception as e:
            print(f"Erro no script3: {e}")
    background_tasks.add_task(run_s3)
    return {"status": "started", "message": "Execução isolada do Script 3 iniciada!"}

@app.post("/run-script2")
async def run_script2_endpoint(background_tasks: BackgroundTasks):
    def run_s2():
        import subprocess, os
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "robo_chat_prospeccao", "orquestrador_reverso.py"))
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        try:
            with open("/tmp/script2_isolado.log", "w") as f:
                subprocess.Popen([python_exec, "-u", script_path, "--coluna", "script2", "--lote", "50"], stdout=f, stderr=f)
        except Exception as e:
            print(f"Erro no script2: {e}")
    background_tasks.add_task(run_s2)
    return {"status": "started", "message": "Execução isolada do Script 2 iniciada!"}

@app.post("/run-script1")
async def run_script1_endpoint(background_tasks: BackgroundTasks):
    def run_s1():
        import subprocess, os
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "robo_chat_prospeccao", "orquestrador_reverso.py"))
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        try:
            with open("/tmp/script1_isolado.log", "w") as f:
                subprocess.Popen([python_exec, "-u", script_path, "--coluna", "script1", "--lote", "50"], stdout=f, stderr=f)
        except Exception as e:
            print(f"Erro no script1: {e}")
    background_tasks.add_task(run_s1)
    return {"status": "started", "message": "Execução isolada do Script 1 iniciada!"}

@app.post("/run-extracao")
async def run_extracao_endpoint(background_tasks: BackgroundTasks):
    def run_ext():
        import subprocess, os
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "robo_chat_prospeccao", "orquestrador_reverso.py"))
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        try:
            with open("/tmp/extracao_isolada.log", "w") as f:
                subprocess.Popen([python_exec, "-u", script_path, "--coluna", "extracao", "--lote", "50"], stdout=f, stderr=f)
        except Exception as e:
            print(f"Erro na extracao: {e}")
    background_tasks.add_task(run_ext)
    return {"status": "started", "message": "Execução isolada da Extração iniciada!"}

@app.post("/send-chat/stop")
async def stop_chat_batch():
    """Sinaliza para o lote de chat parar após o envio atual."""
    orchestrator.CHAT_STOP_SIGNAL = True
    return {"status": "stopping", "message": "Sinal de parada enviado. O chat terminará o item atual e parará."}

@app.get("/send-chat/status")
async def get_chat_status():
    """Retorna se o bot de chat está rodando."""
    return {
        "running": orchestrator.CHAT_IS_RUNNING
    }

@app.post("/run-gerente-geral")
async def run_gerente_geral_endpoint(background_tasks: BackgroundTasks):
    """Aciona a esteira completa do Gerente Geral."""
    import subprocess
    import sys
    import os
    
    # Verifica se já está rodando
    try:
        res = subprocess.run(["pgrep", "-f", "gerente_geral.py"], capture_output=True, text=True)
        if res.stdout.strip():
            return {"status": "already_running", "message": "O Gerente Geral já está trabalhando!"}
    except Exception:
        pass

    def run_gerente():
        gerente_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gerente_geral.py"))
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        log_file_path = "/tmp/gerente_geral.log"
        cwd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        try:
            with open(log_file_path, "w") as f:
                subprocess.Popen([python_exec, gerente_path], stdout=f, stderr=f, cwd=cwd_path)
        except Exception as e:
            print(f"Erro ao disparar gerente geral: {e}")
            
    background_tasks.add_task(run_gerente)
    return {"status": "started", "message": "Gerente Geral iniciado no Workspace!"}

@app.get("/status-gerente-geral")
async def status_gerente_geral_endpoint():
    """Retorna se o Gerente Geral está rodando."""
    import subprocess
    try:
        res = subprocess.run(["pgrep", "-f", "gerente_geral.py"], capture_output=True, text=True)
        is_running = bool(res.stdout.strip())
        return {"running": is_running}
    except Exception:
        return {"running": False}

@app.post("/run-nova-captacao")
async def run_nova_captacao_endpoint(background_tasks: BackgroundTasks):
    """Aciona a Nova Captação (Caixa de Entrada)."""
    import subprocess
    import sys
    import os
    import urllib.request

    try:
        # Pgrep checking for the script name directly instead of dummy process
        res = subprocess.run(["pgrep", "-f", "olx_captacao/fase1_coleta_links.py"], capture_output=True, text=True)
        if res.stdout.strip():
            return {"status": "already_running", "message": "A Nova Captação já está rodando!"}
    except Exception:
        pass

    def run_captacao():
        python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"))
        cwd_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Disable python log buffering so logs appear in real-time in tail -f
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        print("🚀 INICIANDO NOVA CAPTAÇÃO (CAIXA DE ENTRADA)")
        try:
            subprocess.run([python_exec, "olx_captacao/fase1_coleta_links.py"], cwd=cwd_path, env=env)
            
            from dotenv import load_dotenv
            load_dotenv(os.path.join(cwd_path, "scraper", ".env"))
            lote_fase2 = os.getenv("LOTE_FASE2", "50")
            subprocess.run([python_exec, "olx_captacao/fase2_extrai_dados.py", "--lote", lote_fase2], cwd=cwd_path, env=env)
            
            subprocess.run([python_exec, "olx_captacao/fase2_5_filtro_mercado.py"], cwd=cwd_path, env=env)
            
            comando_maps = "import sys, os; sys.path.append('scraper'); from dotenv import load_dotenv; load_dotenv(os.path.join('scraper', '.env')); import asyncio; from tools.geocoder_maps_scraper import main; asyncio.run(main())"
            subprocess.run([python_exec, "-c", comando_maps], cwd=cwd_path, env=env)
            
            # Aciona APENAS a Extração de Telefones (via navegador oculto), sem enviar mensagens
            print("🚀 INICIANDO EXTRAÇÃO DE TELEFONE (SEM MENSAGEM)")
            try:
                import urllib.request
                req = urllib.request.Request("http://localhost:8765/extract-phone/batch?lote=5", method="POST")
                urllib.request.urlopen(req)
            except Exception as ex:
                print(f"Aviso ao iniciar extração de telefone: {ex}")            
            print("\n" + "="*60)
            print("✅ ROTINA FINALIZADA: A Nova Captação concluiu todas as suas fases com sucesso!")
            print("="*60 + "\n")
        except Exception as e:
            print(f"Erro na nova captação: {e}")

    background_tasks.add_task(run_captacao)
    return {"status": "started", "message": "Nova Captação iniciada!"}

if __name__ == "__main__":
    import uvicorn
    # A porta padrão será 8765 para não conflitar com nada do React
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)
