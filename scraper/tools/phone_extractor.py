import asyncio
import re
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

CHROME_PROFILE_PATH = os.getenv('CHROME_PROFILE_PATH', '/home/samuel/.config/google-chrome')

def setup_temp_profile(user_data_dir: str, profile_dir: str = 'Default') -> str:
    """
    Copia o diretório de dados do usuário (somente a pasta Default e Local State) 
    para um diretório temporário, permitindo que o Playwright rode persistente 
    mesmo que o usuário já esteja com o Chrome aberto.
    """
    temp_dir = tempfile.mkdtemp(prefix='playwright-profile-tmp-')
    path_original_user_data = Path(user_data_dir)
    path_original_profile = path_original_user_data / profile_dir
    path_temp_profile = Path(temp_dir) / profile_dir

    if path_original_profile.exists():
        shutil.copytree(path_original_profile, path_temp_profile)
        local_state_src = path_original_user_data / 'Local State'
        local_state_dst = Path(temp_dir) / 'Local State'
        if local_state_src.exists():
            shutil.copy(local_state_src, local_state_dst)
    else:
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        path_temp_profile.mkdir(parents=True, exist_ok=True)
        
    return temp_dir

def extract_phone_numbers(text: str) -> list:
    """Extrai potencias números de telefone de um texto bruto e retorna uma lista."""
    if not text:
        return []
    # Regex para capturar números tipo (11) 99999-9999 ou 11999999999 (várias abordagens)
    pattern = r'(?:\+?55\s?)?(?:\(?0?[1-9]{2}\)?\s?)?(?:9\d{4}[-\s]?\d{4}|\d{4}[-\s]?\d{4})'
    matches = re.finditer(pattern, text)
    telefones = []
    
    for match in matches:
        num = re.sub(r'\D', '', match.group())
        # Filtro básico: se o número tiver entre 10 e 11 caracteres formatado
        if len(num) >= 10 and len(num) <= 11:
            if num not in [t['telefone'] for t in telefones]:
                telefones.append({"nome": None, "telefone": num})
    return telefones

async def extract_phones_from_olx(url: str) -> Dict[str, Any]:
    """
    Acessa a URL do anúncio OLX usando Playwright puro (através do Browser context)
    e interage com a página usando os XPaths exatos para extrair telefones, 
    sem custo de LLM. Cria uma instância baseada no perfil local.
    """
    dados = {
        "expirado": False,
        "telefones": [],
        "erro": None
    }
    
    try:
        async with async_playwright() as p:
            print("Abrindo Playwright com Cookies Injetados Oficiais da sua Sessão Real...")
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            # Injeta todos os cookies que roubamos do seu Google Chrome Linux
            try:
                context = await browser.new_context(
                    storage_state="olx_session.json",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                )
            except Exception as e:
                print(f"⚠️ Aviso: Arquivo de sessão não encontrado ou inválido. O robô irá nu e cru: {e}")
                context = await browser.new_context()
                
            page = await context.new_page()
            
            # Define um timeout para a página carregar e previne redirecionamentos de links como tel:
            try:
                await context.route("tel:**", lambda route: route.abort())
                await page.goto(url, timeout=20000, wait_until='domcontentloaded')
            except Exception as e:
                print(f"⚠️ Aviso no carregamento da página (Timeout ou fechamento parcial): {e}")
            
            await asyncio.sleep(5) # tempinho para o botão de telefone aparecer e a página aterrissar (elevado por causa do fallback de anti-bot)
            
            # 1. VERIFICAR SE O ANÚNCIO ESTÁ INDISPONÍVEL
            # Em geral, o OLX mostra telas de "Anúncio não encontrado" ou "ops.."
            title = await page.title()
            if "ops!" in title.lower() or "não encontrado" in title.lower():
                dados["expirado"] = True
                return dados
                
            # print debug
            try:
                await page.screenshot(path="debug_olx.png", full_page=True)
            except Exception as e:
                print(f"Erro ao tirar temp print: {e}")
                
            # 2. CLICAR E LER TELEFONE PRINCIPAL (BOTÃO OFICIAL)
            btn_phone_xpath = '//*[@id="price-box-button-show-phone"]'
            btn_phone = page.locator(f"xpath={btn_phone_xpath}")
            
            if await btn_phone.count() > 0:
                print("➡️ Botão 'Exibir Telefone' encontrado. Clicando...")
                # O clique no botão principal pode re-renderizar a tela, então no wait
                try:
                    await btn_phone.click(timeout=3000, no_wait_after=True, force=True)
                except Exception:
                    pass
                await asyncio.sleep(2) # aguardar o javascript da mask desmascarar o número
                
                # O texto revelado surge em uma nova tag span específica
                phone_span_xpath = '//*[@id="price-box-container"]/div[2]/div[1]/span'
                phone_span = page.locator(f"xpath={phone_span_xpath}")
                
                if await phone_span.count() > 0:
                    phone_text = await phone_span.inner_text()
                    extracted = extract_phone_numbers(phone_text)
                    for t in extracted:
                        t["origem"] = "botao"
                        dados["telefones"].append(t)
                else:
                    print("⚠️ Span do telefone não apareceu após o clique.")
                    await page.screenshot(path="debug_olx_error.png", full_page=True)
            
            # 3. EXPANDIR DESCRIÇÃO
            btn_desc_xpath = '//*[@id="description-title"]/div/div[2]/div/button'
            btn_desc = page.locator(f"xpath={btn_desc_xpath}")
            if await btn_desc.count() > 0:
                print("➡️ Botão 'Ver descrição completa' encontrado. Expandindo texto...")
                try:
                    await btn_desc.click(timeout=3000)
                    await asyncio.sleep(1)
                except:
                    pass
            
            # 4. VARRER TODA A PÁGINA (ESPECIALMENTE DESCRIÇÃO) CLICANDO EM POSSÍVEIS MÁSCARAS DE TELEFONE
            # Tentar 3 abordagens de elementos mascarados (data-element, role=button na descrição, e texto "ver número")
            locators_to_try = [
                "[data-element='button_show-phone']",
                '//*[@id="description-title"]//span[@role="button"]',
                "//*[contains(translate(text(), 'VER NÚMERO', 'ver número'), 'ver número')]"
            ]
            
            for loc in locators_to_try:
                elements = page.locator(loc if loc.startswith("[") else f"xpath={loc}")
                count = await elements.count()
                for i in range(count):
                    try:
                        # Forçar o clique para ignorar re-renderizações e não aguardar navegação acidental
                        await elements.nth(i).click(timeout=2000, no_wait_after=True, force=True)
                        await asyncio.sleep(1)
                    except:
                        pass
            
            # 5. LER TEXTO DA DESCRIÇÃO DE FATO (INDEPENDENTE DE TER CLICADO EM BOTÃO OU NÃO)
            desc_box = page.locator("[data-testid='ad-description']")
            if await desc_box.count() == 0:
                desc_box = page.locator('xpath=//*[@id="description-title"]/div/div[2]/div')
            
            if await desc_box.count() > 0:
                desc_text = await desc_box.inner_text()
                print("➡️ Buscando telefones secundários no texto da descrição...")
                extra_tels = extract_phone_numbers(desc_text)
                
                # Evita duplicar se o telefone da descrição for o mesmo do botão
                existentes_numeros = [t["telefone"] for t in dados["telefones"]]
                for ext in extra_tels:
                    if ext["telefone"] not in existentes_numeros:
                        ext["origem"] = "descricao"
                        dados["telefones"].append(ext)
                        existentes_numeros.append(ext["telefone"])
            
            await page.close()
            await browser.close()
            
            print(f"✅ Extração Playwright finalizada. {len(dados['telefones'])} contatos resgatados.")
    
    except Exception as e:
        print(f"🚨 Erro durante a extração via Playwright: {e}")
        dados["erro"] = str(e)
            
    return dados
    
if __name__ == "__main__":
    url_teste = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/terrenos/oportunidade-de-terreno-com-linda-vista-da-represa-1476153411"
    async def teste_local():
        resultado = await extract_phones_from_olx(url_teste)
        print("\nResultado Final:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    asyncio.run(teste_local())
