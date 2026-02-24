import asyncio
from playwright.async_api import async_playwright
import os

SESSION_FILE = "olx_session.json"

async def auto_login():
    print("Iniciando Playwright para Login Automático...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        # Adiciona um script para mascarar o webdriver
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = await context.new_page()

        print("Navegando para a página de Login da OLX...")
        await page.goto("https://conta.olx.com.br/acesso", wait_until='domcontentloaded')
        await page.screenshot(path="debug_login_step1.png")
        
        print("Procurando campo de e-mail...")
        try:
            # Pega o input visível que deve ser o E-mail
            input_email = page.locator("input:not([type='hidden'])").first
            await input_email.wait_for(timeout=5000)
            await input_email.fill("samuel.passosp@gmail.com")
            await page.screenshot(path="debug_login_step2.png")
            
            # Clicar no botão Acessar
            btn_acessar = page.locator("button:has-text('Acessar')").first
            if await btn_acessar.count() > 0:
                 print("Clicando no botão Acessar...")
                 await btn_acessar.click()
                 await asyncio.sleep(3)
        except Exception as e:
            print(f"Erro ao preencher email: {e}")
            
        await page.screenshot(path="debug_login_step3.png")

        print("Procurando campo de senha...")
        try:
            senha_selector = "input[type='password']"
            await page.wait_for_selector(senha_selector, timeout=5000)
            await page.fill(senha_selector, "Eu@moimoveis2026")
            
            # Clicar em Entrar
            btn_entrar = page.locator("button:has-text('Entrar')").first
            if await btn_entrar.count() > 0:
                print("Clicando em Entrar...")
                await btn_entrar.click()
                
            # Aguardar sumir o campo de senha ou aparecer a Home
            print("Aguardando login concluir...")
            await asyncio.sleep(8)
            await page.screenshot(path="debug_login_step4.png")
            
            # Vamos checar se logou guardando o Storage
            print("Login aparentemente bem sucedido! Salvando sessão...")
            await context.storage_state(path=SESSION_FILE)
            print(f"✅ Sessão salva em '{SESSION_FILE}'")
                
        except Exception as e:
            print(f"Erro ao preencher senha: {e}")
            await page.screenshot(path="debug_login_error.png", full_page=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(auto_login())
