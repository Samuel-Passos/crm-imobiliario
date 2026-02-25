from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio

# Aqui vamos importar o orquestrador que roda os ciclos de IA
import orchestrator
from orchestrator import run_daily_scraper_cycle, prospect_single_lead, extract_phone_single_lead

app = FastAPI(title="OLX Scraper Pro", description="Orquestrador Python com Browser Use")

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

@app.post("/prospect")
async def prospect_one_lead(payload: ImovelRequest, background_tasks: BackgroundTasks):
    """
    O usuário clicou em "Iniciar Prospecção Agora" para um imóvel específico no CRM.
    """
    background_tasks.add_task(prospect_single_lead, payload.imovel_id)
    return {"status": "started", "message": f"Prospecção do imóvel {payload.imovel_id} enviada para a fila!"}

if __name__ == "__main__":
    import uvicorn
    # A porta padrão será 8765 para não conflitar com nada do React
    uvicorn.run("main:app", host="0.0.0.0", port=8765, reload=True)
