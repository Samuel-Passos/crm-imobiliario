import asyncio
import json
import os
import time
import datetime
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout

BASE_URL = "https://www.crecisp.gov.br"
OUTPUT_DIR = "/home/samuel/Desktop/Scraper_antigravity/creci_scraper/output"
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "progress.json")
CSV_FILE = os.path.join(OUTPUT_DIR, "imobiliarias_creci.csv")
import csv

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    
def get_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {
        "fase": "inicio",
        "fase_desc": "Iniciando",
        "total": 0, "feitos": 0, "pendentes": 0,
        "atual_nome": "", "atual_url": "",
        "aguardando_captcha": False,
        "ultima_atualizacao": "", "iniciado_em": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "log_recente": [],
        "ultima_salva": {}
    }

def update_progress(**kwargs):
    state = get_progress()
    for k, v in kwargs.items():
        state[k] = v
    state["ultima_atualizacao"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PROGRESS_FILE, "w") as f:
        json.dump(state, f, indent=4)
        
def add_log_progress(msg: str):
    state = get_progress()
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    state["log_recente"].insert(0, f"[{ts}] {msg}")
    state["log_recente"] = state["log_recente"][:10]
    update_progress(log_recente=state["log_recente"])
    log(msg)

def save_csv(row: dict):
    file_exists = os.path.exists(CSV_FILE)
    fieldnames = ["razao_social", "creci", "status", "nome_fantasia", "cnpj", "endereco", "cep", "email", "telefone", "responsavel_tecnico", "creci_responsavel", "coletado_em"]
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

async def _extract_registers(page: Page) -> list:
    registros = []
    forms = await page.query_selector_all("form[action*='detalhesimobiliaria']")
    for form in forms:
        input_reg = await form.query_selector("input[name='registerNumber']")
        if input_reg:
            val = await input_reg.get_attribute("value")
            if val and val not in registros:
                registros.append(val)
    return registros

async def _extract_last_page(page: Page) -> int:
    """Procura na paginacao qual e o maior numero de pagina disponivel."""
    max_page = 0
    for link in await page.query_selector_all(".pagination a[href*='page=']"):
        href = await link.get_attribute("href")
        if href and "page=" in href:
            try:
                num = int(href.split("page=")[-1])
                if num > max_page:
                    max_page = num
            except: pass
    return max_page

async def collect_all_registers(page: Page) -> list:
    add_log_progress("Iniciando coleta de registros na pagina atual...")
    all_registros = []
    
    # Extrai da pagina inicial
    reg = await _extract_registers(page)
    all_registros.extend(reg)
    add_log_progress(f"Pagina inicial (0): {len(reg)} registros.")
    
    # Descobre o total de paginas
    last_page = await _extract_last_page(page)
    add_log_progress(f"Paginacao: Total de {last_page + 1} paginas detectadas.")
    
    # Itera de 1 ate last_page
    for p_num in range(1, last_page + 1):
        url = f"{BASE_URL}/cidadao/listadeimobiliarias?page={p_num}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
            reg = await _extract_registers(page)
            all_registros.extend(reg)
            add_log_progress(f"  Pagina '{p_num}': +{len(reg)} registros.")
        except Exception as e:
            add_log_progress(f"  Erro na pagina {p_num}: {e}")
            
    # Remove duplicatas mantendo a ordem
    unique_regs = list(dict.fromkeys(all_registros))
    add_log_progress(f"Total unico de registros coletados: {len(unique_regs)}")
    return unique_regs

async def extrair_detalhes(page: Page, reg_number: str):
    row = {
        "razao_social": "", "creci": reg_number, "status": "", "nome_fantasia": "",
        "cnpj": "", "endereco": "", "cep": "", "email": "", "telefone": "",
        "responsavel_tecnico": "", "creci_responsavel": "",
        "coletado_em": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 1. Navegar via form POST
    js_code = f"""
    const form = document.createElement('form');
    form.method = 'post';
    form.action = 'https://www.crecisp.gov.br/cidadao/detalhesimobiliaria';
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'registerNumber';
    input.value = '{reg_number}';
    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    """
    
    async with page.expect_navigation(timeout=45000):
        await page.evaluate(js_code)
        
    await page.wait_for_timeout(2000)
    
    # 2. Extrair os campos visiveis (h1, divs)
    h1 = await page.query_selector("h1")
    if h1: row["razao_social"] = (await h1.inner_text()).strip()
    
    container = await page.query_selector(".main-container, main")
    if container:
        text = await container.inner_text()
        for line in text.splitlines():
            line = line.strip()
            if not line: continue
            ll = line.lower()
            if "status:" in ll: row["status"] = line.split(":", 1)[1].strip()
            elif "nome de fantasia:" in ll: row["nome_fantasia"] = line.split(":", 1)[1].strip()
            elif "cep:" in ll: row["cep"] = line.split(":", 1)[1].strip()
            elif "responsavel" in ll and ":" in ll and "creci" not in ll: row["responsavel_tecnico"] = line.split(":", 1)[1].strip()
            elif "creci :" in ll or "creci:" in ll and row["responsavel_tecnico"]: row["creci_responsavel"] = line.split(":", 1)[1].strip()

    # 3. Clicar nos olhos para revelar dados mascarados (um por um)
    eyes = await page.query_selector_all("button[onclick*='openCaptchaModal']")
    if eyes:
        add_log_progress(f"Encontrados {len(eyes)} campos mascarados. Resolvendo um por um...")
        for eye in eyes:
            try:
                # Verifica se o campo ja foi revelado (o botao some apos revelar)
                if not await eye.is_visible():
                    continue
                    
                # Usar evaluate(click) em vez de native click evita roubo de foco no Linux/GNOME
                await eye.evaluate("node => node.click()")
                await page.wait_for_timeout(1000)
                
                # Verifica se abriu o modal do CAPTCHA
                captcha_modal = await page.query_selector("iframe[src*='recaptcha']")
                if captcha_modal and await captcha_modal.is_visible():
                    add_log_progress("CAPTCHA detectado! Acionando a API 2Captcha...")
                    update_progress(aguardando_captcha=True)
                    
                    # Chama o 2captcha enviando nossa sitekey
                    import sys
                    sys.path.append("/home/samuel/Desktop/Scraper_antigravity/scraper")
                    from solve_captcha import solve_recaptcha
                    
                    token = solve_recaptcha(page.url)
                    if token:
                        add_log_progress("Token do 2Captcha recebido! Injetando no navegador...")
                        # Injeta o token
                        await page.evaluate(f"document.getElementById('g-recaptcha-response').innerHTML = '{token}';")
                        
                        # Tenta encontrar o botão confirmar do modal e clica via JS (sem roubo de foco)
                        btn_confirm = await page.query_selector("#confirmCaptchaBtn")
                        if btn_confirm:
                            await btn_confirm.evaluate("node => node.click()")
                        else:
                            # Tenta forcar pelo JS
                            await page.evaluate("confirmCaptcha('realestate')")
                            
                        add_log_progress("CAPTCHA resolvido com sucesso pelo robô!")
                    else:
                        add_log_progress("Falha na API 2Captcha. Pulando este campo.")
                        
                    # Aguarda o modal sumir e atualizar a pagina com o dado
                    await page.wait_for_timeout(2500)
                    update_progress(aguardando_captcha=False)
                    
                # Aguarda o AJAX atualizar a pagina com o dado (caso não houvesse captcha)
                await page.wait_for_timeout(1000)
            except Exception as e:
                add_log_progress(f"Erro ao clicar/resolver olho: {e}")
            
    # Extrair os spans revelados (agora todos estarao destrancados se o operador resolveu)
    cnpj_el = await page.query_selector("#cnpjInfo")
    if cnpj_el: row["cnpj"] = (await cnpj_el.inner_text()).strip().replace("*", "")
    
    addr_el = await page.query_selector("#addressInfo")
    if addr_el: row["endereco"] = (await addr_el.inner_text()).strip().replace("*", "")
    
    email_el = await page.query_selector("#primaryEmail")
    if email_el: row["email"] = (await email_el.inner_text()).strip().replace("*", "")
    
    # Telefones podem ter multiplos spans
    phones = await page.query_selector_all(".phonesListItem")
    if phones:
        pls = []
        for p in phones:
            pt = (await p.inner_text()).strip().replace("*", "")
            if pt: pls.append(pt)
        row["telefone"] = " / ".join(pls)
        
    return row

async def main():
    print("======================================================")
    print("  CRECI-SP Scraper — Human-in-the-Loop (CDP Connect)")
    print("======================================================")
    
    # Carrega ou inicializa o json com os all_registros
    state = get_progress()
    all_registros = state.get("todos_registros", [])
    
    async with async_playwright() as pw:
        add_log_progress("Conectando ao seu Chrome (porta 9222)...")
        try:
            browser = await pw.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            add_log_progress(f"ERRO: Nao foi possivel conectar ao Chrome. Erro: {e}")
            return
            
        context = browser.contexts[0]
        
        # Pega a pagina ativa se ja estiver na lista, senao abre nova
        pages = context.pages
        page = None
        for p in pages:
            if "listadeimobiliarias" in p.url:
                page = p
                break
                
        if not page:
            page = await context.new_page()
            add_log_progress("Navegando para o portal do CRECI (buscarporimobiliaria)...")
            await page.goto(f"{BASE_URL}/cidadao/buscarporimobiliaria")
            add_log_progress("ATENCAO: Faca a busca de SAO JOSE DOS CAMPOS manualmente no navegador.")
            add_log_progress("Aguardando voce chegar na lista de imobiliarias...")
            
            try:
                await page.wait_for_url("**/listadeimobiliarias**", timeout=300000)
            except PlaywrightTimeout:
                add_log_progress("Timeout aguardando a lista. Tente rodar o script novamente.")
                return
                
        # FASE 2: Coletar os registros
        if not all_registros:
            update_progress(fase="coleta_links", fase_desc="Coletando CRECIs de todas as paginas")
            all_registros = await collect_all_registers(page)
            update_progress(todos_registros=all_registros, total=len(all_registros))
            
        # FASE 3: Extrair Dados
        total = len(all_registros)
        feitos = state.get("feitos", 0)
        
        update_progress(fase="extracao", fase_desc="Extraindo dados detalhados")
        
        # Cria uma nova aba para as extrações para nao perder a lista original
        detalhes_page = await context.new_page()
        add_log_progress("Preparando aba de extracao...")
        await detalhes_page.goto(BASE_URL)
        
        for idx in range(feitos, total):
            reg = all_registros[idx]
            update_progress(atual_nome=f"CRECI {reg}", atual_url=f"POST {reg}", feitos=idx, pendentes=total-idx)
            
            row = await extrair_detalhes(detalhes_page, reg)
            save_csv(row)
            
            log(f"Salvo: {row['razao_social']} ({reg})")
            update_progress(ultima_salva={"nome": row["razao_social"], "creci": reg, "coletado_em": row["coletado_em"]})
            
            update_progress(feitos=idx+1, pendentes=total-(idx+1))
            
        await detalhes_page.close()
        add_log_progress("Extracao concluida com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
