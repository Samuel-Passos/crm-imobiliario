import asyncio
import json
import os
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright

async def main():
    load_dotenv('.env')
    sup = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

    print("Buscando 10 links na base...")
    res = sup.table('imoveis').select('url').eq('ativo', True).limit(10).execute()
    urls = [r['url'] for r in res.data if r.get('url')]
    
    if not urls:
        print("Nenhuma URL encontrada.")
        return

    all_keys = set()
    all_props = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        for url in urls:
            print(f"Visitando: {url}")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                dl = await page.evaluate("window.dataLayer")
                if dl:
                    for entry in dl:
                        if isinstance(entry, dict) and entry.get('page', {}).get('adDetail'):
                            ad_detail = entry['page']['adDetail']
                            for k in ad_detail.keys():
                                all_keys.add(k)
                            
                            ad_props = entry['page'].get('adProperties', [])
                            for prop in ad_props:
                                if prop.get('name'):
                                    all_props.add(prop.get('name'))
                            break
            except Exception as e:
                print(f"Erro ao carregar {url}: {e}")
        
        await browser.close()

    print("\n====================")
    print("CHAVES UNICAS EM adDetail:")
    print("====================")
    for k in sorted(all_keys):
        print(k)

    print("\n====================")
    print("CHAVES UNICAS EM adProperties (name):")
    print("====================")
    for p in sorted(all_props):
        print(p)

if __name__ == "__main__":
    asyncio.run(main())
