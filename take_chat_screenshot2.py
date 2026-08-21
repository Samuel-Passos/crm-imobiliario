import asyncio
import sys
sys.path.append('scraper')
from tools.browser_manager import start_browser, close_browser

async def main():
    print("Ligando motor...")
    context = await start_browser()
    page = context.pages[0]
    
    print("Navegando...")
    await page.goto("https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/o-p-o-r-t-u-n-i-d-a-d-e-sobrado-jardim-oriente-venda-1525441605", timeout=30000)
    await page.wait_for_timeout(3000)
    
    btn = page.locator('button:has-text("Chat")').first
    if await btn.is_visible():
        print("Chat button found. Clicking...")
        await btn.click()
        await page.wait_for_timeout(5000)
        await page.screenshot(path="chat_after_click.png", full_page=True)
        print("Pages open:", len(context.pages))
    else:
        print("Chat button NOT found.")
        await page.screenshot(path="chat_button_not_found.png", full_page=True)
        
    print("Desligando motor...")
    await close_browser()

asyncio.run(main())
