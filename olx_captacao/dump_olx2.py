import asyncio
from playwright.async_api import async_playwright
import json
import re

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        await page.goto("https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/kitnet-1527823856")
        
        # Get the entire HTML to search for JSON-like structures containing camanducaia
        html = await page.content()
        if "Camanducaia" in html:
            print("SIM, 'Camanducaia' está no HTML puro da página.")
            
            # Tentar achar de onde ele vem
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', html)
            if match:
                state_str = match.group(1)
                if "Camanducaia" in state_str:
                    print("Está dentro do window.__INITIAL_STATE__!")
                    # extract the JSON path
                    try:
                        data = json.loads(state_str)
                        # Busca recursiva para encontrar onde está a rua
                        def find_key(obj, target, path=""):
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    find_key(v, target, path + f"['{k}']")
                            elif isinstance(obj, list):
                                for i, v in enumerate(obj):
                                    find_key(v, target, path + f"[{i}]")
                            elif isinstance(obj, str) and target.lower() in obj.lower():
                                print(f"Encontrado em: {path} = {obj}")
                        
                        find_key(data, "Camanducaia")
                    except Exception as e:
                        print("Erro ao fazer parse do INITIAL_STATE", e)
                else:
                    print("Não está no INITIAL_STATE")
        else:
            print("Não encontrou 'Camanducaia' nem no HTML da página.")
        
        await browser.close()

asyncio.run(main())
