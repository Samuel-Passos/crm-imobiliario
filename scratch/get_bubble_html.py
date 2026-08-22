import asyncio
import os
import sys

# Adiciona o diretorio atual ao path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "robo_chat_prospeccao"))

from browser_manager_chat import start_chat_browser, close_chat_browser, get_chat_page

async def main():
    await start_chat_browser()
    page = get_chat_page()
    
    url = "https://chat.olx.com.br/"
    print(f"Navegando para {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(5.0)
    
    print("Clicando no chat...")
    try:
        await page.click('a[href*="1525441605"]')
        await asyncio.sleep(5.0)
    except Exception as e:
        print(f"Erro ao clicar: {e}")
    
    html = await page.evaluate('''() => {
        const msgs = document.querySelectorAll('[data-testid="message-bubble"], [class*="message-bubble"], [class*="MessageBubble"]');
        if (msgs.length === 0) return "Nenhuma mensagem encontrada.";
        
        let dump = "";
        for (let i = 0; i < msgs.length; i++) {
            let msg = msgs[i];
            let comp = window.getComputedStyle(msg);
            let parentComp = window.getComputedStyle(msg.parentElement);
            dump += `--- Msg ${i} ---\n`;
            dump += `Texto: ${msg.innerText.trim()}\n`;
            dump += `Align-self: ${comp.alignSelf}\n`;
            dump += `Background: ${comp.backgroundColor}\n`;
            dump += `Parent Justify: ${parentComp.justifyContent}\n`;
            dump += `HTML: ${msg.outerHTML}\n\n`;
        }
        return dump;
    }''')
    
    print("DUMP DA MENSAGEM:")
    print(html)
    await close_chat_browser()

if __name__ == "__main__":
    asyncio.run(main())
