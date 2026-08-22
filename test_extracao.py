import asyncio
import sys
import os
import json

# Add scraper to sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scraper'))

from scraper.tools.browser_manager import start_browser, get_page, close_browser
from scraper.tools.phone_extractor import extract_phones_from_olx

URL1 = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/casa-esquina-com-edicula-1528485638"
URL2 = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/casa-a-venda-1528464105"

async def test_urls():
    print("Iniciando browser_manager...")
    await start_browser()
    page = get_page()
    
    if not page:
        print("Erro: não foi possível obter a página.")
        return

    print(f"\n{'='*60}")
    print(f"Testando URL 1: {URL1}")
    print(f"{'='*60}")
    res1 = await extract_phones_from_olx(URL1, page)
    print("\n[RESULTADO URL 1]")
    print(json.dumps(res1, indent=2, ensure_ascii=False))
    
    print(f"\n{'='*60}")
    print(f"Testando URL 2: {URL2}")
    print(f"{'='*60}")
    res2 = await extract_phones_from_olx(URL2, page)
    print("\n[RESULTADO URL 2]")
    print(json.dumps(res2, indent=2, ensure_ascii=False))
    
    print("\nFechando browser...")
    await close_browser()

if __name__ == "__main__":
    asyncio.run(test_urls())
