"""
buscar_link_imovel.py
─────────────────────
Busca a URL pública do imóvel no site baxinvestimentos.com.br
pela referência.

Estratégia:
  1. Tenta via URL de busca direta (?reference=REF) — mais rápido e sem depender
     de interações com o DOM do header.
  2. Fallback: Playwright simulando a busca no campo do header.

Cache em memória durante a sessão de disparo.
"""

import asyncio
import logging
import re
import urllib.parse
import urllib.request

from playwright.async_api import async_playwright

log = logging.getLogger(__name__)

# Cache de links já buscados: { referencia: url }
_cache: dict[str, str] = {}

SITE_BASE   = "https://baxinvestimentos.com.br/"
SEARCH_URL  = "https://baxinvestimentos.com.br/busca/?reference={ref}"

# Seletores CSS robustos (sem índices numéricos hardcoded)
SEL_OPEN_SEARCH = "a.button--reference"          # botão que abre o campo de busca por referência
SEL_INPUT       = "input[name='reference']"      # input de texto correto
SEL_BUTTON      = "button[type='submit']"        # botão de submit da busca
SEL_MSG_ERRO    = "span.sc-1mmbb1k-0"            # span de erro do formulário (Imóvel não encontrado)


async def _buscar_via_url_direta(referencia: str) -> str | None:
    """
    Tenta construir a URL de busca diretamente e verificar se redireciona
    para a página do imóvel — sem abrir browser.
    Mais rápido que o Playwright para a maioria dos casos.
    """
    try:
        ref_enc = urllib.parse.quote(referencia)
        url = SEARCH_URL.format(ref=ref_enc)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            final_url = resp.url
            if "/imovel/" in final_url.lower():
                log.info(f"[LinkImóvel] (URL direta) {referencia} → {final_url}")
                return final_url
            log.debug(f"[LinkImóvel] URL direta não redirecionou para /imovel/: {final_url}")
    except Exception as e:
        log.debug(f"[LinkImóvel] Fallback URL direta falhou: {e}")
    return None


async def _buscar_via_playwright(referencia: str) -> str | None:
    """
    Abre o site com Playwright, interage com o campo de busca por referência
    e retorna a URL resultante. Usa seletores CSS robustos.
    """
    for tentativa in range(1, 3):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1280, "height": 800})

                await page.goto(SITE_BASE, timeout=30_000, wait_until="domcontentloaded")
                # Aguarda a hidratação do React/Next.js
                await page.wait_for_timeout(3000)

                # 1. Clica no ícone para abrir o campo de busca por referência
                open_btn = page.locator(SEL_OPEN_SEARCH).first
                await open_btn.wait_for(state="visible", timeout=15_000)
                await open_btn.click(force=True)
                await page.wait_for_timeout(1000)

                # 2. Digita a referência no input
                input_el = page.locator(SEL_INPUT).first
                await input_el.wait_for(state="visible", timeout=10_000)
                await input_el.fill(referencia)
                await page.wait_for_timeout(800)

                # 3. Verifica mensagem de "não encontrado" antes de clicar
                span_erro = page.locator(SEL_MSG_ERRO).first
                if await span_erro.is_visible():
                    texto = (await span_erro.inner_text()).lower()
                    if "não encontrado" in texto or "nao encontrado" in texto:
                        log.warning(f"[LinkImóvel] Site indicou '{texto}' para {referencia}")
                        await browser.close()
                        return "NOT_FOUND"

                # 4. Clica no botão de buscar (ou pressiona Enter como fallback)
                try:
                    search_btn = page.locator(SEL_BUTTON).first
                    await search_btn.click(timeout=5000)
                except Exception:
                    await input_el.press("Enter")

                # 5. Aguarda navegação
                try:
                    await page.wait_for_url(re.compile(r"/imovel/"), timeout=8000)
                except Exception:
                    await page.wait_for_timeout(4000)

                url = page.url
                await browser.close()

                if "/imovel/" not in url.lower():
                    log.warning(f"[LinkImóvel] Não redirecionou para imóvel (URL: {url})")
                    return None

                log.info(f"[LinkImóvel] (Playwright) {referencia} → {url}")
                return url

        except Exception as e:
            log.warning(f"[LinkImóvel] Tentativa {tentativa}/2 falhou para {referencia}: {e}")

    log.error(f"[LinkImóvel] Não foi possível obter link para {referencia} após 2 tentativas.")
    return None


async def _buscar_async(referencia: str) -> str | None:
    # Estratégia 1: URL direta (rápida, sem browser)
    url = await _buscar_via_url_direta(referencia)
    if url:
        return url

    # Estratégia 2: Playwright (fallback completo)
    return await _buscar_via_playwright(referencia)


def buscar_link_imovel(referencia: str) -> str | None:
    """
    Versão síncrona com cache automático.
    A mesma referência não é buscada duas vezes na mesma sessão.
    """
    ref = referencia.strip().upper()
    if ref in _cache:
        log.info(f"[LinkImóvel] Cache hit para {ref}: {_cache[ref]}")
        return _cache[ref]

    url = asyncio.run(_buscar_async(ref))
    if url:
        _cache[ref] = url
    return url


# ── Teste rápido ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import time

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    refs = sys.argv[1:] if len(sys.argv) > 1 else ["SAMAP26", "REF-INEXISTENTE-9999"]
    for ref in refs:
        print(f"\n{'─'*50}")
        print(f"Buscando: {ref}")
        t0 = time.time()
        link = buscar_link_imovel(ref)
        elapsed = time.time() - t0
        print(f"URL:      {link}")
        print(f"Tempo:    {elapsed:.1f}s")
