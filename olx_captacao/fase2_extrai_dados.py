"""
fase2_extrai_dados.py
---------------------
Fase 2 do scraper OLX: busca links pendentes da tabela `links_anuncios`,
entra em cada anúncio e extrai dados para a tabela `imoveis`.

ESTRATÉGIA DE EXTRAÇÃO:
  - Usa page.evaluate() para acessar window.dataLayer diretamente no contexto JS
  - Isso é mais confiável que parsear o HTML, pois o dataLayer sempre é populado
    via JS mesmo quando o HTML renderizado não o mostra como texto estático
  - Complementa com schema.org JSON-LD para fotos e descrição

Uso:
  python fase2_extrai_dados.py
  python fase2_extrai_dados.py --lote 20
  python fase2_extrai_dados.py --url "https://sp.olx.com.br/..."  # modo teste
"""
import asyncio
import os
import random
import sys
import argparse
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser
from playwright_stealth import Stealth

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from supabase_client import supabase
from parser_olx import (
    extrair_dados_do_datalayer,
    complementar_com_schema,
    _extrair_list_id_da_url,
)

# ── Configurações ──────────────────────────────────────────────────────────────
CHROME_PROFILE = os.getenv("CHROME_PROFILE_PATH", "/home/samuel/.config/google-chrome")
DELAY_MIN = float(os.getenv("DELAY_MIN_SEGUNDOS", "2"))
DELAY_MAX = float(os.getenv("DELAY_MAX_SEGUNDOS", "5"))
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scraper"))
try:
    from config_db import get_config
    _cfg = get_config()
    LOTE_PADRAO = _cfg.get("lote_fase2")
except ImportError:
    LOTE_PADRAO = 50
MAX_FALHAS_CONSECUTIVAS = 5

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


def _buscar_links_pendentes(limite: int) -> list[dict]:
    """
    Busca links com status='pendente' da tabela `links_anuncios`.
    Ordena por created_at DESC — processa os mais recentes (mais provável de estar ativos) primeiro.
    """
    res = (
        supabase.table("links_anuncios")
        .select("id, url, list_id")
        .eq("status", "pendente")
        .order("created_at", desc=True)
        .limit(limite)
        .execute()
    )
    return res.data or []


def _upsert_imovel(dados: dict) -> bool:
    """Salva dados do imóvel via upsert por list_id."""
    if not dados or not dados.get("list_id"):
        return False
    try:
        supabase.table("imoveis").upsert(dados, on_conflict="list_id").execute()
        return True
    except Exception as e:
        print(f"  ❌ Erro ao salvar no Supabase: {e}")
        return False


def _atualizar_status_link(link_id: int, status: str):
    """Atualiza o status de um link em `links_anuncios`."""
    try:
        supabase.table("links_anuncios").update({
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", link_id).execute()
    except Exception as e:
        print(f"  ⚠️ Erro ao atualizar link {link_id}: {e}")


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
    
    # Carrega cookies reais do Chrome (bypass Cloudflare)
    context_kwargs = {
        "user_agent": user_agent,
        "viewport": viewport,
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
    }
    
    # Fase 2: Rodamos de forma anônima, sem usar o login
    print(f"  🕵️ Rodando modo anônimo (sem login)")
    
    context = await browser.new_context(**context_kwargs)
    
    page = await context.new_page()
    
    # Aplica playwright-stealth (oculta assinaturas de automação)
    await Stealth().apply_stealth_async(page)
    
    return page


async def _detectar_bloqueio_ou_expirado(page: Page) -> str | None:
    """
    Verifica se a página atual é um bloqueio Cloudflare ou anúncio expirado.
    Retorna 'bloqueio', 'expirado', ou None (página normal).
    """
    try:
        title = await page.title()
        title_lower = title.lower()
        
        # Cloudflare
        if "just a moment" in title_lower or "attention required" in title_lower or "cloudflare" in title_lower:
            return "bloqueio"
        
        # Anúncio não encontrado
        if "não encontrado" in title_lower or "not found" in title_lower:
            return "expirado"
        
        # Verifica no HTML também (para casos onde o title é genérico)
        html = await page.content()
        if "anúncio não encontrado" in html.lower()[:5000]:
            return "expirado"
        if "cf-error-details" in html or "cloudflare" in html[:2000].lower():
            return "bloqueio"
            
    except Exception:
        pass
    return None


async def _extrair_dados_da_pagina(page: Page, url: str, tentativa: int = 1) -> tuple[dict | None, str]:
    """
    Navega até URL e extrai dados usando window.dataLayer via JS.
    
    Retorna (dados_dict, status) onde status é:
      'ok'       → dados extraídos com sucesso
      'expirado' → anúncio não encontrado (404 ou title de erro)
      'bloqueio' → Cloudflare (link permanece pendente para retry)
      'erro'     → falha de rede ou parse
    """
    try:
        response = await page.goto(url, wait_until="domcontentloaded", timeout=35000)

        # 404 = não encontrado, 410 = removido permanentemente (OLX usa 410 para anúncios expirados)
        if response and response.status in (404, 410):
            return None, "expirado"

        # ── Verifica bloqueio/expirado ANTES de qualquer processamento ──
        status_inicial = await _detectar_bloqueio_ou_expirado(page)
        if status_inicial == "bloqueio":
            print(f"  🚫 Cloudflare detectado (tentativa {tentativa}/2)")
            if tentativa == 1:
                # Retry automático após 45s de espera
                print(f"  ⏳ Aguardando 45s antes de retry...")
                await asyncio.sleep(45)
                return await _extrair_dados_da_pagina(page, url, tentativa=2)
            return None, "bloqueio"
        
        if status_inicial == "expirado":
            return None, "expirado"

        # Aguarda o dataLayer ser populado pelo JS da OLX
        try:
            await page.wait_for_function(
                """() => {
                    const dl = window.dataLayer || [];
                    return dl.some(e => e.page && e.page.adDetail);
                }""",
                timeout=12000
            )
        except Exception:
            pass  # Continua mesmo sem confirmar — pode ser tipo de página diferente

        # Delay humano
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # ── Estratégia 1: window.dataLayer via JS (PRINCIPAL) ──
        # Extração seletiva: copia apenas page/ecommerce/event para evitar circular reference React/DOM
        try:
            dl_json = await page.evaluate("""() => {
                try {
                    const dl = window.dataLayer || [];
                    const safe = dl.map(entry => {
                        const copy = {};
                        ['page', 'ecommerce', 'event', 'gtm.start', 'gtm.uniqueEventId'].forEach(key => {
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
        except Exception as e:
            print(f"  ⚠️ Erro ao avaliar dataLayer: {e}")
            datalayer = []

        # Segunda verificação de bloqueio (pode aparecer depois do JS carregar)
        status_pos = await _detectar_bloqueio_ou_expirado(page)
        if status_pos == "bloqueio":
            print(f"  🚫 Cloudflare detectado após carregamento (tentativa {tentativa}/2)")
            if tentativa == 1:
                print(f"  ⏳ Aguardando 45s antes de retry...")
                await asyncio.sleep(45)
                return await _extrair_dados_da_pagina(page, url, tentativa=2)
            return None, "bloqueio"
        if status_pos == "expirado":
            return None, "expirado"


        # Extrai dados do dataLayer
        dados = extrair_dados_do_datalayer(datalayer, url)

        if not dados:
            # ── Estratégia 2: HTML + schema.org como último recurso ──
            html = await page.content()
            if "anúncio não encontrado" in html.lower():
                return None, "expirado"
            # Mesmo sem dataLayer estruturado, tenta extrair o mínimo do HTML
            list_id = _extrair_list_id_da_url(url)
            if list_id:
                dados = {
                    "list_id": int(list_id),
                    "ad_id": int(list_id),
                    "url": url,
                    "origem": "OLX",
                    "titulo": title or "Sem título",
                    "ativo": True,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "telefone_pesquisado": False,
                    "anuncio_expirado": False,
                }
                dados = complementar_com_schema(dados, html)
            else:
                return None, "erro"

        # Complementa com schema.org (fotos, descrição, CEP)
        html = await page.content()
        dados = complementar_com_schema(dados, html)

        return dados, "ok"

    except Exception as e:
        print(f"  ❌ Erro ao acessar {url}: {e}")
        return None, "erro"


async def processar_url_unica(url: str) -> dict:
    """
    Processa uma única URL em modo de teste (sem salvar no banco).
    Retorna os dados extraídos ou {} se falhar.
    """
    print(f"\n🔍 Processando URL de teste: {url}")

    async with async_playwright() as p:
        browser = await _configurar_browser(p)
        page = await _configurar_pagina(browser)

        dados, status = await _extrair_dados_da_pagina(page, url)
        await browser.close()

    if status == "expirado":
        print("  ⚠️ Anúncio expirado/não encontrado")
        return {}

    if dados:
        campos = list(dados.keys())
        print(f"  ✅ Dados extraídos: {campos}")
        print(f"  📋 Título: {dados.get('titulo')}")
        print(f"  💰 Preço: {dados.get('preco_str')}")
        print(f"  📍 Bairro: {dados.get('bairro')}, {dados.get('cidade')}")
    else:
        print(f"  ❌ Não foi possível extrair dados (status: {status})")

    return dados or {}


async def processar_e_salvar_unico(url: str) -> bool:
    """
    Processa uma única URL e SALVA no banco. Utilizado pela nova API de frontend.
    Retorna True se sucesso, False se falha.
    """
    print(f"\n🔍 Extraindo e salvando URL única: {url}")
    
    from parser_olx import _extrair_list_id_da_url
    list_id = _extrair_list_id_da_url(url)
    
    # 1. Checa IMEDIATAMENTE se o list_id já existe na tabela imoveis
    if list_id:
        res = supabase.table("imoveis").select("id").eq("list_id", list_id).execute()
        if res.data:
            print(f"  ✅ Já existente (Imóveis) — ignorando extração para economizar tempo.")
            print(f"__RESULT__={{\"sucesso\": true, \"acao\": \"Existente\", \"titulo\": \"Imóvel já estava na base\"}}")
            return True
            
    # Se não existe, inicia a extração demorada com o Playwright
    async with async_playwright() as p:
        browser = await _configurar_browser(p)
        page = await _configurar_pagina(browser)
        dados, status = await _extrair_dados_da_pagina(page, url)
        await browser.close()
        
    if status == "expirado":
        print("  ⚠️ Anúncio expirado/não encontrado")
        return False
        
    if status == "ok" and dados:
        dados["url"] = url
        if list_id:
            dados["list_id"] = list_id
                
        if _upsert_imovel(dados):
            print(f"  ✅ Salvo — {dados.get('titulo', 'sem título')[:60]}")
            print(f"     💰 {dados.get('preco_str', 'sem preço')} | 📍 {dados.get('bairro', '?')} — 🏙️ {dados.get('cidade', '?')}")
            
            # Insere/atualiza também na tabela links_anuncios como 'processado'
            if list_id:
                try:
                    supabase.table("links_anuncios").upsert({
                        "url": url,
                        "list_id": list_id,
                        "status": "processado"
                    }, on_conflict="url").execute()
                except Exception as e:
                    pass

            print(f"__RESULT__={{\"sucesso\": true, \"acao\": \"Salvo\", \"titulo\": \"{dados.get('titulo', '')}\"}}")
            return True
            
    print(f"  ❌ Falha ao salvar ou extrair dados (status: {status})")
    print(f"__RESULT__={{\"sucesso\": false, \"status\": \"{status}\"}}")
    return False


async def extrair_dados(lote: int = LOTE_PADRAO) -> dict:
    """
    Função principal da Fase 2.
    Processa links pendentes do Supabase em lote.
    """
    print("=" * 60)
    print("🚀 FASE 2 — EXTRAÇÃO DE DADOS OLX")
    print(f"   Lote: {lote} links")
    print("=" * 60)

    # Processa o lote estabelecido para este ciclo
    lote_efetivo = lote

    links = _buscar_links_pendentes(lote_efetivo)
    total = len(links)

    if total == 0:
        print("\n✅ Nenhum link pendente para processar.")
        return {"processados": 0, "salvos": 0, "erros": 0, "expirados": 0}

    print(f"\n📋 {total} links pendentes encontrados\n")

    salvos = 0
    erros = 0
    expirados = 0
    falhas_consecutivas = 0

    async with async_playwright() as p:
        browser = await _configurar_browser(p)
        page = await _configurar_pagina(browser)

        for i, link in enumerate(links, 1):
            link_id = link["id"]
            url = link["url"]

            print(f"\n[{i}/{total}] 📄 {url}")

            if falhas_consecutivas >= MAX_FALHAS_CONSECUTIVAS:
                print(f"\n🚨 {MAX_FALHAS_CONSECUTIVAS} falhas consecutivas — pausando.")
                print("   Execute novamente mais tarde.")
                break

            try:
                dados, status = await _extrair_dados_da_pagina(page, url)

                if status == "expirado":
                    print(f"  ⚠️ Anúncio expirado — marcando como expirado")
                    _atualizar_status_link(link_id, "expirado")
                    expirados += 1
                    falhas_consecutivas = 0

                elif status == "bloqueio":
                    print(f"  🚫 Bloqueio — link permanece pendente para retry")
                    falhas_consecutivas += 1
                    # NÃO atualiza status — fica pendente para próxima execução

                elif status == "ok" and dados:
                    dados["url"] = url
                    if link.get("list_id"):
                        dados.setdefault("list_id", link["list_id"])

                    if _upsert_imovel(dados):
                        _atualizar_status_link(link_id, "processado")
                        salvos += 1
                        falhas_consecutivas = 0
                        print(f"  ✅ Salvo — {dados.get('titulo', 'sem título')[:60]}")
                        print(f"     💰 {dados.get('preco_str', 'sem preço')} | 📍 {dados.get('bairro', '?')} — 🏙️ {dados.get('cidade', '?')}")
                    else:
                        _atualizar_status_link(link_id, "erro")
                        erros += 1
                        falhas_consecutivas += 1

                else:
                    print(f"  ❌ Falha ao extrair dados (status: {status})")
                    _atualizar_status_link(link_id, "erro")
                    erros += 1
                    falhas_consecutivas += 1

            except Exception as e:
                print(f"  ❌ Erro inesperado: {e}")
                _atualizar_status_link(link_id, "erro")
                erros += 1
                falhas_consecutivas += 1

            # Delay anti-bot
            delay = random.uniform(DELAY_MIN, DELAY_MAX)
            print(f"  ⏳ Aguardando {delay:.1f}s...")
            await asyncio.sleep(delay)

        await browser.close()

    print("\n" + "=" * 60)
    print("📊 FASE 2 CONCLUÍDA")
    print(f"   Processados: {salvos + erros + expirados}/{total}")
    print(f"   ✅ Salvos em imoveis:  {salvos}")
    print(f"   ⚪ Expirados:         {expirados}")
    print(f"   ❌ Erros:             {erros}")
    print("=" * 60)

    return {
        "processados": salvos + erros + expirados,
        "salvos": salvos,
        "erros": erros,
        "expirados": expirados,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fase 2 — Extração de dados OLX")
    parser.add_argument("--lote", type=int, default=LOTE_PADRAO, help="Links a processar por execução")
    parser.add_argument("--url", type=str, default=None, help="Testa uma URL específica (sem salvar)")
    args = parser.parse_args()

    if args.url:
        resultado = asyncio.run(processar_url_unica(args.url))
        if resultado:
            print("\n📋 Dados extraídos:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
    else:
        resultado = asyncio.run(extrair_dados(lote=args.lote))
        print(f"\nResultado: {resultado}")
