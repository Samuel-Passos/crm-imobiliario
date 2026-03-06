import asyncio
import os
import subprocess
import threading
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext

# Variáveis globais para segurar a sessão do browser
_playwright: Playwright | None = None
_browser: Browser | None = None
_context: BrowserContext | None = None
_page: None = None  # Agora publicamos a aba padrão para reuso seguro!
_extraction_lock = asyncio.Lock()  # Lock para garantir sequencialidade e evitar colisão de cliques

import random
from playwright_stealth import Stealth

def _get_random_fingerprint():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15"
    ]
    viewports = [
        {'width': 1920, 'height': 1080},
        {'width': 1366, 'height': 768},
        {'width': 1536, 'height': 864},
        {'width': 1440, 'height': 900},
        {'width': 1280, 'height': 800}
    ]
    return random.choice(user_agents), random.choice(viewports)

async def start_browser() -> BrowserContext:
    """
    Inicia o Playwright, o Chromium (via watcher no WS2), carrega os cookies,
    abre a aba padrão e retorna o contexto global, com evasao Anti-Bot.
    """
    global _playwright, _browser, _context

    if _context is not None:
        return _context

    print("🌐 [BROWSER MANAGER] Iniciando sessão global persistente do Playwright...")

    _playwright = await async_playwright().start()

    # Launch do browser
    _browser = await _playwright.chromium.launch(
        headless=False,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
        ]
    )

    # Carrega sessão (cookies)
    session_file = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'olx_session.json')
    )

    chosen_ua, chosen_vp = _get_random_fingerprint()
    print(f"  🎭 [ANTI-BOT] Camuflagem sorteada: Viewport {chosen_vp['width']}x{chosen_vp['height']} | UA: ...{chosen_ua[-40:]}")

    try:
        _context = await _browser.new_context(
            storage_state=session_file,
            user_agent=chosen_ua,
            viewport=chosen_vp
        )
        print("  ✅ [BROWSER MANAGER] Sessão do Samuel carregada com sucesso.")
    except Exception as e:
        print(f"  ⚠️ [BROWSER MANAGER] Sessão não encontrada, rodando sem login: {e}")
        _context = await _browser.new_context(
            user_agent=chosen_ua,
            viewport=chosen_vp
        )

    await _context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )

    # Abre a página em branco primeiro para pegar a janela
    print("  -> Preparando a aba padrão e ancorando no Workspace 2...")
    default_page = await _context.new_page()
    
    # Injeta proteções stealth na página para ocultar a assinatura de robô
    await Stealth().apply_stealth_async(default_page)
    
    # ── MÁGICA ──
    # Para mover a janela correta, damos um título impossível de conflitar.
    magical_title = "OLX_SCRAPER_BACKGROUND_WINDOW_XYZ"
    await default_page.evaluate(f'document.title = "{magical_title}"')
    
    # Aguarda o X11 registrar o nome e move
    import time
    moved = False
    for _ in range(20):
        # -r <nome> move a janela com esse substring no título
        # -t 1 move para o workspace de index 1 (Workspace 2)
        res = subprocess.run(['wmctrl', '-r', magical_title, '-t', '1'], capture_output=True)
        if res.returncode == 0:
            moved = True
            break
        time.sleep(0.5)
        
    if moved:
        print("  🖥️  [WORKSPACE] ✅ Janela firmemente fixada no Workspace 2 (usando wmctrl).")
    else:
        print("  ⚠️  [WORKSPACE] Falha ou timeout ao tentar mover a janela para o Workspace 2.")

    try:
        # Apenas vai para um link neutro da região para manter os cookies quentes no mesmo TLD
        await default_page.goto(
            "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos",
            timeout=60000, 
            wait_until='domcontentloaded'
        )
        print("  ✅ [BROWSER MANAGER] Aba padrão carregada na rota base.")
    except Exception as e:
        print(f"  ⚠️ [BROWSER MANAGER] Timeout ao carregar aba padrão (não impedirá o funcionamento): {e}")

    # Salva globalmente para reuso sem criar novas abas
    global _page
    _page = default_page

    return _context

def get_context() -> BrowserContext | None:
    """Retorna o contexto atual se estiver rodando, ou None."""
    return _context
    
def get_page():
    """Retorna a página global fixada no WS2."""
    return _page

def get_lock() -> asyncio.Lock:
    """Retorna o Lock para ser usado no orquestrador."""
    return _extraction_lock

async def close_browser():
    """Fecha tudo graciosamente."""
    global _playwright, _browser, _context
    print("🛑 [BROWSER MANAGER] Encerrando sessão global persistente...")
    if _context:
        try:
            await _context.close()
        except Exception:
            pass
        _context = None
    
    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None
    
    print("  ✅ [BROWSER MANAGER] Playwright encerrado com sucesso.")
