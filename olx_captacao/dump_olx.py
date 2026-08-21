import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        await page.goto("https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/kitnet-1527823856")
        dl = await page.evaluate("window.dataLayer")
        with open("dl.json", "w") as f:
            json.dump(dl, f, indent=2)
        await browser.close()

asyncio.run(main())
