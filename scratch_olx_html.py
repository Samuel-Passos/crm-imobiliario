import asyncio
from playwright.async_api import async_playwright
import re

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?f=p"
        await page.goto(url, wait_until="domcontentloaded")
        html = await page.content()
        
        # Search for elements containing "Próxima"
        matches = re.findall(r'<[^>]*Próxima[^>]*>', html, re.IGNORECASE)
        print("Matches for Próxima:")
        for m in matches:
            print(m)
            
        # Or next-page
        matches2 = re.findall(r'<[^>]*next-page[^>]*>', html, re.IGNORECASE)
        print("Matches for next-page:")
        for m in matches2:
            print(m)

        await browser.close()

asyncio.run(run())
