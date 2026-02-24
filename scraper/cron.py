import time
import requests
import schedule
from datetime import datetime

# URL do servidor FastAPI local
API_URL = "http://localhost:8765/run"

def run_job():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏰ Disparando rotina diária do Scraper...")
    try:
        response = requests.post(API_URL)
        if response.status_code == 200:
            print("✅ Sucesso! O FastAPI aceitou a requisição e iniciou o ciclo em background.")
        else:
            print(f"⚠️ Erro ao acionar a API. Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("🚨 Erro: Não foi possível conectar ao FastAPI. Ele está rodando na porta 8765?")

if __name__ == "__main__":
    
    # Executa sempre às 9AM (Pode alterar para o horário que desejar)
    HORARIO = "09:00"
    
    schedule.every().day.at(HORARIO).do(run_job)
    
    print("="*50)
    print(f"🤖 Scraper Cron Schedule ATIVADO")
    print(f"O ciclo de extração rodará todos os dias às {HORARIO}.")
    print("Mantenha este terminal aberto!")
    print("="*50)
    
    while True:
        schedule.run_pending()
        time.sleep(60) # Checa a cada minuto
