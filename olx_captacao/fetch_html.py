import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        url = 'https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/terrenos/alugo-para-eventos-chacara-no-bairro-capuava-1527297070'
        await page.goto(url, wait_until='domcontentloaded')
        html = await page.content()
        with open('page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        await browser.close()

asyncio.run(main())
