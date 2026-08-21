import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv

from geocoder_maps_scraper import geocodificar_imovel_maps_scraper, _configurar_contexto
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

load_dotenv("../.env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def main():
    # Pega o imovel ativo mais recente sem latitude
    res = supabase.table("imoveis").select("id, rua, bairro, cidade, estado, numero, cep, nome_condominio, url").eq("ativo", True).is_("latitude", "null").order("id", desc=True).limit(1).execute()
    
    if not res.data:
        print("Nenhum imovel recente sem coordenada encontrado.")
        return

    imovel = res.data[0]
    print(f"Testando Imóvel ID: {imovel['id']} - {imovel['url']}")
    
    async with async_playwright() as p:
        context = await _configurar_contexto(p)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        rua = imovel.get('rua') or ''
        bairro = imovel.get('bairro') or ''
        cidade = imovel.get('cidade') or 'São José dos Campos'
        estado = imovel.get('estado') or 'SP'
        numero = imovel.get('numero') or ''
        cep = imovel.get('cep') or ''
        cond = imovel.get('nome_condominio') or ''
        
        coords, est, prec = await geocodificar_imovel_maps_scraper(page, rua, bairro, cidade, estado, numero, cep, cond)
        print(f"Resultado: Coords={coords}, Estrategia='{est}', Precisao='{prec}'")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
