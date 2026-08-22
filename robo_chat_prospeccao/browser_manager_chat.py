import asyncio
import os
import subprocess
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext

_playwright: Playwright | None = None
_browser: Browser | None = None
_context: BrowserContext | None = None
_page = None

async def start_chat_browser() -> BrowserContext:
    """
    Inicia o Playwright, o Chromium (ancorado no Workspace 3),
    carrega os cookies, e mantém a aba aberta.
    """
    global _playwright, _browser, _context, _page

    if _context is not None:
        return _context

    print("🌐 [CHAT BROWSER] Iniciando sessão persistente (Workspace 2)...")
    _playwright = await async_playwright().start()

    _browser = await _playwright.chromium.launch(
        executable_path="/usr/bin/chromium",
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
    )

    scraper_dir = os.path.join(os.path.dirname(__file__), "..", "scraper")
    session_file = os.path.normpath(os.path.join(scraper_dir, 'olx_session.json'))

    context_kwargs = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "viewport": {"width": 1366, "height": 768},
        "locale": "pt-BR",
        "timezone_id": "America/Sao_Paulo",
    }

    if os.path.exists(session_file):
        context_kwargs["storage_state"] = session_file
        print(f"  🍪 [CHAT BROWSER] Sessão carregada.")
    else:
        print(f"  ⚠️ [CHAT BROWSER] Sessão NÃO carregada, rodando deslogado.")

    _context = await _browser.new_context(**context_kwargs)

    # Aplica stealth
    from playwright_stealth import Stealth
    stealth = Stealth()
    _context.on('page', lambda page: asyncio.create_task(stealth.apply_stealth_async(page)))

    print("  -> Preparando a aba de Chat no Workspace 2...")
    _page = await _context.new_page()
    
    # ── ANCORAR NO WORKSPACE 2 ──
    magical_title = "OLX_CHAT_MONITOR_WS2"
    await _page.evaluate(f'document.title = "{magical_title}"')
    
    import time
    moved = False
    for _ in range(20):
        # -t 1 move para o Workspace 2 (index 1)
        res = subprocess.run(['wmctrl', '-r', magical_title, '-t', '1'], capture_output=True)
        if res.returncode == 0:
            moved = True
            break
        time.sleep(0.5)
        
    if moved:
        print("  🖥️  [WORKSPACE] ✅ Janela firmemente fixada no Workspace 2.")
    else:
        print("  ⚠️  [WORKSPACE] Falha ao tentar mover a janela para o Workspace 2 (talvez não haja interface gráfica).")

    try:
        await _page.goto("https://chat.olx.com.br/", timeout=60000, wait_until='domcontentloaded')
        print("  ✅ [CHAT BROWSER] Aba ancorada na página principal de Chat.")
    except Exception as e:
        print(f"  ⚠️ [CHAT BROWSER] Timeout ao carregar: {e}")

    return _context

def get_chat_page():
    return _page

async def close_chat_browser():
    global _playwright, _browser, _context, _page
    if _context:
        await _context.close()
    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()
    _context = None
    _browser = None
    _playwright = None
    _page = None
