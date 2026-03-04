import asyncio
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente (Supabase, OpenAI)
load_dotenv()

async def main():
    print("🤖 ChatBot iniciado com sucesso isolado do Scraper!")
    print("Pronto para se conectar ao banco e enviar as mensagens via Browser Use.")
    
if __name__ == "__main__":
    asyncio.run(main())
