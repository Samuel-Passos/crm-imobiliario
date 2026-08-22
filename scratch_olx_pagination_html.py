import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?f=p"
        await page.goto(url, wait_until="domcontentloaded")
        html = await page.evaluate('''() => {
            const list = document.querySelector('[data-testid="ad-list"]') || document.body;
            // Get all a tags that have href containing "?o="
            const links = Array.from(document.querySelectorAll('a[href*="?o="]'));
            return links.map(l => l.outerHTML).join('\\n');
        }''')
        print(html)
        await browser.close()

asyncio.run(run())
