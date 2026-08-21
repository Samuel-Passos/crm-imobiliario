import asyncio
import os
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from chat_sender_isolado import send_chat_isolado, MENSAGEM_PADRAO

# Configurações do Supabase (reaproveitando o env da pasta scraper)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "scraper", ".env")
load_dotenv(dotenv_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Caminho para sessão (Cookies da OLX)
SCRAPER_DIR = os.path.join(os.path.dirname(__file__), "..", "scraper")
SESSION_FILE = os.path.normpath(os.path.join(SCRAPER_DIR, "olx_session.json"))
CHROMIUM_PATH = "/usr/bin/chromium"

KANBAN_SCRIPT1_ID = "934d8c3e-b887-482d-86ce-7fdeafe3101a"

async def _criar_contexto_isolado(p):
    """Cria um contexto do Playwright com bypass Cloudflare."""
    browser = await p.chromium.launch(
        executable_path=CHROMIUM_PATH,
        headless=False,  # Deixar False temporariamente se quiser ver rodando, ou True
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )
    
    context_kwargs = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
    }
    
    if os.path.exists(SESSION_FILE):
        context_kwargs["storage_state"] = SESSION_FILE
        print(f"🍪 Usando cookies reais da sessão OLX ({SESSION_FILE})")
    else:
        print("⚠️ Arquivo olx_session.json não encontrado — rodando sem cookies.")
        
    context = await browser.new_context(**context_kwargs)
    
    # Aplica stealth em todas as novas páginas do contexto
    stealth = Stealth()
    context.on('page', lambda page: asyncio.create_task(stealth.apply_stealth_async(page)))
    
    return browser, context

async def processar_envio(url: str):
    """
    Função principal que orquestra o Playwright e atualiza o banco de dados.
    """
    print("=" * 60)
    print("🚀 INICIANDO TESTE DO ROBÔ AUTÔNOMO DE CHAT")
    print(f"URL Alvo: {url}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser, context = await _criar_contexto_isolado(p)
        
        try:
            # Roda o chat sender isolado
            resultado = await send_chat_isolado(context, url)
            
            if resultado.get("enviado"):
                print("\n✅ MENSAGEM ENVIADA COM SUCESSO! Atualizando banco de dados...")
                
                # 1. Busca o ID do imóvel usando a URL
                # A URL que salvamos na tabela imoveis pode variar parâmetros finais,
                # então buscaremos pelo ID extraído da URL ou ILIKE.
                # Extrai os dígitos finais (list_id) da URL:
                import re
                match = re.search(r'-(\d+)(?:\?.*)?$', url)
                if match:
                    list_id = match.group(1)
                    res = supabase.table("imoveis").select("id").eq("list_id", int(list_id)).execute()
                    
                    if res.data:
                        imovel_id = res.data[0]["id"]
                        
                        try:
                            # 2. Registra na tabela prospecoes_chat (tentamos sem a coluna conflitante se o cache estiver velho)
                            supabase.table("prospecoes_chat").upsert({
                                "imovel_id": imovel_id,
                                "status": "aguardando_resposta",
                                "data_ultimo_envio": datetime.now(timezone.utc).isoformat(),
                                "numero_tentativas": 1,
                            }, on_conflict="imovel_id").execute()
                            print("  ✅ Registrado na tabela 'prospecoes_chat'.")
                        except Exception as e:
                            print(f"  ⚠️ Aviso ao inserir em prospecoes_chat: {e}")
                        
                        # 3. Move no Kanban para "Script 1"
                        supabase.table("imoveis").update({
                            "kanban_coluna_id": KANBAN_SCRIPT1_ID
                        }).eq("id", imovel_id).execute()
                        print("  ✅ Imóvel movido para a coluna 'Script 1' do Kanban.")
                        
                    else:
                        print(f"  ⚠️ Imóvel com list_id {list_id} não encontrado na tabela 'imoveis'. Pulando DB update.")
                else:
                    print("  ⚠️ Não foi possível extrair list_id da URL. Pulando DB update.")
            else:
                print("\n❌ Falha no envio da mensagem.")
                print(f"Motivo: {resultado.get('erro')}")
                
        finally:
            await browser.close()
            print("=" * 60)
            print("🏁 FIM DA EXECUÇÃO")
            print("=" * 60)

if __name__ == "__main__":
    url_teste = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/kitnet-1527823856?lis=listing_1000"
    asyncio.run(processar_envio(url_teste))
