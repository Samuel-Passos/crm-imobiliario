import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?f=p"
        await page.goto(url, wait_until="networkidle")
        html = await page.content()
        with open("olx_page.html", "w") as f:
            f.write(html)
        await browser.close()

asyncio.run(run())
