import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Navigate to a known page (first page)
        url = "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?f=p"
        await page.goto(url, wait_until="domcontentloaded")
        has_next = await page.evaluate('''() => {
            const btn = document.querySelector('[data-testid="next-page"]');
            if (!btn) return false;
            return !btn.disabled && !btn.hasAttribute('disabled');
        }''')
        print(f"Page 1 has next: {has_next}")
        
        # Navigate to last page (assuming 42)
        url_42 = "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?f=p&o=42"
        await page.goto(url_42, wait_until="domcontentloaded")
        has_next_42 = await page.evaluate('''() => {
            const btn = document.querySelector('[data-testid="next-page"]');
            if (!btn) return false;
            return !btn.disabled && !btn.hasAttribute('disabled');
        }''')
        print(f"Page 42 has next: {has_next_42}")

        await browser.close()

asyncio.run(run())
