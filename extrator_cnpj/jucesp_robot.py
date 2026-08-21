import os
import sys
import time
import json
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader
from datetime import datetime

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("JucespRobot")

def extrair_texto_pdf(pdf_path):
    """Lê o PDF e retorna o texto extraído."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        log.error(f"Erro ao ler PDF: {e}")
        return ""

def salvar_no_supabase(cnpj, novas_notas):
    """Salva os dados extraídos no campo notas_investigacao do Supabase."""
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        
        # Carrega env
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        client = create_client(url, key)
        
        # 1. Busca notas atuais
        res = client.table("empresas_sjc").select("notas_investigacao").eq("cnpj", cnpj).execute()
        notas_atuais = ""
        if res.data:
            notas_atuais = res.data[0].get("notas_investigacao") or ""
            
        # 2. Concatena
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        separador = "\n\n" if notas_atuais else ""
        notas_finais = f"{notas_atuais}{separador}--- 🤖 EXTRAÇÃO JUCESP ({timestamp}) ---\n{novas_notas}"
        
        # 3. Update
        client.table("empresas_sjc").update({"notas_investigacao": notas_finais}).eq("cnpj", cnpj).execute()
        log.info(f"✅ Notas do CNPJ {cnpj} atualizadas via PDF JUCESP.")
        return True
    except Exception as e:
        log.error(f"Erro ao salvar no Supabase: {e}")
        return False

def rodar_automacao_jucesp(cnpj):
    """
    Fluxo: Abre JUCESP -> Espera Login -> Busca CNPJ -> Baixa PDF -> Processa.
    """
    cnpj_limpo = str(cnpj).replace(".", "").replace("/", "").replace("-", "")
    output_dir = Path(__file__).parent / "output" / "pdfs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        log.info("🚀 Iniciando Navegador em MODO CAMALEÃO (Ultimate Stealth)...")
        
        # Pasta para salvar login/cookies
        user_data_dir = Path(__file__).parent / "output" / "browser_session"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Abre navegador modo persistente
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            channel="chrome", 
            headless=False,
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            args=[
                "--start-maximized",
                "--no-sandbox",
                "--disable-infobars"
            ]
        )

        page = context.new_page()
        
        # 1. Ir para o Portal JUCESP
        log.info("🌐 Abrindo o Portal JUCESP...")
        try:
            page.goto("https://www.jucesponline.sp.gov.br/", wait_until="domcontentloaded", timeout=60000)
            log.info("📢 Portal aberto. Por favor, faça o Login Gov.br no navegador.")
        except Exception as e:
            log.warning(f"⚠️ Aviso no carregamento inicial: {e}. Tentando prosseguir...")
        
        log.info("⚠️ AGUARDANDO LOGIN NO NAVEGADOR (Janela aberta)...")
        
        # Espera o usuário logar (detecta por múltiplos possíveis seletores de saída)
        try:
            page.wait_for_function("""
                () => document.body.innerText.includes('Sair') || 
                      document.body.innerText.includes('Logoff') ||
                      document.querySelector('a[href*="Logoff"]') !== null
            """, timeout=300000) 
            log.info("✅ Login detectado com sucesso! Iniciando sequência de busca...")
        except Exception as e:
            log.error(f"❌ Falha ao aguardar o login: {e}")
            context.close()
            return {"ok": False, "msg": "Login não detectado (Timeout)."}

        # 2. Busca Automática (Baseada nos XPaths do Usuário)
        try:
            log.info(f"🔍 Buscando CNPJ: {cnpj_limpo}...")
            page.goto("https://www.jucesponline.sp.gov.br/Default.aspx")
            
            # Preencher CNPJ
            page.wait_for_selector('//*[@id="ctl00_cphContent_frmBuscaSimples_txtPalavraChave"]', timeout=30000)
            page.fill('//*[@id="ctl00_cphContent_frmBuscaSimples_txtPalavraChave"]', cnpj_limpo)
            log.info("Submetendo formulário de busca...")
            page.click('//*[@id="ctl00_cphContent_frmBuscaSimples_btPesquisar"]')
            
            # Clicar no primeiro NIRE da lista
            log.info("Selecionando empresa na lista de resultados...")
            page.wait_for_selector('//*[@id="ctl00_cphContent_gdvResultadoBusca_gdvContent_ctl02_lbtSelecionar"]')
            page.click('//*[@id="ctl00_cphContent_gdvResultadoBusca_gdvContent_ctl02_lbtSelecionar"]')
            
            # Selecionar "Simplificada" e Emitir
            log.info("Emitindo Ficha Cadastral...")
            page.wait_for_selector('//*[@id="ctl00_cphContent_frmPreVisualiza_rblTipoDocumento_0"]')
            page.check('//*[@id="ctl00_cphContent_frmPreVisualiza_rblTipoDocumento_0"]')
            
            # Lida com o Download
            with page.expect_download() as download_info:
                page.click('//*[@id="ctl00_cphContent_frmPreVisualiza_btnEmitir"]')
            
            download = download_info.value
            pdf_path = output_dir / f"jucesp_{cnpj_limpo}_{int(time.time())}.pdf"
            download.save_as(pdf_path)
            log.info(f"📥 PDF baixado: {pdf_path}")

            # 3. Processar PDF
            log.info("📄 Lendo PDF e extraindo inteligência...")
            texto = extrair_texto_pdf(pdf_path)
            if texto:
                resumo = texto.strip()[:2000] 
                salvar_no_supabase(cnpj, resumo)
                context.close()
                return {"ok": True, "msg": "PDF processado e anexado ao lead!"}
            else:
                context.close()
                return {"ok": False, "msg": "Falha ao extrair texto do PDF."}

        except Exception as e:
            log.error(f"Erro na navegação automática: {e}")
            time.sleep(5)
            context.close()
            return {"ok": False, "msg": f"Erro na automação: {str(e)}"}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        rodar_automacao_jucesp(sys.argv[1])
    else:
        print("Uso: python jucesp_robot.py <CNPJ>")
