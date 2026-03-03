import asyncio
import re
import json
import os
import random
from typing import Dict, Any
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# ─── XPaths Confirmados (Samuel) ─────────────────────────────────────────────
XPATH_BTN_PRINCIPAL      = '//*[@id="price-box-button-show-phone"]'
XPATHS_TELEFONE_PRINCIPAL = [
    '//*[@id="price-box-container"]/div[2]/div[1]/span',
    '#price-box-container > div.flex.flex-col > div[class*="ad__sc-"] > span', # Seletor flexível baseado no do Samuel
    '#price-box-container span' # Fallback final mais amplo
]
XPATH_BTN_DESCRICAO      = '//*[@id="description-title"]/div/div[2]/div/button'
XPATH_MASCARA_DESCRICAO  = '//*[@id="description-title"]/div/div[2]/div/span/span/span'
XPATH_TEL_DESCRICAO      = '//*[@id="description-title"]/div/div[2]/div/span/span/span'
# ─────────────────────────────────────────────────────────────────────────────

PHONE_REGEX = re.compile(
    r'(?:\+?55\s*)?(?:\(?0?[1-9]{2}\)?[\s.\-]*)?(?:9[\s.\-]*\d{4}[\s.\-]*\d{4}|\d{4}[\s.\-]*\d{4}|9\d{8}|\d{8})'
)

MASKED_KEYWORDS = ("... ver número", "ver número", "...")


def _extrair_numeros(texto: str, ad_id: str | None = None) -> list[str]:
    """Extrai e normaliza números de telefone de um texto."""
    numeros = []
    for m in PHONE_REGEX.finditer(texto):
        raw = m.group()
        num = re.sub(r'\D', '', raw)
        if ad_id and str(ad_id) in num:
            continue
        if len(num) in (8, 9):
            num = '12' + num
        if 10 <= len(num) <= 13:
            numeros.append(num)
    return list(dict.fromkeys(numeros))


async def _aguardar_numero_revelar(page, selector: str, timeout_ms: int = 8000) -> str:
    """Aguarda o span mudar de máscara para número real e retorna o texto."""
    # Prefixar xpath= se for xpath, senão é css selector
    loc_str = f"xpath={selector}" if selector.startswith('/') else selector
    
    # A query js precisa usar querySelector ou evaluate dependendo do tipo
    js_query = f"""() => {{
        const el = "{selector}".startsWith('/') 
            ? document.evaluate("{selector}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue
            : document.querySelector("{selector}");
        if (!el) return false;
        const txt = el.textContent || '';
        const isNotMasked = !txt.includes('ver número') && !txt.includes('..');
        const hasDigits = (txt.replace(/\\D/g, '').length >= 8);
        return isNotMasked && hasDigits;
    }}"""

    try:
        await page.wait_for_function(js_query, timeout=timeout_ms)
        el = page.locator(loc_str).first
        return (await el.text_content(timeout=3000) or "").strip()
    except Exception:
        try:
            el = page.locator(loc_str).first
            return (await el.text_content(timeout=2000) or "").strip()
        except Exception:
            return ""


async def _fechar_modal_se_aberto(page) -> str:
    """
    Detecta o modal da OLX que aparece após clicar no botão de telefone.
    PRIMEIRO raspa o número contido no modal (se houver), DEPOIS fecha.
    Retorna o texto do telefone encontrado no modal, ou string vazia.
    """
    modal = page.locator('[data-ds-component="DS-Modal"][data-show="true"]')
    if await modal.count() == 0:
        return ""

    # ── Tenta raspar o número ANTES de fechar ────────────────────────────────
    telefone_no_modal = ""
    seletores_tel = [
        '[data-ds-component="DS-Modal"] a[href^="tel:"]',  # link tel: direto
        '[data-ds-component="DS-Modal"] [class*="phone"]',
        '[data-ds-component="DS-Modal"] span',
    ]
    for sel in seletores_tel:
        try:
            els = page.locator(sel)
            count = await els.count()
            for i in range(count):
                txt = (await els.nth(i).text_content(timeout=2000) or "").strip()
                # verifica se parece um número de telefone
                digits = "".join(c for c in txt if c.isdigit())
                if 8 <= len(digits) <= 13:
                    telefone_no_modal = txt
                    print(f"  📱 [MODAL] Telefone encontrado no modal: '{txt}'")
                    break
            if telefone_no_modal:
                break
        except Exception:
            pass

    # Tenta também href tel: (formato mais confiável)
    try:
        links_tel = page.locator('[data-ds-component="DS-Modal"] a[href^="tel:"]')
        if await links_tel.count() > 0:
            href = await links_tel.first.get_attribute('href', timeout=2000)
            if href:
                telefone_no_modal = href.replace('tel:', '').strip()
                print(f"  📱 [MODAL] Telefone via href tel: '{telefone_no_modal}'")
    except Exception:
        pass

    # ── Fecha o modal ─────────────────────────────────────────────────────────
    print("  ⚠️ Modal detectado! Fechando com ESC...")
    await page.keyboard.press('Escape')
    await asyncio.sleep(1)

    if await modal.count() > 0:
        for sel in [
            '.olx-modal-close-button',
            '[data-ds-component="DS-Modal"] button[aria-label]',
            '[data-ds-component="DS-Modal"] button',
        ]:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(0.5)
                    print(f"  ✅ Modal fechado via: {sel}")
                    break
            except Exception:
                pass

    return telefone_no_modal



async def extract_phones_from_olx(url: str) -> Dict[str, Any]:
    """
    Acessa a URL do anúncio OLX usando Playwright + cookies do Samuel.

    Fluxo com ordem aleatória para confundir anti-bot:
      Grupo A: Botão principal de telefone (price-box)
      Grupo B: Expandir descrição + clicar máscara oculta
    A ordem A→B ou B→A é sorteada a cada execução.
    """
    dados: Dict[str, Any] = {
        "expirado": False,
        "telefones": [],
        "erro": None,
        "bloqueado": False
    }

    ad_id = None
    id_match = re.search(r'-(\d+)$', url.split('?')[0])
    if id_match:
        ad_id = id_match.group(1)

    session_file = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'olx_session.json')
    )

    try:
        async with async_playwright() as p:
            print(f"🔍 Iniciando extração (Playwright + Sessão Samuel): {url}")

            # headless=False é OBRIGATÓRIO: o Cloudflare da OLX detecta
            # "HeadlessChrome" no header sec-ch-ua e bloqueia a API showphone
            # com 403. Em modo headed, a API retorna 200 normalmente.
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )

            try:
                context = await browser.new_context(
                    storage_state=session_file,
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                    viewport={'width': 1280, 'height': 800}
                )
                print("  ✅ Sessão do Samuel carregada.")
            except Exception as e:
                print(f"  ⚠️ Sessão não encontrada, rodando sem login: {e}")
                context = await browser.new_context()

            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
            )

            page = await context.new_page()

            # ── Rastreamento de bloqueios de API ──────────────────────────
            api_bloqueada = False

            def on_request_failed(request):
                nonlocal api_bloqueada
                if 'showphone' in request.url or 'grayzone' in request.url:
                    failure = request.failure or ''
                    print(f"  🚫 API bloqueada: {request.url[:80]} => {failure}")
                    api_bloqueada = True

            page.on('requestfailed', on_request_failed)

            # NÃO interceptamos rotas (sem bloqueio de imagens etc.)
            # para evitar problemas com o anti-bot Cloudflare

            try:
                print("  -> Navegando para a URL...")
                await page.goto(url, timeout=60000, wait_until='domcontentloaded')

                # Aguarda o React renderizar (delay humano aleatório)
                try:
                    await page.wait_for_selector('h1', timeout=10000)
                except Exception:
                    pass
                await asyncio.sleep(random.uniform(1.0, 2.5))

                # ── Verifica expirado ─────────────────────────────────────────
                title   = await page.title()
                content = await page.content()
                if any(kw in title.lower() or kw in content.lower() for kw in [
                    "anúncio finalizado", "ops!", "não encontrado",
                    "anúncio desativado", "página não encontrada"
                ]):
                    print("  ⚠️ Anúncio expirado ou indisponível.")
                    dados["expirado"] = True
                    await browser.close()
                    return dados

                # ═══════════════════════════════════════════════════════════
                # DEFINIÇÃO DOS GRUPOS DE PASSOS
                # ═══════════════════════════════════════════════════════════

                async def _grupo_botao():
                    """Grupo A: Botão principal de telefone (price-box lateral)"""
                    try:
                        print("  -> [BOTÃO] Aguardando botão principal de telefone...")
                        await page.wait_for_selector(
                            f"xpath={XPATH_BTN_PRINCIPAL}",
                            state="visible",
                            timeout=15000
                        )
                        btn = page.locator(f"xpath={XPATH_BTN_PRINCIPAL}").first
                        await btn.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.3, 1.2))
                        await btn.click()
                        print("  -> [BOTÃO] Clicado! Aguardando resposta...")
                        await asyncio.sleep(random.uniform(2.0, 3.5))

                        # Checa modal (pode ter número ou erro)
                        tem_numero_no_modal = False
                        modal = page.locator('[data-ds-component="DS-Modal"][data-show="true"]')
                        if await modal.count() > 0:
                            texto_modal = await modal.first.text_content()
                            if texto_modal and "Não foi possível exibir o telefone" not in texto_modal:
                                for num in _extrair_numeros(texto_modal, ad_id):
                                    if num not in [t["telefone"] for t in dados["telefones"]]:
                                        dados["telefones"].append({
                                            "nome": None, "telefone": num, "origem": "botao"
                                        })
                                        print(f"  ✅ [BOTÃO] Telefone via modal: {num}")
                                        tem_numero_no_modal = True

                        # Tenta ler do span do price-box
                        if not tem_numero_no_modal:
                            for loc in XPATHS_TELEFONE_PRINCIPAL:
                                try:
                                    tel_texto = await _aguardar_numero_revelar(
                                        page, loc, timeout_ms=5000
                                    )
                                    print(f"  -> [BOTÃO] Texto do span ({loc}): '{tel_texto}'")
                                    sucesso = False
                                    for num in _extrair_numeros(tel_texto, ad_id):
                                        if num not in [t.get("telefone") for t in dados["telefones"]]:
                                            dados["telefones"].append({
                                                "nome": None, "telefone": num, "origem": "botao"
                                            })
                                            print(f"  ✅ [BOTÃO] Telefone via span: {num}")
                                            sucesso = True
                                    if sucesso:
                                        break
                                except Exception:
                                    pass

                        # Fecha modal se estava aberto
                        if await modal.count() > 0:
                            try:
                                await page.keyboard.press("Escape")
                                await asyncio.sleep(random.uniform(0.3, 0.8))
                            except Exception:
                                pass

                    except Exception:
                        print("  ℹ️ [BOTÃO] Botão principal não encontrado (normal em alguns anúncios).")

                async def _grupo_descricao():
                    """Grupo B: Expandir descrição + clicar máscara oculta"""
                    # Sub-passo: Expandir descrição
                    try:
                        print("  -> [DESC] Verificando botão 'Ver descrição completa'...")
                        btn_desc = page.locator(f"xpath={XPATH_BTN_DESCRICAO}").first
                        if await btn_desc.count() > 0 and await btn_desc.is_visible():
                            await btn_desc.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(0.3, 1.0))
                            await btn_desc.click()
                            print("  -> [DESC] Descrição expandida.")
                            await asyncio.sleep(random.uniform(1.5, 3.0))
                        else:
                            print("  ℹ️ [DESC] Descrição já visível.")
                    except Exception as e_desc:
                        print(f"  ℹ️ [DESC] Botão de descrição indisponível: {e_desc}")

                    # Sub-passo: Clicar na máscara de telefone na descrição
                    try:
                        print("  -> [DESC] Verificando telefone oculto na descrição...")
                        mascara = page.locator(f"xpath={XPATH_MASCARA_DESCRICAO}").first

                        if await mascara.count() > 0 and await mascara.is_visible():
                            texto_mascara = (await mascara.text_content() or "").strip()
                            print(f"  -> [DESC] Elemento encontrado: '{texto_mascara}'")

                            is_masked = any(kw in (texto_mascara or "") for kw in MASKED_KEYWORDS)
                            if is_masked:
                                await mascara.scroll_into_view_if_needed()
                                await asyncio.sleep(random.uniform(0.3, 1.0))
                                await mascara.click()
                                print("  -> [DESC] Clique na máscara. Aguardando API...")

                                tel_desc_texto = await _aguardar_numero_revelar(
                                    page, XPATH_TEL_DESCRICAO, timeout_ms=8000
                                )
                                print(f"  -> [DESC] Texto após revelação: '{tel_desc_texto}'")

                                for num in _extrair_numeros(tel_desc_texto, ad_id):
                                    if num not in [t["telefone"] for t in dados["telefones"]]:
                                        dados["telefones"].append({
                                            "nome": None, "telefone": num, "origem": "descricao"
                                        })
                                        print(f"  ✅ [DESC] Telefone via descrição: {num}")
                            else:
                                # Número já visível diretamente
                                print(f"  -> [DESC] Número já visível: '{texto_mascara}'")
                                for num in _extrair_numeros(texto_mascara, ad_id):
                                    if num not in [t["telefone"] for t in dados["telefones"]]:
                                        dados["telefones"].append({
                                            "nome": None, "telefone": num, "origem": "descricao"
                                        })
                                        print(f"  ✅ [DESC] Telefone visível: {num}")
                        else:
                            print("  ℹ️ [DESC] Nenhum telefone oculto na descrição.")

                    except Exception as e_mask:
                        print(f"  ℹ️ [DESC] Sem máscara na descrição: {e_mask}")

                # ═══════════════════════════════════════════════════════════
                # EXECUTA OS GRUPOS EM ORDEM ALEATÓRIA
                # ═══════════════════════════════════════════════════════════
                if random.random() < 0.5:
                    print("  🔀 Ordem sorteada: BOTÃO → DESCRIÇÃO")
                    await _grupo_botao()
                    await asyncio.sleep(random.uniform(1.5, 4.0))
                    await _grupo_descricao()
                else:
                    print("  🔀 Ordem sorteada: DESCRIÇÃO → BOTÃO")
                    await _grupo_descricao()
                    await asyncio.sleep(random.uniform(1.5, 4.0))
                    await _grupo_botao()

                # ═══════════════════════════════════════════════════════════
                # FALLBACK ─ Retentativa do botão se necessário
                # ═══════════════════════════════════════════════════════════
                if not any(t["origem"] == "botao" for t in dados["telefones"]):
                    try:
                        print("  -> [FALLBACK] Retentativa do botão principal...")
                        btn = page.locator(f"xpath={XPATH_BTN_PRINCIPAL}").first
                        if await btn.count() > 0 and await btn.is_visible():
                            await btn.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            await btn.click()
                            await asyncio.sleep(random.uniform(2.0, 3.5))

                            telefone_modal = await _fechar_modal_se_aberto(page)
                            if telefone_modal:
                                for num in _extrair_numeros(telefone_modal, ad_id):
                                    if num not in [t["telefone"] for t in dados["telefones"]]:
                                        dados["telefones"].append({
                                            "nome": None, "telefone": num, "origem": "botao"
                                        })
                                        print(f"  ✅ [FALLBACK] Telefone via modal: {num}")
                            else:
                                for loc in XPATHS_TELEFONE_PRINCIPAL:
                                    try:
                                        tel_texto = await _aguardar_numero_revelar(
                                            page, loc, timeout_ms=5000
                                        )
                                        sucesso_fb = False
                                        for num in _extrair_numeros(tel_texto, ad_id):
                                            if num not in [t["telefone"] for t in dados["telefones"]]:
                                                dados["telefones"].append({
                                                    "nome": None, "telefone": num, "origem": "botao"
                                                })
                                                print(f"  ✅ [FALLBACK] Telefone recuperado: {num}")
                                                sucesso_fb = True
                                        if sucesso_fb:
                                            break
                                    except Exception:
                                        pass
                    except Exception as e_fb:
                        print(f"  ℹ️ [FALLBACK] Tentativa falhou: {e_fb}")

                # ═══════════════════════════════════════════════════════════
                # DETECÇÃO DE BLOQUEIO CLOUDFLARE
                # ═══════════════════════════════════════════════════════════
                if api_bloqueada and len(dados["telefones"]) == 0:
                    dados["bloqueado"] = True
                    print("  🚫 BLOQUEIO DETECTADO: API showphone foi bloqueada pelo Cloudflare.")

                await page.screenshot(path="debug_final_result.png")

            except Exception as e:
                print(f"  🚨 Erro durante navegação/interação: {e}")
                dados["erro"] = str(e)

            await browser.close()
            print(f"✅ Extração finalizada: {len(dados['telefones'])} contato(s) encontrado(s).")

    except Exception as e:
        print(f"🚨 Erro crítico Playwright: {e}")
        dados["erro"] = str(e)

    return dados


if __name__ == "__main__":
    url_teste = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/casa-a-venda-no-j-satelite-aceita-troca-por-casa-no-jardim-portugal-ou-bosque-1467276395"

    async def teste_local():
        resultado = await extract_phones_from_olx(url_teste)
        print("\n📋 Resultado Final:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

    asyncio.run(teste_local())
