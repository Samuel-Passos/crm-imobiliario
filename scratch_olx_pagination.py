import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Navigate to a known page
        url = "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?f=p&o=42"
        await page.goto(url, wait_until="domcontentloaded")
        
        # Check next page button
        has_next = await page.evaluate('''() => {
            const nextBtn = document.querySelector('[data-testid="next-page"]');
            if (!nextBtn) return "NO_BUTTON";
            return nextBtn.disabled ? "DISABLED" : "ENABLED";
        }''')
        
        # Check total pages in dataLayer
        total_pages = await page.evaluate('''() => {
            const dl = window.dataLayer || [];
            for (let i = 0; i < dl.length; i++) {
                if (dl[i].page && dl[i].page.adList && dl[i].page.adList.totalPages) {
                    return dl[i].page.adList.totalPages;
                }
            }
            return null;
        }''')
        
        # Check canonical URL
        url_now = page.url
        print(f"Has Next Button: {has_next}")
        print(f"Total pages in dataLayer: {total_pages}")
        print(f"URL after load: {url_now}")
        
        await browser.close()

asyncio.run(run())
