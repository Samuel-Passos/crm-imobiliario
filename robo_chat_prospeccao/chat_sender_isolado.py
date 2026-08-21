import asyncio
import random
from typing import Dict, Any
from playwright.async_api import Page, BrowserContext

MENSAGEM_PADRAO = """Meu nome é Samuel sou corretor de imoveis autônomo, tenho uma platafomra com mais de 500 contatos de corretores o que facilita muito a venda, permuta ou compra de imóveis.

Gostaria de saber se posso trabalhar com seu imóvel junto a nossa carteira de clientes e investidores e corretores parceiros."""

async def _digitar_humano(page: Page, loc, texto: str):
    """
    Clica no elemento e digita simulando digitação humana (delay entre teclas).
    Usa o método type do Playwright para garantir compatibilidade com acentos.
    """
    await loc.click()
    await asyncio.sleep(random.uniform(0.3, 0.8))

    # O usuário pediu para "colar de uma só vez a mensagem",
    # fill() faz exatamente isso no Playwright, copiando o bloco todo no input.
    await loc.fill(texto)
    await asyncio.sleep(random.uniform(0.5, 1.0))

    await asyncio.sleep(random.uniform(0.5, 1.2))


async def send_chat_isolado(context: BrowserContext, url: str) -> Dict[str, Any]:
    """
    1. Abre aba no anúncio.
    2. Localiza o botão //*[@id="price-box-button-chat"].
    3. Ao clicar, captura a nova aba aberta do chat.
    4. Digita a mensagem em //*[@id="input-text-message"].
    5. Pressiona Enter.
    """
    dados = {
        "enviado": False,
        "erro": None
    }
    
    print(f"\n💬 [ROBO ISOLADO] Iniciando navegação para: {url}")
    page = await context.new_page()
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Delay de renderização
        await asyncio.sleep(random.uniform(2.0, 4.0))
        
        # Localiza botão pelo XPath exato fornecido ou fallbacks
        xpaths_chat = [
            '//*[@id="price-box-button-chat"]',
            'button[data-testid="chat-button"]',
            'button:has-text("Chat")',
            'a:has-text("Chat")'
        ]
        
        btn_chat = None
        for xpath in xpaths_chat:
            loc = page.locator(f"xpath={xpath}" if xpath.startswith('/') else xpath).first
            try:
                await loc.wait_for(state="visible", timeout=6000)
                btn_chat = loc
                print(f"  ✅ Botão de chat localizado via: {xpath}")
                break
            except Exception:
                pass
                
        if not btn_chat:
            await page.screenshot(path="debug_chat_btn.png")
            print("  ❌ Botão de chat não encontrado no anúncio a tempo. (Screenshot salvo)")
            dados["erro"] = "botao_chat_nao_encontrado"
            await page.close()
            return dados
            
        await btn_chat.scroll_into_view_if_needed()
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        # O clique neste botão na OLX abre uma *nova aba*
        print("  -> Clicando no botão e aguardando nova janela do chat...")
        async with context.expect_page() as new_page_info:
            await btn_chat.click()
        
        chat_page = await new_page_info.value
        await chat_page.wait_for_load_state("domcontentloaded")
        print(f"  ✅ Nova aba do chat aberta: {chat_page.url}")
        
        # Aguarda a renderização do React na aba de chat
        await asyncio.sleep(random.uniform(3.0, 5.0))
        
        # Seleciona o input pelo XPath fornecido
        xpath_input = '//*[@id="input-text-message"]'
        input_msg = chat_page.locator(f"xpath={xpath_input}").first
        
        try:
            await input_msg.wait_for(state="visible", timeout=15000)
            print("  ✅ Campo de mensagem localizado.")
        except Exception:
            print("  ❌ Campo de mensagem não ficou visível a tempo.")
            dados["erro"] = "input_mensagem_nao_encontrado"
            await chat_page.close()
            await page.close()
            return dados
            
        # Digita a mensagem como humano
        print(f"  -> Digitando a mensagem ({len(MENSAGEM_PADRAO)} caracteres)...")
        await _digitar_humano(chat_page, input_msg, MENSAGEM_PADRAO)
        
        # Envia com Enter
        print("  -> Pressionando Enter para enviar...")
        await input_msg.press("Enter")
        await asyncio.sleep(random.uniform(1.0, 2.0))
        
        print("  ✅ [SUCESSO] Mensagem enviada e enter pressionado!")
        dados["enviado"] = True
        
        # Fecha as abas utilizadas
        await chat_page.close()
        await page.close()
        
    except Exception as e:
        print(f"  🚨 [ERRO CRÍTICO] {e}")
        dados["erro"] = str(e)
        
        try:
            await page.close()
        except:
            pass
            
    return dados
