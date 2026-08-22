import subprocess
import sys
import os
import urllib.request
import urllib.error

# Caminho para o ambiente virtual de Python que o projeto usa
VENV_PYTHON = "scraper/.venv/bin/python"

from dotenv import load_dotenv

# Carrega as configurações do arquivo .env central
load_dotenv(os.path.join("scraper", ".env"))

# =============================================================================
# ⚙️ CONFIGURAÇÕES DE LOTE (Puxando do arquivo scraper/.env)
# =============================================================================

LOTE_FASE2 = int(os.getenv("LOTE_FASE2", 50))
LOTE_FASE3 = int(os.getenv("LOTE_FASE3", 50))
LOTE_CHAT = int(os.getenv("LOTE_CHAT", 50))
# =============================================================================

def executar_script(nome_etapa, caminho_script):
    """Executa um script de forma isolada e aguarda ele terminar."""
    print("=" * 60)
    print(f"🚀 INICIANDO ETAPA: {nome_etapa}")
    print(f"Executando: {caminho_script}")
    print("=" * 60)
    
    try:
        # Chama o processo e espera (stream da saída direto para o console)
        args = caminho_script.split()
        resultado = subprocess.run([VENV_PYTHON] + args, check=False)
        
        if resultado.returncode == 0:
            print(f"\n✅ {nome_etapa} FINALIZADA COM SUCESSO!\n")
        else:
            print(f"\n⚠️ {nome_etapa} TEVE UM AVISO OU ERRO (Código: {resultado.returncode}). Continuando a esteira...\n")
            
    except Exception as e:
        print(f"\n❌ ERRO FATAL AO TENTAR EXECUTAR {nome_etapa}: {e}\n")

def executar_geocodificador():
    """O Geocodificador do Google Maps é uma função dentro de um script, então o chamamos via Python inline."""
    nome_etapa = "GOOGLE MAPS (GEOCODIFICADOR)"
    print("=" * 60)
    print(f"🌍 INICIANDO ETAPA: {nome_etapa}")
    print("=" * 60)
    
    comando_python = """
import sys
import os
sys.path.append('scraper')
from dotenv import load_dotenv
load_dotenv(os.path.join('scraper', '.env'))
from tools.geocoder import main
main()
    """
    
    try:
        resultado = subprocess.run([VENV_PYTHON, "-c", comando_python], check=False)
        if resultado.returncode == 0:
            print(f"\n✅ {nome_etapa} FINALIZADA COM SUCESSO!\n")
        else:
            print(f"\n⚠️ {nome_etapa} TEVE UM AVISO OU ERRO. Continuando a esteira...\n")
    except Exception as e:
        print(f"\n❌ ERRO FATAL AO EXECUTAR MAPS: {e}\n")

def executar_extracao_telefone(lote=10):
    """Aciona a extração de telefone em lote via endpoint do servidor, reaproveitando o navegador persistente."""
    nome_etapa = "FASE 3 (EXTRAÇÃO DE TELEFONE VIA BACKEND)"
    print("=" * 60)
    print(f"📱 INICIANDO ETAPA: {nome_etapa}")
    print("=" * 60)
    
    url = f"http://localhost:8765/extract-phone/batch?lote={lote}"
    try:
        req = urllib.request.Request(url, method="POST")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print(f"\n✅ {nome_etapa} INICIADA COM SUCESSO NO SERVIDOR!\n")
            else:
                print(f"\n⚠️ {nome_etapa} RETORNOU STATUS {response.status}. Continuando...\n")
    except urllib.error.URLError as e:
        print(f"\n❌ ERRO AO ACIONAR {nome_etapa}: Servidor backend não está rodando? {e}\n")
    except Exception as e:
        print(f"\n❌ ERRO FATAL EM {nome_etapa}: {e}\n")

def run_gerente_geral():
    print("\n" + "★" * 60)
    print("👔 BEM-VINDO AO GERENTE GERAL DO SISTEMA")
    print("Orquestrando a esteira completa de captação e relacionamento.")
    print("★" * 60 + "\n")
    
    # 0. Varre a Caixa de Entrada da OLX em busca de respostas tardias
    executar_script("SCANNER DE INBOX (RESPOSTAS)", "robo_chat_prospeccao/scanner_inbox.py")

    # 1. Libera o funil enviando mensagens (Onda Reversa)
    executar_script("ONDA REVERSA (CHAT)", f"robo_chat_prospeccao/orquestrador_reverso.py --lote {LOTE_CHAT}")
    
    # 2. Raspa novos links na OLX
    executar_script("FASE 1 (COLETA DE LINKS OLX)", "olx_captacao/fase1_coleta_links.py")
    
    # 3. Pega detalhes dos imóveis novos
    executar_script("FASE 2 (EXTRAÇÃO DE DADOS OLX)", f"olx_captacao/fase2_extrai_dados.py --lote {LOTE_FASE2}")
    
    # 4. Remove corretores da Caixa de Entrada
    executar_script("FASE 2.5 (FILTRO DE PROFISSIONAIS)", "olx_captacao/fase2_5_filtro_mercado.py")
    
    # 5. Acha a Latitude/Longitude no Google Maps para os sobreviventes
    executar_geocodificador()
    
    # 6. Extrai o Telefone em Lote dos sobreviventes
    # Usando o endpoint do backend para reaproveitar a página persistente do Workspace 2
    executar_extracao_telefone(lote=LOTE_FASE3)
    
    print("\n" + "★" * 60)
    print("🏁 ESTEIRA COMPLETA FINALIZADA COM SUCESSO!")
    print("O funil andou e a Caixa de Entrada está abastecida e limpa!")
    print("★" * 60 + "\n")

if __name__ == "__main__":
    # Garante que o script seja rodado da raiz (Scraper_antigravity)
    if not os.path.exists("scraper"):
        print("Erro: Você deve executar o gerente_geral.py a partir da pasta raiz (Scraper_antigravity).")
        sys.exit(1)
        
    run_gerente_geral()
