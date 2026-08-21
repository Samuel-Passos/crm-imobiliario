import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        await page.goto("https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/o-p-o-r-t-u-n-i-d-a-d-e-sobrado-jardim-oriente-venda-1525441605", timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Procura botao chat
        btn = page.locator('button:has-text("Chat")').first
        if await btn.is_visible():
            print("Chat button found. Clicking...")
            await btn.click()
            await page.wait_for_timeout(5000)
            await page.screenshot(path="chat_after_click.png")
            
            # Checa se abriu nova aba ou modal
            print("Pages open:", len(page.context.pages))
        else:
            print("Chat button NOT found.")
            await page.screenshot(path="chat_button_not_found.png")
            
        await browser.close()

asyncio.run(main())
