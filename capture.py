import asyncio
from playwright.async_api import async_playwright

URL1 = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/casa-esquina-com-edicula-1528485638"
URL2 = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/casa-a-venda-1528464105"

async def test_urls():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Loading {URL1}")
        await page.goto(URL1, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        await page.screenshot(path="url1.png")
        html1 = await page.content()
        with open("url1.html", "w") as f:
            f.write(html1)
            
        print(f"Loading {URL2}")
        await page.goto(URL2, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        await page.screenshot(path="url2.png")
        html2 = await page.content()
        with open("url2.html", "w") as f:
            f.write(html2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_urls())
