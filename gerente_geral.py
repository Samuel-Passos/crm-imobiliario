import subprocess
import sys
import os

# Caminho para o ambiente virtual de Python que o projeto usa
VENV_PYTHON = "scraper/.venv/bin/python"

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
import asyncio
import sys
sys.path.append('scraper')
from tools.geocoder_maps_scraper import main
asyncio.run(main())
    """
    
    try:
        resultado = subprocess.run([VENV_PYTHON, "-c", comando_python], check=False)
        if resultado.returncode == 0:
            print(f"\n✅ {nome_etapa} FINALIZADA COM SUCESSO!\n")
        else:
            print(f"\n⚠️ {nome_etapa} TEVE UM AVISO OU ERRO. Continuando a esteira...\n")
    except Exception as e:
        print(f"\n❌ ERRO FATAL AO EXECUTAR MAPS: {e}\n")

def run_gerente_geral():
    print("\n" + "★" * 60)
    print("👔 BEM-VINDO AO GERENTE GERAL DO SISTEMA")
    print("Orquestrando a esteira completa de captação e relacionamento.")
    print("★" * 60 + "\n")
    
    # 1. Libera o funil enviando mensagens (Onda Reversa)
    executar_script("ONDA REVERSA (CHAT)", "robo_chat_prospeccao/orquestrador_reverso.py")
    
    # 2. Raspa novos links na OLX
    executar_script("FASE 1 (COLETA DE LINKS OLX)", "olx_captacao/fase1_coleta_links.py")
    
    # 3. Pega detalhes dos imóveis novos
    executar_script("FASE 2 (EXTRAÇÃO DE DADOS OLX)", "olx_captacao/fase2_extrai_dados.py")
    
    # 4. Remove corretores da Caixa de Entrada
    executar_script("FASE 2.5 (FILTRO DE PROFISSIONAIS)", "olx_captacao/fase2_5_filtro_mercado.py")
    
    # 5. Acha a Latitude/Longitude no Google Maps para os sobreviventes
    executar_geocodificador()
    
    # 6. Extrai o Telefone em Lote dos sobreviventes
    # Usando limite conservador por padrão (ex: 10), mas isso pode ser alterado
    executar_script("FASE 3 (EXTRAÇÃO DE TELEFONE)", "olx_captacao/fase3_extrai_telefone_em_lote.py --lote 10")
    
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
