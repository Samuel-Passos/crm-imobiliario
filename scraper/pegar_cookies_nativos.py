import browser_cookie3
import json
import traceback

SESSION_FILE = "olx_session.json"

def extrair_cookies_do_chrome_ubuntu():
    print("Tentando roubar cookies do seu Google Chrome Linux legítimo...")
    try:
        # Pega TODOS os cookies do dominio olx.com.br
        cj = browser_cookie3.chrome(domain_name='olx.com.br')
        
        # Pega localstorage e cookies no formato exato que o Playwright engole...
        cookies_playwright = []
        for cookie in cj:
            cookies_playwright.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "expires": -1 if cookie.expires is None else cookie.expires,
                "httpOnly": "HttpOnly" in getattr(cookie, '_rest', {}),
                "secure": bool(cookie.secure),
                "sameSite": "Lax" # padrão pro Playwright
            })
            
        print(f"Extratores mágicos pegaram {len(cookies_playwright)} cookies da OLX!")
        
        state = {
            "cookies": cookies_playwright,
            "origins": [] # O local storage ficara pra depois se precisar, os cookies do Cloudflare/Login são a chave.
        }
        
        with open(SESSION_FILE, "w") as f:
            json.dump(state, f, indent=4)
            
        print(f"✅ MÁGICA CONCLUÍDA! Cookies oficias salvos em: {SESSION_FILE}")
        
    except Exception as e:
        print("🚨 Deu errinho mágico: ")
        traceback.print_exc()

if __name__ == "__main__":
    extrair_cookies_do_chrome_ubuntu()
