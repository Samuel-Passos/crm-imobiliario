import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/studio-40m-patio-sao-jose-1528324681"
    KEYWORDS_EXPIRADO = [
        "anúncio finalizado", "ops!", "não encontrado",
        "anúncio desativado", "página não encontrada"
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await asyncio.sleep(2)
        
        title = await page.title()
        content = await page.content()
        print(f"Title: {title}")
        
        for kw in KEYWORDS_EXPIRADO:
            if kw in title.lower():
                print(f"FOUND IN TITLE: {kw}")
            if kw in content.lower():
                print(f"FOUND IN CONTENT: {kw}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
