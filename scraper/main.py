from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Aqui vamos importar o orquestrador que roda os ciclos de IA
import orchestrator
from orchestrator import run_daily_scraper_cycle, extract_phone_single_lead
from tools.phone_extractor import extract_phones_from_olx
from pegar_cookies_nativos import extrair_cookies_do_chrome_ubuntu
import tools.geocoder
import tools.geocoder_reprocess
import tools.geocoder_google
import tools.geocoder_google_reprocess
import tools.geocode_signals as geocode_signals

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

# Libera CORS para o CRM React no localhost:5173 e 5174
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
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
    background_tasks.add_task(tools.geocoder_google.main)
    return {"status": "started", "message": "Geocodificador Google Maps iniciado em background!"}

@app.post("/geocode/google/reprocess")
async def run_geocoder_google_reprocess(background_tasks: BackgroundTasks):
    """
    Reprocessa imóveis com geocode_needs_review=True usando a Google Maps API.
    Esses imóveis foram marcados pelo Nominatim como imprecisos (bairro/cidade).
    """
    background_tasks.add_task(tools.geocoder_google_reprocess.main)
    return {"status": "started", "message": "Reprocessamento Google Maps iniciado! Imóveis com needs_review serão corrigidos."}

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

if __name__ == "__main__":
    import uvicorn
    # A porta padrão será 8765 para não conflitar com nada do React
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)
