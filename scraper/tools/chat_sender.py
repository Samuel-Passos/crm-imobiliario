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

async def send_chat_message_olx(url: str, mensagem: str) -> Dict[str, Any]:
    """
    Usa o Browser Use para acessar a URL do anúncio OLX,
    abrir o chat lateral e enviar uma mensagem.
    """
    
    # O prompt do agente: abrir chat, digitar, enviar e confirmar
    task = f"""
    Sua missão é enviar uma mensagem de chat no OLX. 
    A URL do anúncio é: {url}
    
    A mensagem a ser enviada é EXATAMENTE esta:
    "{mensagem}"
    
    PASSO A PASSO RIGOROSO:
    1. A url pode cair em uma tela de erro se o anúncio for apagado. Se isso acontecer, retorne {{"sucesso": false, "motivo": "anuncio_expirado"}}
    2. Se a página carregar, encontre o botão principal que diz "Chat", ou o ícone de balão de chat, e clique nele. (O painel de chat da OLX vai abrir na lateral).
    3. Digite a mensagem fornecida no campo de texto do chat.
    4. Envie a mensagem clicando no botão de enviar (geralmente uma setinha) ou apertando "Enter".
    5. Confirme visualmente se a mensagem apareceu na conversa.
    
    6. RESULTADO FINAL (RETORNE APENAS JSON):
       Se a mensagem foi enviada, retorne: {{"sucesso": true, "motivo": null}}
       Se não conseguiu achar o chat ou houve erro, retorne: {{"sucesso": false, "motivo": "explicacao do que deu errado"}}
    """
    
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser
    )
    
    try:
        print(f"💬 Iniciando envio de chat para: {url}")
        history = await agent.run()
        
        resultado_final = history.final_result()
        if not resultado_final:
            return {"sucesso": False, "motivo": "Agente não retornou um resultado claro."}
            
        limpo = resultado_final.strip()
        if limpo.startswith("```json"): limpo = limpo[7:]
        if limpo.startswith("```"): limpo = limpo[3:]
        if limpo.endswith("```"): limpo = limpo[:-3]
        
        dados = json.loads(limpo.strip())
        
        if dados.get("sucesso"):
            print("✅ Mensagem enviada com sucesso no chat da OLX!")
        else:
            print(f"❌ Falha ao enviar chat: {dados.get('motivo')}")
            
        return dados
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Erro ao decodificar JSON do LLM: {resultado_final}")
        return {"sucesso": False, "motivo": "Falha de parser (JSON inválido)"}
    except Exception as e:
        print(f"🚨 Erro na automação: {e}")
        return {"sucesso": False, "motivo": str(e)}

if __name__ == "__main__":
    import sys
    url_teste = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/linda-casa-condominio-terra-nova-sao-jose-dos-campos-sp-r-610-000-1479566282"
    msg_teste = "Olá! Tenho interesse no imóvel. Teste de automação."
    
    async def teste_local():
        resultado = await send_chat_message_olx(url_teste, msg_teste)
        print("\nResultado Final:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        await browser.close()
        
    asyncio.run(teste_local())
