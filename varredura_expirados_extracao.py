import asyncio
import os
import random
import argparse
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import Stealth

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'olx_captacao'))
try:
    from supabase_client import supabase
except ImportError:
    from supabase import create_client, Client
    dotenv_path = os.path.join(os.path.dirname(__file__), "scraper", ".env")
    if not os.path.exists(dotenv_path):
        dotenv_path = os.path.join(os.path.dirname(__file__), "olx_captacao", ".env")
    load_dotenv(dotenv_path)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(supabase_url, supabase_key)


# -- Configurações --
DELAY_MIN = 2.0
DELAY_MAX = 5.0
CHROMIUM_PATH = "/usr/bin/chromium"

KANBAN_IDS = {
    "EXTRACAO_TELEFONE": "9cfb9d98-89cb-4169-88e1-db399f3ce877",
    "EXPIRADOS": "5f01efe9-6531-4259-9927-76c130e2851d",
}

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

async def _configurar_browser(p) -> Browser:
    return await p.chromium.launch(
        executable_path=CHROMIUM_PATH,
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]
    )

async def _configurar_pagina(browser: Browser) -> Page:
    user_agent = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)
    
    context = await browser.new_context(
        user_agent=user_agent,
        viewport=viewport,
        locale="pt-BR",
        timezone_id="America/Sao_Paulo",
    )
    page = await context.new_page()
    await Stealth().apply_stealth_async(page)
    return page

async def _detectar_bloqueio_ou_expirado(page: Page) -> str | None:
    try:
        title = await page.title()
        title_lower = title.lower()
        
        if "just a moment" in title_lower or "attention required" in title_lower or "cloudflare" in title_lower:
            return "bloqueio"
            
        if "não encontrado" in title_lower or "not found" in title_lower:
            return "expirado"
            
        html = await page.content()
        if "anúncio não encontrado" in html.lower()[:5000]:
            return "expirado"
        if "cf-error-details" in html or "cloudflare" in html[:2000].lower():
            return "bloqueio"
    except Exception:
        pass
    return None

async def verificar_anuncio(page: Page, url: str) -> str:
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=35000)
        
        if response and response.status in (404, 410):
            return "expirado"
            
        status = await _detectar_bloqueio_ou_expirado(page)
        if status:
            return status
            
        return "ok"
    except Exception as e:
        print(f"  ❌ Erro ao acessar {url}: {e}")
        return "erro"

def formatar_tempo(segundos):
    m, s = divmod(int(segundos), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    else:
        return f"{s}s"

async def varrer_expirados(lote: int):
    print("="*60)
    print("🧹 INICIANDO VARREDURA DE ANÚNCIOS EXPIRADOS")
    print(f"   Kanban: Extração de Telefone")
    print(f"   Limite: {lote} anúncios")
    print("="*60)

    res = supabase.table("imoveis").select("id, titulo, url").eq("kanban_coluna_id", KANBAN_IDS["EXTRACAO_TELEFONE"]).limit(lote).execute()
    imoveis = res.data
    
    if not imoveis:
        print("📭 Nenhum anúncio encontrado neste kanban.")
        return

    total = len(imoveis)
    print(f"📋 Total de anúncios a verificar: {total}")
    print("Iniciando verificação...\n")

    async with async_playwright() as p:
        browser = await _configurar_browser(p)
        page = await _configurar_pagina(browser)
        
        movidos = 0
        erros = 0
        ok = 0
        bloqueios = 0
        
        inicio_processo = time.time()
        
        for i, imovel in enumerate(imoveis, 1):
            inicio_link = time.time()
            url = imovel.get("url")
            titulo = imovel.get("titulo") or f"ID {imovel.get('id')}"
            
            faltam = total - i
            
            print(f"[{i}/{total}] (Faltam {faltam}) 🔍 {titulo}")
            
            if not url:
                print(f"  ⚠️ Sem URL. Ignorando.")
                erros += 1
                continue
                
            status = await verificar_anuncio(page, url)
            
            if status == "expirado":
                print("  ⚠️ Expirado! Movendo...")
                try:
                    supabase.table("imoveis").update({
                        "anuncio_expirado": True,
                        "kanban_coluna_id": KANBAN_IDS["EXPIRADOS"],
                        
                    }).eq("id", imovel["id"]).execute()
                    movidos += 1
                except Exception as e:
                    print(f"  ❌ Erro ao mover: {e}")
                    erros += 1
            elif status == "ok":
                print("  ✅ Ativo.")
                ok += 1
            elif status == "bloqueio":
                print("  🚫 Bloqueio Anti-bot.")
                bloqueios += 1
            else:
                print(f"  ❌ Erro.")
                erros += 1

            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            tempo_decorrido_link = time.time() - inicio_link
            
            # Estimativa
            tempo_total_link = tempo_decorrido_link + delay
            tempo_medio = (time.time() - inicio_processo) / i
            eta_segundos = tempo_medio * faltam
            
            print(f"  ⏱️  Tempo no link: {tempo_decorrido_link:.1f}s | Delay: {delay:.1f}s | ETA: {formatar_tempo(eta_segundos)}")
            await asyncio.sleep(delay)
            print("-" * 50)
            
        await browser.close()
        
    print("\n" + "="*60)
    print("📊 VARREDURA CONCLUÍDA")
    print(f"   Ativos (OK):    {ok}")
    print(f"   Expirados:      {movidos}")
    print(f"   Erros:          {erros}")
    print(f"   Bloqueios:      {bloqueios}")
    print(f"   Tempo Total:    {formatar_tempo(time.time() - inicio_processo)}")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Varredura de expirados no kanban de extração de telefone.")
    parser.add_argument("--lote", type=int, default=50, help="Quantidade máxima de anúncios a verificar (default: 50)")
    args = parser.parse_args()
    
    asyncio.run(varrer_expirados(lote=args.lote))
