import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client
from playwright.async_api import async_playwright

# IDs das colunas
COLUNA_CAIXA_ENTRADA = '71723ac2-b725-4bf9-b215-6e7993d93673'
COLUNA_EXTRACAO = '9cfb9d98-89cb-4169-88e1-db399f3ce877'
COLUNA_EXPIRADOS = '5f01efe9-6531-4259-9927-76c130e2851d'

async def check_is_expired(page, url):
    try:
        # Acesso timeout curto pra não perder tempo
        response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        
        # Redirecionou pra home ou categoria raiz
        current_url = page.url
        if current_url.endswith(".olx.com.br/") or current_url.endswith("/estado-sp") or "/imoveis" not in current_url:
            return True
            
        if response and response.status in (404, 410):
            return True
            
        title = await page.title()
        if "não encontrado" in title.lower() or "not found" in title.lower():
            return True
            
        # Elemento na página
        ops = await page.locator("text=Ops! Esse anúncio").count()
        if ops > 0:
            return True
            
        return False
    except Exception as e:
        print(f"    Erro ao acessar {url}: {e}")
        # Em caso de timeout/bloqueio, consideramos ativo para não descartar indevidamente
        return False

async def main():
    print("Iniciando Limpador de Expirados...")
    # Configura Supabase
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", "scraper", ".env"))
    sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    
    # Busca imoveis
    res = sup.table('imoveis').select('id, list_id, titulo, url, kanban_coluna_id').in_('kanban_coluna_id', [COLUNA_CAIXA_ENTRADA, COLUNA_EXTRACAO]).execute()
    imoveis = res.data
    
    if not imoveis:
        print("Nenhum imóvel encontrado nas colunas iniciais.")
        return
        
    print(f"Total de {len(imoveis)} anúncios para verificar.")
    
    async with async_playwright() as p:
        # Modo headless verdadeiro (invisível) sem carregar sessão
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        total_expirados = 0
        
        # Sequencial pra não sobrecarregar e tomar block do cloudflare.
        for index, im in enumerate(imoveis):
            print(f"[{index+1}/{len(imoveis)}] Checando ID {im['id']} - {im['list_id']}...")
            page = await context.new_page()
            is_expired = await check_is_expired(page, im['url'])
            await page.close()
            
            if is_expired:
                print(f"  ❌ EXPIRADO: Movendo para lixo.")
                sup.table('imoveis').update({
                    'kanban_coluna_id': COLUNA_EXPIRADOS,
                    'anuncio_expirado': True
                }).eq('id', im['id']).execute()
                total_expirados += 1
            else:
                print(f"  ✅ ATIVO.")
                
            # Um pequeno delay pra não irritar o firewall
            await asyncio.sleep(1)
            
        await browser.close()
        print(f"\nFinalizado! {total_expirados} anúncios expirados foram movidos pro lixo.")

if __name__ == "__main__":
    asyncio.run(main())
