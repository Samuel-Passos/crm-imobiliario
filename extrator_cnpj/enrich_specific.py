import os
import requests
import json
import re
from pipeline import _consultar_cnpj_api, step6_salvar_supabase
import pandas as pd

target_cnpj = "18224975000169"
print(f"Enriquecendo CNPJ: {target_cnpj}")

dados = _consultar_cnpj_api(target_cnpj)
if dados:
    row_dict = {
        "cnpj": target_cnpj,
        "whatsapp": "", # Mantém o que tiver
        "score": 5,
        "status": "enriquecido_ok"
    }
    
    # Inteligência de Sócios (OSINT)
    socios_raw = dados.get("qsa", [])
    nomes = [s.get("nome_socio", "") for s in socios_raw]
    row_dict["socios"] = " | ".join(n for n in nomes if n)
    qsa_limitado = []
    for s in socios_raw:
        qsa_limitado.append({
            "nome": s.get("nome_socio"),
            "cpf": s.get("cnpj_cpf_do_socio"),
            "qualificacao": s.get("qualificacao_socio"),
            "entrada": s.get("data_entrada_sociedade")
        })
    row_dict["qsa_completo"] = json.dumps(qsa_limitado)
    row_dict["responsavel_qualificacao"] = dados.get("qualificacao_do_responsavel", "Não informada")
    
    # Salvar em CSV temporário para o step6
    df = pd.DataFrame([row_dict])
    df.to_csv("extrator_cnpj/output/google_maps_enriched.csv", index=False)
    
    from pipeline import step6_salvar_supabase
    step6_salvar_supabase()
    print("Sucesso!")
else:
    print("Falha ao consultar API.")
