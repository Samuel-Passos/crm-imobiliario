import asyncio
import os
import sys

# Adiciona o diretorio atual ao path
sys.path.append(os.path.dirname(__file__))

from browser_manager_chat import start_chat_browser, close_chat_browser, get_chat_page

async def main():
    await start_chat_browser()
    page = get_chat_page()
    
    url = "https://chat.olx.com.br/?list-id=1525441605"
    print(f"Navegando para {url}")
    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
    await asyncio.sleep(10.0) # Espera carregar as mensagens
    
    html = await page.evaluate('''() => {
        return document.body.outerHTML;
    }''')
    
    with open("dom_dump.txt", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Salvo em dom_dump.txt")
    await close_chat_browser()

if __name__ == "__main__":
    asyncio.run(main())
