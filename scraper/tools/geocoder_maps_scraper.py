"""
geocoder_maps_scraper.py
────────────────────────
Motor de geocodificação usando automação (Playwright) diretamente no Google Maps,
sem usar a API oficial (sem custos).

Estratégia:
  1. Montamos uma query baseada nos dados do imóvel.
  2. Acessamos `https://www.google.com/maps/search/{query}`.
  3. O Google Maps, ao encontrar o lugar, atualiza a URL incluindo as coordenadas,
     ex: `.../@-23.2201,-45.9080,15z...`.
  4. Extraímos essa latitude e longitude da URL via Expressão Regular (Regex).

Este script é feito para ser invocado pelo orquestrador.
"""

import os
import re
import asyncio
import random
from urllib.parse import quote_plus
from dotenv import load_dotenv
from supabase import create_client, Client
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth

import tools.geocode_signals as geocode_signals
from tools.geocoder import remover_sufixo_ibge

load_dotenv()
signals = geocode_signals

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None

STRATEGY_NAME = "Google Maps Scraper"

# Fingerprints para mascarar o scraper (Anti-Bot)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
]


async def _configurar_contexto(p) -> BrowserContext:
    """Configura e retorna um contexto headless anônimo do Playwright."""
    browser = await p.chromium.launch(
        executable_path="/usr/bin/chromium",
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    )
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport=random.choice(VIEWPORTS),
        locale='pt-BR',
        timezone_id='America/Sao_Paulo'
    )
    return context


def _extrair_coords_da_url(url: str) -> tuple[float, float] | None:
    """Extrai latitude e longitude da URL do Google Maps."""
    # O Google Maps insere coordenadas na URL no formato: /@latitude,longitude,zoom
    # Ex: https://www.google.com/maps/place/.../@-23.2201395,-45.9080536,15z
    match = re.search(r'/@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None


async def _aceitar_cookies(page: Page):
    """Clica no botão de aceitar cookies se a tela de consentimento aparecer."""
    try:
        accept_btn = page.locator('button:has-text("Aceitar"), button:has-text("Accept"), button:has-text("Concordo")').first
        if await accept_btn.count() > 0:
            await accept_btn.click()
            await asyncio.sleep(1)
    except Exception:
        pass


async def _tentar_busca(page: Page, query: str) -> tuple[float, float] | None:
    """Acessa a URL de busca do Google Maps e aguarda a URL mudar para pegar as coordenadas."""
    url_busca = f"https://www.google.com/maps/search/{quote_plus(query)}?hl=pt-BR"
    
    try:
        await page.goto(url_busca, wait_until='domcontentloaded', timeout=20000)
        
        # Aceita cookies na primeira vez
        await _aceitar_cookies(page)

        # Aguarda a URL mudar e conter as coordenadas (o Maps faz um redirect pro place)
        # Timeout curto porque se a busca for ruim, a URL não vai mudar para um place exato
        try:
            await page.wait_for_url(r".*/@.*", timeout=8000)
            await asyncio.sleep(1.5) # Dá um tempinho extra para a URL consolidar
            return _extrair_coords_da_url(page.url)
        except Exception:
            # Se não fez redirect pra um place com coordenadas (por exemplo, mostrou vários resultados de busca)
            # Tenta verificar se a URL atual pelo menos tem centro do mapa válido para a busca
            coords = _extrair_coords_da_url(page.url)
            # Mas cuidado: as vezes o Maps só centraliza na cidade se for muito vago
            if coords:
                # Opcional: Se a busca falhou em achar 1 place exato e só listou vários, ele centraliza
                # a visão em um ponto genérico (a cidade ou o bairro). Podemos aceitar como 'APPROXIMATE'.
                return coords
            return None
    except Exception as e:
        print(f"    ⚠️  Erro na automação do Maps para '{query}': {e}")
        return None


async def geocodificar_imovel_maps_scraper(
    page: Page,
    rua: str,
    bairro: str,
    cidade: str,
    estado: str,
    numero: str = '',
    cep: str = '',
    nome_condominio: str = ''
) -> tuple[tuple[float, float] | None, str, str]:
    """
    Geocodifica usando o Playwright para fazer scraping no Google Maps.
    Tenta da query mais específica para a mais genérica.
    Retorna (coordenadas, estrategia, precisao) ou (None, '', '').
    """
    rua_limpa = remover_sufixo_ibge(rua)
    tentativas = []

    # T1: Estruturado Total (Limpo)
    if rua_limpa:
        query_t1 = f"{rua_limpa}"
        if numero: query_t1 += f", {numero}"
        if bairro: query_t1 += f", {bairro}"
        query_t1 += f", {cidade}, {estado}, Brasil"
        tentativas.append((query_t1, f"{STRATEGY_NAME} (total limpo)"))

    # T2: Precisão Postal (CEP)
    if cep:
        query_postal = f"{numero}, {cep}, {cidade}, Brasil" if numero else f"{cep}, {cidade}, Brasil"
        tentativas.append((query_postal, f"{STRATEGY_NAME} (CEP + número)" if numero else f"{STRATEGY_NAME} (CEP)"))

    # T3: Local Conhecido (Condomínio)
    if nome_condominio:
        tentativas.append((f"{nome_condominio}, {cidade}, {estado}, Brasil", f"{STRATEGY_NAME} (condomínio)"))

    # T4: Rua + Cidade
    if rua_limpa:
        tentativas.append((f"{rua_limpa}, {cidade}, Brasil", f"{STRATEGY_NAME} (rua + cidade)"))

    # Fallbacks de emergência
    if not tentativas:
        if bairro:
            tentativas.append((f"{bairro}, {cidade}, {estado}, Brasil", f"{STRATEGY_NAME} (bairro)"))
        tentativas.append((f"{cidade}, {estado}, Brasil", f"{STRATEGY_NAME} (cidade)"))

    for query, label in tentativas:
        print(f"    🔍 {label}: {query[:80]}")
        
        coords = await _tentar_busca(page, query)
        
        if coords:
            # Como é scraper, não temos o nível de precisão exato do payload do Google.
            # Mas podemos assumir que se caiu no Fallback de bairro/cidade, é 'APPROXIMATE'.
            precisao = 'ROOFTOP' if 'total' in label or 'CEP' in label or 'condomínio' in label else 'APPROXIMATE'
            print(f"    📍 Encontrado: {coords} - Precisão: {precisao}")
            return coords, label, precisao
        
        # Delay anti-bot
        await asyncio.sleep(random.uniform(2.0, 4.0))

    return None, '', ''


# Função para testes avulsos
async def run_test():
    async with async_playwright() as p:
        context = await _configurar_contexto(p)
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        print("Teste de Geocodificação Scraper (Jardim Aquarius)")
        coords, est, prec = await geocodificar_imovel_maps_scraper(
            page,
            rua="Avenida Cassiano Ricardo",
            bairro="Jardim Aquarius",
            cidade="São José dos Campos",
            estado="SP",
            numero="319"
        )
        print(f"Resultado final: {coords} | {est} | {prec}")
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

# --- ADICIONADO PARA PROCESSAMENTO EM LOTE ---
async def main():
    print("🚀 Iniciando Geocodificador via Maps Scraper (Playwright)...")
    geocode_signals.IS_RUNNING = True
    geocode_signals.STOP_SIGNAL = False
    
    try:
        res_col = supabase.table('kanban_colunas').select('id').eq('nome', 'Caixa de Entrada').execute()
        col_id = res_col.data[0]['id'] if res_col.data else None
        
        query = supabase.table('imoveis').select("id, titulo, rua, bairro, cidade, estado, numero").is_("latitude", "null").eq("ativo", True)
        if col_id:
            query = query.eq("kanban_coluna_id", col_id)
            
        response = query.limit(20).execute()
        imoveis = response.data
        
        if not imoveis:
            print("✅ Nenhum imóvel sem geocodificação! Todos já possuem coordenadas.")
            return

        print(f"📍 {len(imoveis)} imóveis sem coordenadas neste lote. Processando...\n")
        
        async with async_playwright() as p:
            context = await _configurar_contexto(p)
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)
            await _aceitar_cookies(page)

            for imovel in imoveis:
                if geocode_signals.STOP_SIGNAL:
                    print("🛑 Parada solicitada via sinal! Interrompendo geocoder...")
                    break
                    
                id_ = imovel['id']
                print(f"[{id_}] Buscando no Maps: {imovel.get('rua')} | {imovel.get('bairro')} | {imovel.get('cidade')}")
                
                coords, est, prec = await geocodificar_imovel_maps_scraper(
                    page,
                    rua=imovel.get('rua') or '',
                    bairro=imovel.get('bairro') or '',
                    cidade=imovel.get('cidade') or '',
                    estado=imovel.get('estado') or 'SP',
                    numero=imovel.get('numero') or ''
                )
                
                if coords:
                    lat, lng = coords
                    print(f"  ✅ ({lat:.5f}, {lng:.5f}) salvo no banco!\n")
                    supabase.table('imoveis').update({'latitude': lat, 'longitude': lng, 'geocode_strategy': est}).eq('id', id_).execute()
                else:
                    print(f"  ❌ Nenhuma coordenada encontrada no Maps.\n")
            
            await context.close()
    finally:
        geocode_signals.IS_RUNNING = False
        geocode_signals.STOP_SIGNAL = False
