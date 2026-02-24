import asyncio
from playwright.async_api import async_playwright
import os

SESSION_FILE = "olx_session.json"

async def create_and_save_session():
    print("Iniciando Playwright para Login Manual...")
    async with async_playwright() as p:
        # Abrir browser visual para o usuário preencher captcha e logar
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navegando para a página de Login da OLX...")
        await page.goto("https://conta.olx.com.br/acesso")

        print("\n" + "="*50)
        print("👤 AÇÃO NECESSÁRIA:")
        print("Por favor, faça o login na página do navegador que se abriu.")
        print("Resolva qualquer Cloudflare ou CAPTCHA visualmente.")
        print("Quando estiver logado e na tela inicial, volte aqui e pressione ENTER.")
        print("="*50 + "\n")
        
        # Espera pela ação humana
        input("Pressione ENTER após concluir o login com sucesso no navegador...")

        # Salva o arquivo contendo cookies, localStorage e sessionStorage da página
        print("Salvando estado da sessão...")
        await context.storage_state(path=SESSION_FILE)
        
        print(f"✅ Sessão salva com sucesso em '{SESSION_FILE}'!")
        print("O robô passará a usar este arquivo para autenticar sem captcha. Pode fechar.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(create_and_save_session())
