import asyncio
import json
from typing import Dict, Any
from browser_use import Agent, Browser
from langchain_groq import ChatGroq
from pydantic import ConfigDict
from dotenv import load_dotenv
import os

load_dotenv()

class CustomChatGroq(ChatGroq):
    provider: str = 'groq'
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = getattr(self, 'model_name', 'llama3')

llm = CustomChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
)

CHROME_PROFILE_PATH = os.getenv('CHROME_PROFILE_PATH', '/home/samuel/.config/google-chrome')

browser = Browser(
    headless=False,
    user_data_dir=CHROME_PROFILE_PATH
)

async def read_latest_chat_reply(url: str) -> Dict[str, Any]:
    """
    Acessa o anúncio, abre o painel lateral de chat
    e extrai A ÚLTIMA MENSAGEM enviada pela OUTRA PESSOA (o proprietário/vendedor).
    """
    
    task = f"""
    Sua missão é ler a última resposta recebida em um chat do OLX.
    URL: {url}
    
    PASSO A PASSO:
    1. Carregue a página do anúncio.
    2. Clique no botão "Chat" para abrir as mensagens antigas.
    3. Leia a conversa no painel lateral.
    4. Identifique as mensagens enviadas por VOCÊ (eu) e mensagens enviadas pelo VENDEDOR (proprietário).
    5. Descubra qual foi a ÚLTIMA mensagem inteira da conversa:
       - Se a última mensagem do chat foi SUA (significa que ele não respondeu ainda), ignore.
       - Se a última mensagem do chat foi DO VENDEDOR (ele nos respondeu!), grave o texto exato dela.
       
    6. RESULTADO FINAL (RETORNE APENAS JSON):
       - Se o vendedor respondeu (a última msg é dele), retorne:
         {{"respondeu": true, "texto_resposta": "o que ele disse aqui"}}
       - Se o vendedor não respondeu (a última msg é sua ou a conversa está vazia), retorne:
         {{"respondeu": false, "texto_resposta": null}}
    """
    
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser
    )
    
    try:
        print(f"👀 Iniciando leitura de chat para: {url}")
        history = await agent.run()
        
        resultado_final = history.final_result()
        if not resultado_final:
            return {"respondeu": False, "texto_resposta": None, "erro": "Sem retorno."}
            
        limpo = resultado_final.strip()
        if limpo.startswith("```json"): limpo = limpo[7:]
        if limpo.startswith("```"): limpo = limpo[3:]
        if limpo.endswith("```"): limpo = limpo[:-3]
        
        dados = json.loads(limpo.strip())
        
        if dados.get("respondeu"):
            print(f"📩 Resposta encontrada! '{dados.get('texto_resposta')}'")
        else:
            print("⏳ Nenhuma resposta nova (estão nos ignorando).")
            
        return dados
        
    except Exception as e:
        print(f"🚨 Erro na automação: {e}")
        return {"respondeu": False, "texto_resposta": None, "erro": str(e)}

if __name__ == "__main__":
    url_teste = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/linda-casa-condominio-terra-nova-sao-jose-dos-campos-sp-r-610-000-1479566282"
    
    async def teste_local():
        resultado = await read_latest_chat_reply(url_teste)
        print("\nResultado Final:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        await browser.close()
        
    asyncio.run(teste_local())
