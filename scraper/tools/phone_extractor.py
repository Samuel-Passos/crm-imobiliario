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
        
    # Regex melhorada: captura formatos com DDD opcional, espaços, parênteses e hífens
    # Agora também captura números de 8 ou 9 dígitos sozinhos
    pattern = r'(?:\+?55\s?)?(?:\(?0?[1-9]{2}\)?\s?)?(?:9\d{4}[-\s]?\d{4}|\d{4}[-\s]?\d{4})'
    matches = re.finditer(pattern, text)
    telefones = []
    
    for match in matches:
        raw_match = match.group()
        num = re.sub(r'\D', '', raw_match)
        
        # Filtro inteligente: 
        # 10 ou 11 dígitos = Completo com DDD
        # 8 ou 9 dígitos = Sem DDD (provavelmente local)
        if 8 <= len(num) <= 11:
            # Se tiver 8 ou 9, vamos manter como extraído, o CRM pode tratar depois
            # ou podemos assumir DDD 12 se for o padrão da região (comentado por segurança)
            # if len(num) == 9: num = "12" + num 
            
            if num not in [t['telefone'] for t in telefones]:
                telefones.append({"nome": None, "telefone": num})
    return telefones

async def extract_phones_from_olx(url: str) -> Dict[str, Any]:
    """
    Acessa a URL do anúncio OLX usando Playwright puro e interage com a página 
    usando os XPaths exatos para extrair telefones.
    """
    dados = {
        "expirado": False,
        "telefones": [],
        "erro": None
    }
    
    try:
        async with async_playwright() as p:
            print("Abrindo Playwright com Cookies Injetados Oficiais...")
            browser = await p.chromium.launch(
                headless=False, # Alterado para o usuário ver o navegador abrindo
                args=['--disable-blink-features=AutomationControlled']
            )
            
            try:
                context = await browser.new_context(
                    storage_state="olx_session.json",
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
                )
            except Exception as e:
                print(f"⚠️ Aviso: Arquivo de sessão não encontrado. {e}")
                context = await browser.new_context()
                
            page = await context.new_page()
            
            try:
                await context.route("tel:**", lambda route: route.abort())
                await page.goto(url, timeout=30000, wait_until='domcontentloaded')
            except Exception as e:
                print(f"⚠️ Aviso no carregamento: {e}")
            
            await asyncio.sleep(4) 
            
            # 1. VERIFICAR SE O ANÚNCIO ESTÁ INDISPONÍVEL
            title = await page.title()
            if "ops!" in title.lower() or "não encontrado" in title.lower():
                dados["expirado"] = True
                await browser.close()
                return dados
                
            # 2. CLICAR E LER TELEFONE PRINCIPAL (BOTÃO OFICIAL)
            btn_phone_xpath = '//*[@id="price-box-button-show-phone"]'
            btn_phone = page.locator(f"xpath={btn_phone_xpath}")
            
            if await btn_phone.count() > 0:
                print("➡️ Botão 'Exibir Telefone' encontrado. Clicando...")
                try:
                    await btn_phone.click(timeout=3000, no_wait_after=True, force=True)
                    await asyncio.sleep(2)
                    
                    phone_span_xpath = '//*[@id="price-box-container"]/div[2]/div[1]/span'
                    phone_span = page.locator(f"xpath={phone_span_xpath}")
                    
                    if await phone_span.count() > 0:
                        phone_text = await phone_span.inner_text()
                        for t in extract_phone_numbers(phone_text):
                            t["origem"] = "botao"
                            dados["telefones"].append(t)
                except Exception:
                    pass
            
            # 3. EXPANDIR DESCRIÇÃO
            btn_desc_xpath = '//*[@id="description-title"]/div/div[2]/div/button'
            btn_desc = page.locator(f"xpath={btn_desc_xpath}")
            if await btn_desc.count() > 0:
                print("➡️ Expandindo descrição completa...")
                try:
                    await btn_desc.click(timeout=3000)
                    await asyncio.sleep(1)
                except:
                    pass
            
            # 4. VARRER TODA A PÁGINA (BOTÕES MASCARADOS) 
            # OLX usa spans clicáveis na descrição para esconder parte do número
            locators_to_try = [
                "[data-element='button_show-phone']",
                '//*[@id="description-title"]//span[@role="button"]',
                "//*[contains(translate(text(), 'VER NÚMERO', 'ver número'), 'ver número')]",
                "//*[contains(text(), 'ver número')]",
                "//*[contains(text(), '...')]"
            ]
            
            for loc in locators_to_try:
                try:
                    selector = loc if loc.startswith("[") else f"xpath={loc}"
                    elements = page.locator(selector)
                    count = await elements.count()
                    for i in range(count):
                        try:
                            # Verifica se o elemento é visível e tem texto antes de clicar
                            if await elements.nth(i).is_visible():
                                await elements.nth(i).click(timeout=2000, no_wait_after=True, force=True)
                                await asyncio.sleep(0.8)
                        except:
                            pass
                except:
                    pass
            
            # 5. LER TEXTO DA DESCRIÇÃO (Vários possíveis XPaths)
            # Incluindo o XPath específico enviado pelo usuário
            description_xpaths = [
                "//*[@id='description-title']/div/div[2]/div/span/span/span", # XPath enviado pelo usuário
                "[data-testid='ad-description']",
                '//*[@id="description-title"]/div/div[2]/div'
            ]
            
            all_texts = []
            for xpath in description_xpaths:
                loc = page.locator(xpath if xpath.startswith("[") else f"xpath={xpath}")
                if await loc.count() > 0:
                    txt = await loc.inner_text()
                    if txt: all_texts.append(txt)
            
            # Combina e extrai
            full_description_text = "\n".join(all_texts)
            if full_description_text:
                print("➡️ Analisando texto da descrição...")
                extra_tels = extract_phone_numbers(full_description_text)
                
                existentes_numeros = [t["telefone"] for t in dados["telefones"]]
                for ext in extra_tels:
                    if ext["telefone"] not in existentes_numeros:
                        ext["origem"] = "descricao"
                        dados["telefones"].append(ext)
                        existentes_numeros.append(ext["telefone"])
            
            await browser.close()
            print(f"✅ Extração finalizada: {len(dados['telefones'])} contatos.")
    
    except Exception as e:
        print(f"🚨 Erro na extração: {e}")
        dados["erro"] = str(e)
            
    return dados
    
if __name__ == "__main__":
    url_teste = "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/terrenos/oportunidade-de-terreno-com-linda-vista-da-represa-1476153411"
    async def teste_local():
        resultado = await extract_phones_from_olx(url_teste)
        print("\nResultado Final:")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    asyncio.run(teste_local())
