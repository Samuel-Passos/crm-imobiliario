import subprocess
import os

VENV_PYTHON = "scraper/.venv/bin/python"

print("\n" + "=" * 60)
print("🧪 TESTE RÁPIDO - 1 ITEM POR FASE")
print("=" * 60)

# FASE 1
print("\n[1/4] Coletando Links (Máximo de 1 página)")
subprocess.run([VENV_PYTHON, "olx_captacao/fase1_coleta_links.py", "--max-paginas", "1"])

# FASE 2
print("\n[2/4] Extraindo Dados (Lote de 1 item)")
subprocess.run([VENV_PYTHON, "olx_captacao/fase2_extrai_dados.py", "--lote", "1"])

# FASE 2.5
print("\n[3/4] Filtrando Profissionais")
subprocess.run([VENV_PYTHON, "olx_captacao/fase2_5_filtro_mercado.py"])

# FASE 3
print("\n[4/4] Extraindo Telefone (Lote de 1 item via Servidor)")
import urllib.request
import urllib.error
try:
    url = "http://localhost:8765/extract-phone/batch?lote=1"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req) as response:
        print(f"✅ FASE 3 ACIONADA NO SERVIDOR COM SUCESSO (Status: {response.status})")
except Exception as e:
    print(f"❌ Erro ao acionar servidor (ele está rodando?): {e}")

print("\n🎉 TESTE CONCLUÍDO!")
