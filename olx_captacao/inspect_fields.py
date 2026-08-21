import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Using a regular property URL (not kitnet) that is more likely to have full fields
        url = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/lindo-apartamento-a-venda-em-sao-jose-dos-campos-spl-residencial-club-ref-77405-1327118128"
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        await page.goto(url, wait_until='domcontentloaded')
        
        dl = await page.evaluate("window.dataLayer")
        if dl:
            for entry in dl:
                if isinstance(entry, dict) and entry.get('page', {}).get('adDetail'):
                    print('--- adDetail Keys ---')
                    print(list(entry['page']['adDetail'].keys()))
                    print('\n--- adProperties ---')
                    for prop in entry['page'].get('adProperties', []):
                        print(prop.get('name'), '=', prop.get('value'))
                    break
        else:
            print("dataLayer not found")
        await browser.close()

asyncio.run(main())
