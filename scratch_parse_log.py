import re

log_path = "/home/samuel/.gemini/antigravity-ide/brain/3ed601ae-8b1e-4342-9247-ae982dd9f1e3/.system_generated/tasks/task-813.log"

with open(log_path, 'r') as f:
    lines = f.readlines()

stats = {
    "mensagens_enviadas": 0,
    "expirados_script_1": 0,
    "expirados_script_2": 0,
    "expirados_script_3": 0,
    "expirados_extracao": 0,
    "telefones_encontrados": 0,
    "telefones_nao_encontrados": 0,
    "inconsistencias": 0,
    "anuncios_mercado": 0, # Fase 2.5
    "geocoder_sucesso": 0
}

current_kanban = None

for line in lines:
    # Rastrea Kanban atual
    if "PROCESSANDO ONDA:" in line:
        current_kanban = line.split("PROCESSANDO ONDA:")[1].strip()
        
    # Mensagens enviadas
    if "Mensagem enviada com sucesso" in line or "Primeiro contato enviado via botão" in line:
        stats["mensagens_enviadas"] += 1
        
    # Expirados
    if "Anúncio expirado ou indisponível" in line or "Movendo para Expirados" in line:
        if current_kanban == "Script 1": stats["expirados_script_1"] += 1
        elif current_kanban == "Script 2": stats["expirados_script_2"] += 1
        elif current_kanban == "Script 3": stats["expirados_script_3"] += 1
        elif current_kanban == "Extração de Telefone": stats["expirados_extracao"] += 1
        
    # Inconsistências (Erros)
    if "ERRO" in line or "Erro" in line or "Falha" in line:
        if "Movendo para Expirados" not in line:  # Ignora "Falha ao abrir chat" que foi tratado
            stats["inconsistencias"] += 1
            
    # Fase 2.5
    if "Deduzido como profissional" in line or "Marcado pela OLX como Profissional" in line:
        stats["anuncios_mercado"] += 1

print("=== STATS ===")
for k, v in stats.items():
    print(f"{k}: {v}")

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
sup = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# O último lote era de 50 anúncios. Vamos checar os últimos 50 pesquisados.
res = sup.table("imoveis").select("id, telefones_extraidos").eq("telefone_pesquisado", True).order("id", desc=True).limit(50).execute()

achou = 0
nao_achou = 0

for im in res.data:
    tels = im.get("telefones_extraidos") or []
    if len(tels) > 0:
        achou += 1
    else:
        nao_achou += 1

print("=== FASE 3 (TELEFONES) ===")
print(f"Achou telefone: {achou}")
print(f"Nao achou: {nao_achou}")
