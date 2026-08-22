import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scraper'))
from scraper.tools.browser_manager import start_browser, get_page, close_browser

URL1 = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/casa-esquina-com-edicula-1528485638"
URL2 = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/casa-a-venda-1528464105"

async def dump_html():
    await start_browser()
    page = get_page()
    
    await page.goto(URL1, wait_until='domcontentloaded')
    await asyncio.sleep(5)
    html1 = await page.content()
    with open("dump1.html", "w") as f:
        f.write(html1)
        
    await page.goto(URL2, wait_until='domcontentloaded')
    await asyncio.sleep(5)
    html2 = await page.content()
    with open("dump2.html", "w") as f:
        f.write(html2)
        
    await close_browser()

if __name__ == "__main__":
    asyncio.run(dump_html())
