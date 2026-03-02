import asyncio
import re
import json
import os
from typing import Dict, Any
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# ─── XPaths Confirmados (Samuel) ─────────────────────────────────────────────
XPATH_BTN_PRINCIPAL      = '//*[@id="price-box-button-show-phone"]'
XPATH_TELEFONE_PRINCIPAL = '//*[@id="price-box-container"]/div[2]/div[1]/span'
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


async def _aguardar_numero_revelar(page, xpath: str, timeout_ms: int = 8000) -> str:
    """Aguarda o span mudar de máscara para número real e retorna o texto."""
    try:
        await page.wait_for_function(
            """(xpath) => {
                const el = document.evaluate(
                    xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                ).singleNodeValue;
                if (!el) return false;
                const txt = el.textContent || '';
                const isNotMasked = !txt.includes('ver número') && !txt.includes('..');
                const hasDigits = (txt.replace(/\\D/g, '').length >= 8);
                return isNotMasked && hasDigits;
            }""",
            arg=xpath,
            timeout=timeout_ms
        )
        el = page.locator(f"xpath={xpath}").first
        return (await el.text_content(timeout=3000) or "").strip()
    except Exception:
        try:
            el = page.locator(f"xpath={xpath}").first
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

    Fluxo de 3 passos:
      1. Clica #price-box-button-show-phone → raspa XPATH_TELEFONE_PRINCIPAL.
      2. Clica botão "Ver descrição completa" → expande descrição.
      3. Clica máscara "ver número" na descrição → aguarda API → raspa número.
    """
    dados: Dict[str, Any] = {
        "expirado": False,
        "telefones": [],
        "erro": None
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

            browser = await p.chromium.launch(
                headless=True,
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

            async def intercept_route(route):
                if route.request.resource_type in ("image", "media", "font"):
                    return await route.abort()
                await route.continue_()

            await page.route("**/*", intercept_route)

            try:
                print("  -> Navegando para a URL...")
                await page.goto(url, timeout=60000, wait_until='domcontentloaded')

                # Aguarda o React renderizar os componentes (título do anúncio é um bom indicador)
                try:
                    await page.wait_for_selector('h1', timeout=10000)
                except Exception:
                    pass  # Continua mesmo que o h1 demore

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
                # PASSO 1 ─ Botão principal de telefone (price box lateral)
                # ═══════════════════════════════════════════════════════════
                try:
                    print("  -> [PASSO 1] Aguardando botão principal de telefone...")
                    await page.wait_for_selector(
                        f"xpath={XPATH_BTN_PRINCIPAL}",
                        state="visible",
                        timeout=15000  # 15s — React pode demorar para renderizar
                    )
                    btn = page.locator(f"xpath={XPATH_BTN_PRINCIPAL}").first
                    await btn.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await btn.click()
                    print("  -> [PASSO 1] Clicado! Aguardando resposta...")
                    await asyncio.sleep(2)

                    # Fecha modal se apareceu (comportamento de alguns anúncios) E tenta pegar o número de lá
                    telefone_modal = await _fechar_modal_se_aberto(page)
                    await asyncio.sleep(0.5)

                    if telefone_modal:
                        for num in _extrair_numeros(telefone_modal, ad_id):
                            if num not in [t["telefone"] for t in dados["telefones"]]:
                                dados["telefones"].append({
                                    "nome": None, "telefone": num, "origem": "botao"
                                })
                                print(f"  ✅ [PASSO 1] Telefone via modal do botão: {num}")
                    else:
                        # Se não pegou do modal, tenta raspar o número do span revelado
                        try:
                            tel_texto = await _aguardar_numero_revelar(
                                page, XPATH_TELEFONE_PRINCIPAL, timeout_ms=8000
                            )
                            print(f"  -> [PASSO 1] Texto do span: '{tel_texto}'")
                            for num in _extrair_numeros(tel_texto, ad_id):
                                if num not in [t["telefone"] for t in dados["telefones"]]:
                                    dados["telefones"].append({
                                        "nome": None, "telefone": num, "origem": "botao"
                                    })
                                    print(f"  ✅ [PASSO 1] Telefone via botão: {num}")
                        except Exception as e_read:
                            print(f"  ⚠️ [PASSO 1] Não conseguiu ler span: {e_read}")

                except Exception:
                    print("  ℹ️ [PASSO 1] Botão principal não encontrado (normal em alguns anúncios).")

                # ═══════════════════════════════════════════════════════════
                # PASSO 2 ─ Expande a descrição completa
                # ═══════════════════════════════════════════════════════════
                try:
                    print("  -> [PASSO 2] Verificando botão 'Ver descrição completa'...")
                    btn_desc = page.locator(f"xpath={XPATH_BTN_DESCRICAO}").first
                    if await btn_desc.count() > 0 and await btn_desc.is_visible():
                        await btn_desc.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await btn_desc.click()
                        print("  -> [PASSO 2] Descrição expandida. Aguardando DOM...")
                        await asyncio.sleep(2)
                    else:
                        print("  ℹ️ [PASSO 2] Descrição já completamente visível.")
                except Exception as e_desc:
                    print(f"  ℹ️ [PASSO 2] Botão de descrição indisponível: {e_desc}")

                # ═══════════════════════════════════════════════════════════
                # PASSO 3 ─ Telefone oculto na descrição ("12 9... ver número")
                # ═══════════════════════════════════════════════════════════
                try:
                    print("  -> [PASSO 3] Verificando telefone oculto na descrição...")
                    mascara = page.locator(f"xpath={XPATH_MASCARA_DESCRICAO}").first

                    if await mascara.count() > 0 and await mascara.is_visible():
                        texto_mascara = (await mascara.text_content() or "").strip()
                        print(f"  -> [PASSO 3] Elemento encontrado: '{texto_mascara}'")

                        is_masked = any(kw in (texto_mascara or "") for kw in MASKED_KEYWORDS)
                        if is_masked:
                            await mascara.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await mascara.click()
                            print("  -> [PASSO 3] Clique efetuado. Aguardando número revelar pela API...")

                            tel_desc_texto = await _aguardar_numero_revelar(
                                page, XPATH_TEL_DESCRICAO, timeout_ms=8000
                            )
                            print(f"  -> [PASSO 3] Texto após revelação: '{tel_desc_texto}'")

                            for num in _extrair_numeros(tel_desc_texto, ad_id):
                                if num not in [t["telefone"] for t in dados["telefones"]]:
                                    dados["telefones"].append({
                                        "nome": None, "telefone": num, "origem": "descricao"
                                    })
                                    print(f"  ✅ [PASSO 3] Telefone via descrição: {num}")
                        else:
                            # Número já estava visível diretamente
                            print(f"  -> [PASSO 3] Número já visível: '{texto_mascara}'")
                            for num in _extrair_numeros(texto_mascara, ad_id):
                                if num not in [t["telefone"] for t in dados["telefones"]]:
                                    dados["telefones"].append({
                                        "nome": None, "telefone": num, "origem": "descricao"
                                    })
                                    print(f"  ✅ [PASSO 3] Telefone visível: {num}")
                    else:
                        print("  ℹ️ [PASSO 3] Nenhum telefone oculto na descrição.")

                except Exception as e_mask:
                    print(f"  ℹ️ [PASSO 3] Sem máscara na descrição: {e_mask}")

                # ═══════════════════════════════════════════════════════════
                # PASSO 4 ─ Retentativa do Botão Principal (Fallback)
                # ═══════════════════════════════════════════════════════════
                # Se o PASSO 1 falhou (ex: API OLX deu erro temporário) e o botão
                # ainda está lá, tentamos clicar nele de novo agora que o PASSO 3
                # (e possivelmente uma nova chamada de API) já ocorreu.
                if len(dados["telefones"]) == 1 and not any(t["origem"] == "botao" for t in dados["telefones"]):
                    try:
                        print("  -> [PASSO 4] Retentativa do botão principal (API OLX pode ter se recuperado)...")
                        btn = page.locator(f"xpath={XPATH_BTN_PRINCIPAL}").first
                        if await btn.count() > 0 and await btn.is_visible():
                            await btn.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await btn.click()
                            await asyncio.sleep(2)
                            
                            # Tenta raspar do modal novamente
                            telefone_modal = await _fechar_modal_se_aberto(page)
                            if telefone_modal:
                                for num in _extrair_numeros(telefone_modal, ad_id):
                                    if num not in [t["telefone"] for t in dados["telefones"]]:
                                        dados["telefones"].append({
                                            "nome": None, "telefone": num, "origem": "botao"
                                        })
                                        print(f"  ✅ [PASSO 4] Telefone via modal do botão: {num}")
                            else:
                                # Tenta raspar o número inline
                                try:
                                    tel_texto = await _aguardar_numero_revelar(
                                        page, XPATH_TELEFONE_PRINCIPAL, timeout_ms=5000
                                    )
                                    for num in _extrair_numeros(tel_texto, ad_id):
                                        if num not in [t["telefone"] for t in dados["telefones"]]:
                                            dados["telefones"].append({
                                                "nome": None, "telefone": num, "origem": "botao"
                                            })
                                            print(f"  ✅ [PASSO 4] Telefone recuperado via botão: {num}")
                                except Exception:
                                    pass
                    except Exception as e_passo4:
                        print(f"  ℹ️ [PASSO 4] Tentativa falhou: {e_passo4}")

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
