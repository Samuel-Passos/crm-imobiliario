"""
fase1_coleta_links.py
---------------------
Fase 1 do scraper OLX: navega pelas páginas de listagem de imóveis de
São José dos Campos e salva os links na tabela `links_anuncios` do Supabase.

ESTRATÉGIA DE EXTRAÇÃO:
  - Usa page.evaluate('window.dataLayer') para extrair impressions via JS
  - Fallback: regex nos hrefs do HTML se o dataLayer não tiver impressions
  
Fluxo:
  1. Abre URL de listagem com Playwright
  2. Aguarda carregamento da página
  3. Extrai links via window.dataLayer (JS) + fallback regex no HTML
  4. Salva em `links_anuncios` com status='pendente' (insere apenas novos)
  5. Navega para próxima página (?o=N)
  6. Para quando: não há links novos em 3 páginas seguidas OU atingiu MAX_PAGINAS

Uso:
  python fase1_coleta_links.py
  python fase1_coleta_links.py --max-paginas 5
"""
import asyncio
import os
import random
import argparse
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import Stealth

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from supabase_client import supabase
from parser_olx import extrair_links_do_datalayer, extrair_links_do_html, tem_proxima_pagina

# ── Configurações ──────────────────────────────────────────────────────────────
URL_BASE = "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?f=p"
CHROME_PROFILE = os.getenv("CHROME_PROFILE_PATH", "/home/samuel/.config/google-chrome")
MAX_PAGINAS = int(os.getenv("MAX_PAGINAS", "100"))
DELAY_MIN = float(os.getenv("DELAY_MIN_SEGUNDOS", "3"))
DELAY_MAX = float(os.getenv("DELAY_MAX_SEGUNDOS", "6"))

# Usa o Chromium do sistema (mesmo que o scraper existente usa)
CHROMIUM_PATH = "/usr/bin/chromium"

# Caminho para o arquivo de sessão (cookies reais do Chrome — bypass Cloudflare)
SCRAPER_DIR = os.path.join(os.path.dirname(__file__), "..", "scraper")
SESSION_FILE = os.path.normpath(os.path.join(SCRAPER_DIR, "olx_session.json"))

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


def _url_pagina(pagina: int, base_url: str = URL_BASE) -> str:
    """Monta URL da página N da listagem OLX."""
    # Se a URL já tiver query params (ex: ?q=...), usamos '&o=' ao invés de '?o='
    if pagina <= 1:
        return base_url
    separador = "&" if "?" in base_url else "?"
    return f"{base_url}{separador}o={pagina}"


def _salvar_links_supabase(links: list[dict]) -> tuple[int, int]:
    """
    Salva links em `links_anuncios`.
    Insere apenas links novos (verifica existência por URL antes de inserir).
    Retorna (novos_inseridos, ja_existiam).
    """
    if not links:
        return 0, 0

    novos = 0
    existiam = 0

    for link in links:
        url = link["url"]
        list_id = link.get("list_id")

        res = supabase.table("links_anuncios").select("id").eq("url", url).execute()

        if res.data:
            existiam += 1
        else:
            payload = {"url": url, "status": "pendente"}
            if list_id:
                payload["list_id"] = int(list_id)

            try:
                supabase.table("links_anuncios").insert(payload).execute()
                novos += 1
            except Exception as e:
                print(f"  ⚠️ Erro ao inserir {url}: {e}")

    return novos, existiam


async def _configurar_browser(p):
    """Cria browser com Chromium do sistema."""
    browser = await p.chromium.launch(
        executable_path=CHROMIUM_PATH,
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )
    return browser


async def _configurar_pagina(browser: Browser) -> Page:
    """Cria contexto com fingerprint aleatório, cookies reais e playwright-stealth."""
    user_agent = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)
    
    context_kwargs = {
        "user_agent": user_agent,
        "viewport": viewport,
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
    }
    
    # Fase 1: Rodamos de forma anônima, sem usar o login
    print(f"  🕵️ Rodando modo anônimo (sem login)")
    
    context = await browser.new_context(**context_kwargs)
    page = await context.new_page()
    
    # Aplica playwright-stealth (oculta assinaturas de automação)
    await Stealth().apply_stealth_async(page)
    
    return page


async def _extrair_links_da_pagina(page: Page) -> list[dict]:
    """
    Extrai links de anúncios de uma página de listagem.
    
    Estratégia 1: window.dataLayer via JS (mais completo)
    Estratégia 2: regex nos hrefs do HTML (fallback)
    """
    links = []

    # Estratégia 1: dataLayer via JS — extração seletiva para evitar circular reference
    try:
        dl_json = await page.evaluate("""() => {
            try {
                const dl = window.dataLayer || [];
                const safe = dl.map(entry => {
                    const copy = {};
                    ['page', 'ecommerce', 'event'].forEach(key => {
                        if (entry[key] !== undefined) {
                            try {
                                const test = JSON.stringify(entry[key]);
                                copy[key] = JSON.parse(test);
                            } catch(e) {}
                        }
                    });
                    return copy;
                });
                return JSON.stringify(safe);
            } catch(e) {
                return '[]';
            }
        }""")
        datalayer = json.loads(dl_json)
        links = extrair_links_do_datalayer(datalayer)
        if links:
            print(f"  📊 {len(links)} links via dataLayer")
            return links
    except Exception as e:
        print(f"  ⚠️ dataLayer JS falhou: {e}")

    # Estratégia 2: regex no HTML
    try:
        html = await page.content()
        links = extrair_links_do_html(html)
        if links:
            print(f"  📊 {len(links)} links via regex HTML")
    except Exception as e:
        print(f"  ⚠️ Regex HTML falhou: {e}")

    return links


async def coletar_links(max_paginas: int = 50, url_base: str = None) -> dict:
    """
    Navega pelas páginas da OLX, extrai os links dos anúncios e salva no Supabase.
    Retorna estatísticas da execução.
    """
    total_novos = 0
    total_existiam = 0
    paginas_sem_novos = 0
    MAX_PAGINAS_SEM_NOVOS = 3
    num_pagina = 0
    url_alvo = url_base if url_base else URL_BASE

    print("=" * 60)
    print("🚀 FASE 1 — COLETA DE LINKS OLX")
    print(f"   URL: {url_alvo}")
    print(f"   Máx. páginas: {max_paginas}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await _configurar_browser(p)
        page = await _configurar_pagina(browser)

        for num_pagina in range(1, max_paginas + 1):
            url_atual = _url_pagina(num_pagina, base_url=url_alvo)
            print(f"\n📄 Página {num_pagina}: {url_atual}")

            try:
                response = await page.goto(
                    url_atual,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                if response and response.status in (404, 410):
                    print(f"  ⛔ HTTP {response.status} — Fim da paginação.")
                    break

                # Aguarda os cards de anúncios carregarem
                try:
                    await page.wait_for_function(
                        """() => {
                            const dl = window.dataLayer || [];
                            return dl.some(e => e.ecommerce && e.ecommerce.impressions);
                        }""",
                        timeout=12000
                    )
                except Exception:
                    # Sem impressions — pode ser listagem vazia ou sem dataLayer
                    await asyncio.sleep(3)

                # Verifica bloqueio
                title = await page.title()
                if "just a moment" in title.lower():
                    print(f"  🚫 Cloudflare detectado — aguardando 30s")
                    await asyncio.sleep(30)
                    paginas_sem_novos += 1
                    continue

                # Extrai links
                links = await _extrair_links_da_pagina(page)
                print(f"  🔗 Links encontrados: {len(links)}")

                if len(links) == 0:
                    print(f"  ⚠️ Nenhum link encontrado nesta página")
                    paginas_sem_novos += 1
                    if paginas_sem_novos >= MAX_PAGINAS_SEM_NOVOS:
                        print(f"  ⛔ {MAX_PAGINAS_SEM_NOVOS} páginas sem links — encerrando")
                        break
                    continue

                # Salva no Supabase
                novos, existiam = _salvar_links_supabase(links)
                total_novos += novos
                total_existiam += existiam

                print(f"  ✅ Salvos: {novos} novos | {existiam} já existiam")

                if novos == 0:
                    paginas_sem_novos += 1
                    print(f"  📊 Páginas sem novos: {paginas_sem_novos}/{MAX_PAGINAS_SEM_NOVOS}")
                    if paginas_sem_novos >= MAX_PAGINAS_SEM_NOVOS:
                        print(f"  ⛔ Todos os links já estão no banco — encerrando")
                        break
                else:
                    paginas_sem_novos = 0

                # Verifica próxima página via HTML
                html = await page.content()
                if not tem_proxima_pagina(html) and num_pagina > 1:
                    print(f"  ✅ Última página detectada pelo HTML")
                    break

                # Delay humano entre páginas
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                print(f"  ⏳ Aguardando {delay:.1f}s antes da próxima página...")
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"  ❌ Erro na página {num_pagina}: {e}")
                await asyncio.sleep(5)
                continue

        await browser.close()

    print("\n" + "=" * 60)
    print("📊 FASE 1 CONCLUÍDA")
    print(f"   Links novos inseridos: {total_novos}")
    print(f"   Links já existentes:   {total_existiam}")
    print("=" * 60)

    return {
        "total_novos": total_novos,
        "total_existiam": total_existiam,
        "paginas_visitadas": num_pagina,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fase 1 — Coleta de links OLX")
    parser.add_argument("--url", type=str, default=URL_BASE, help="URL base para extração")
    parser.add_argument("--max-paginas", type=int, default=MAX_PAGINAS, help="Máximo de páginas a percorrer")
    args = parser.parse_args()

    resultado = asyncio.run(coletar_links(max_paginas=args.max_paginas, url_base=args.url))
    print(f"\nResultado: {resultado}")
