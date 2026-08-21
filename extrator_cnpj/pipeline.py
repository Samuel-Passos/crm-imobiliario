"""
============================================================
EXTRATOR DE CNPJ — PIPELINE DE PROSPECÇÃO
Baseado no plano de São José dos Campos (SJC)
============================================================
"""

import os
import re
import csv
import time
import json
import logging
import argparse
import asyncio
import requests
import subprocess
import pandas as pd
from supabase import create_client
from tqdm import tqdm
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Carrega o .env da pasta raiz ou da pasta atual
env_path = Path(__file__).parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / "scraper" / ".env"
load_dotenv(env_path)

# Tenta carregar BRASILIO_TOKEN do user_config.json (configurações do CRM)
config_json = Path(__file__).parent.parent / "robo_disponibilidade" / "user_config.json"
BRASILIO_TOKEN = os.getenv("BRASILIO_TOKEN", "")

if config_json.exists():
    try:
        with open(config_json, "r") as f:
            user_config = json.load(f)
            if "BRASILIO_TOKEN" in user_config and user_config["BRASILIO_TOKEN"]:
                BRASILIO_TOKEN = user_config["BRASILIO_TOKEN"]
    except Exception as e: log.error(f"  API Exception: {e}")

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────

VENV_PYTHON = Path(__file__).parent / ".venv" / "bin" / "python3"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path("python3") # Fallback

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
SUPABASE_URL        = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY        = os.getenv("SUPABASE_KEY", "")
USE_SUPABASE        = bool(SUPABASE_URL and SUPABASE_KEY)

OUTPUT_DIR  = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

BASE_CNPJ_CSV    = OUTPUT_DIR / "01_base_raw.csv"
FILTRADO_CSV     = OUTPUT_DIR / "02_filtrado.csv"
ENRICH_CNPJ_CSV  = OUTPUT_DIR / "03_enrich_opencnpj.csv"
ENRICH_MAPS_CSV  = OUTPUT_DIR / "04_enrich_maps.csv"
FINAL_CSV        = OUTPUT_DIR / "05_final_com_whatsapp.csv"

# CNAEs relevantes para prospecção imobiliária (Default)
CNAES_ALVO = {
    "6810201": "Compra e venda de imóveis",
    "6810202": "Aluguel de imóveis",
    "6821801": "Administração de imóveis",
    "6822600": "Avaliação de imóveis",
    "6811400": "Incorporação imobiliária",
    "4120400": "Construção de edifícios",
    "4221904": "Construção de redes",
    "8112500": "Condomínio predial (gestão)",
}

# Natureza jurídica de condomínios edilícios
NATUREZAS_CONDOMINIO = {"2054", "3085"}

# Para o Teste de Condomínios e Associações
CNAES_CONDO = {"8112500", "6822600", "9499500"}
NATUREZAS_CONDO = {"2054", "3085", "3999"}
KEYWORDS_CONDO = ["MORADORES", "LOTEAMENTO", "RESIDENCIAL", "PROPRIETARIOS", "VIVENDAS", "CONDOMINIO", "EDIFICIO", "VILLAGE", "CHACARAS"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "pipeline.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# AUXILIAR: PROGRESS TRACKING
# ─────────────────────────────────────────────

STATUS_FILE = OUTPUT_DIR / "current_status.json"

def update_status(step, progress, msg, details=None):
    status = {
        "last_step": step,
        "progress": progress,
        "message": msg,
        "details": details or {},
        "stats": get_stats(),
        "updated_at": datetime.now().isoformat()
    }
    STATUS_FILE.write_text(json.dumps(status, indent=2))

def get_stats():
    """Calcula estatísticas rápidas da base atual."""
    stats = {
        "total": 0, 
        "whatsapp": 0, 
        "website": 0, 
        "email": 0,
        "opencnpj_ok": 0,
        "maps_ok": 0,
        "scraping_ok": 0
    }
    
    # Prioritiza o arquivo mais avançado que existir
    target = None
    if FINAL_CSV.exists(): target = FINAL_CSV
    elif ENRICH_MAPS_CSV.exists(): target = ENRICH_MAPS_CSV
    elif ENRICH_CNPJ_CSV.exists(): target = ENRICH_CNPJ_CSV
    elif FILTRADO_CSV.exists(): target = FILTRADO_CSV
    
    if target:
        try:
            df = pd.read_csv(target, dtype=str)
            stats["total"] = len(df)
            
            # Limpeza de colunas para contagem precisa
            def count_filled(col_name):
                if col_name not in df.columns: return 0
                return int(df[col_name].apply(lambda x: str(x).strip() if pd.notna(x) else "").apply(lambda x: x not in ["", "nan", "None", "[]"]).sum())

            stats["whatsapp"] = count_filled("whatsapp")
            stats["email"] = count_filled("email") + count_filled("email_site")
            
            # Website: Soma site oficial e site do Google
            stats["website"] = count_filled("site") + count_filled("site_google")
            
            # Sócios: Contamos se a coluna 'socios' tiver conteúdo
            stats["opencnpj_ok"] = count_filled("socios")
            
            if "status" in df.columns:
                counts = df["status"].value_counts()
                stats["maps_ok"] = int(counts.get("maps_ok", 0))
                if FINAL_CSV.exists():
                    stats["scraping_ok"] = len(df)
        except Exception as e: log.error(f"  API Exception: {e}")
    return stats

# ─────────────────────────────────────────────
# PASSO 0 — BAIXAR DUMPS (SE NECESSÁRIO)
# ─────────────────────────────────────────────

def step0_download_dumps():
    log.info("=== PASSO 0: Verificando/Baixando Dumps da Receita Federal ===")
    update_status(0, 0, "Baixando dumps da Receita Federal (Mirror Brasil.io)...")
    
    script_fetch = Path(__file__).parent / "fetch_dump.py"
    try:
        subprocess.run([str(VENV_PYTHON), str(script_fetch)], check=True)
        update_status(0, 100, "Downloads concluídos.")
    except Exception as e:
        log.error(f"Erro ao baixar dumps: {e}")
        raise

# ─────────────────────────────────────────────
# PASSO 1 — EXTRAÇÃO FILTRADA DO DUMP
# ─────────────────────────────────────────────

def step1_extrair_do_dump(municipio: str, limit: int = 0, all_cnaes: bool = False, test_condo: bool = False):
    log.info(f"=== PASSO 1: Extraindo dados para {municipio} do dump local ===")
    
    # Caminhos
    repo_path = Path(__file__).parent.parent / "socios-brasil"
    extract_script = repo_path / "extract_dump.py"
    download_dir = repo_path / "data" / "download"
    output_temp_dir = repo_path / "data" / "output_temp"
    output_temp_dir.mkdir(parents=True, exist_ok=True)

    # Identifica arquivos ZIP
    zips = sorted(list(download_dir.glob("DADOS_ABERTOS_CNPJ_*.zip")))
    if not zips:
        log.error("Nenhum arquivo de dump encontrado em data/download. Rode o Passo 0.")
        return

    # Limpa arquivo base anterior
    if BASE_CNPJ_CSV.exists():
        BASE_CNPJ_CSV.unlink()

    total_zips = len(zips)
    for i, zip_file in enumerate(zips):
        progress_val = int(((i) / total_zips) * 100)
        msg = f"Lendo arquivo {i+1}/{total_zips}: {zip_file.name}..."
        log.info(f"[{i+1}/{total_zips}] {msg}")
        update_status(1, progress_val, msg, {"current": i+1, "total": total_zips})

        # Comando para ESTE arquivo específico
        cmd = [
            str(VENV_PYTHON), str(extract_script),
            str(output_temp_dir),
            str(zip_file),
            "--city", municipio,
            "--no_censorship", # Habilita e-mails e outros campos úteis para B2B
        ]
        
        if test_condo:
            cmd.extend(["--cnaes", ",".join(CNAES_CONDO)])
        elif not all_cnaes:
            cmd.extend(["--cnaes", ",".join(CNAES_ALVO.keys())])

        try:
            # Roda a extração para este arquivo
            subprocess.run(cmd, check=True, cwd=str(repo_path))
            
            # O script gera arquivo empresa.csv.gz no output_temp_dir
            empresa_csv_gz = output_temp_dir / "empresa.csv.gz"
            
            if empresa_csv_gz.exists():
                import gzip
                import shutil
                # Modo 'ab' (append binary). Se for o primeiro arquivo, cria ('wb').
                mode = 'wb' if i == 0 else 'ab'
                
                with gzip.open(empresa_csv_gz, 'rb') as f_in:
                    # Se não for o primeiro arquivo, precisamos pular o cabeçalho
                    if i > 0:
                        f_in.readline() # Pula a primeira linha (header)
                    
                    with open(BASE_CNPJ_CSV, mode) as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Opcional: remover o arquivo temporário para economizar espaço
                empresa_csv_gz.unlink()

        except subprocess.CalledProcessError as e:
            log.error(f"Erro na execução do extract_dump.py para {zip_file.name}: {e}")
            raise

    log.info(f"✓ Extração total finalizada. Dados em {BASE_CNPJ_CSV}")
    update_status(1, 100, f"Extração concluída com sucesso ({total_zips} arquivos processados).")


# ─────────────────────────────────────────────
# PASSO 2 — FILTRAR E LIMPAR
# ─────────────────────────────────────────────

def step2_filtrar(municipio: str, incluir_condominios: bool = True, all_cnaes: bool = False, test_condo: bool = False):
    log.info("=== PASSO 2: Filtrando e normalizando base ===")
    update_status(2, 20, "Filtrando registros...")

    # Lista completa de campos conforme empresa.csv headers (total 35 campos úteis)
    RAW_COLS = [
        "cnpj", "identificador_matriz_filial", "razao_social", "nome_fantasia", 
        "situacao_cadastral", "data_situacao_cadastral", "motivo_situacao_cadastral", 
        "nome_cidade_exterior", "codigo_pais", "nome_pais", "codigo_natureza_juridica", 
        "data_inicio_atividade", "cnae_fiscal", "descricao_tipo_logradouro", 
        "logradouro", "numero", "complemento", "bairro", "cep", "uf", 
        "codigo_municipio", "municipio", "ddd_telefone_1", "ddd_telefone_2", 
        "ddd_fax", "correio_eletronico", "qualificacao_do_responsavel", 
        "capital_social", "porte", "opcao_pelo_simples", "data_opcao_pelo_simples", 
        "data_exclusao_do_simples", "opcao_pelo_mei", "situacao_especial", 
        "data_situacao_especial"
    ]

    try:
        # Tenta ler a primeira linha para ver se é cabeçalho ou dados
        first_line = pd.read_csv(BASE_CNPJ_CSV, nrows=1, header=None).iloc[0,0]
        has_header = str(first_line).lower() == "cnpj"
    except Exception:
        has_header = False

    if has_header:
        df = pd.read_csv(BASE_CNPJ_CSV, dtype=str, low_memory=False)
    else:
        df = pd.read_csv(BASE_CNPJ_CSV, dtype=str, low_memory=False, names=RAW_COLS, header=None)

    log.info(f"Registros carregados: {len(df):,}")

    df.columns = df.columns.str.lower().str.strip()

    col_map = {
        "cnpj": "cnpj",
        "razao_social": "razao_social",
        "nome_fantasia": "nome_fantasia",
        "cnae_fiscal": "cnae",
        "codigo_natureza_juridica": "natureza_juridica",
        "situacao_cadastral": "situacao_cadastral",
        "logradouro": "logradouro",
        "numero": "numero",
        "bairro": "bairro",
        "municipio": "municipio_import",
        "uf": "uf",
        "cep": "cep",
        "ddd_telefone_1": "ddd1",
        "ddd_telefone_2": "ddd2",
        "correio_eletronico": "email",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Remove duplicatas que possam ter sido geradas por execuções simultâneas
    if "cnpj" in df.columns:
        df = df.drop_duplicates(subset=["cnpj"])
        log.info(f"Registros após remover duplicatas: {len(df):,}")

    # Filtro situação ativa (02 = ATIVA na RF)
    if "situacao_cadastral" in df.columns:
        df = df[df["situacao_cadastral"].isin(["02", "2"])]
    
    # Filtro CNAE + condomínios
    if test_condo:
        log.info("  Aplicando filtros específicos de CONDOMÍNIOS e ASSOCIAÇÕES...")
        # Máscara básica por código
        mask_cnae = df.get("cnae", pd.Series(dtype=str)).isin(CNAES_CONDO)
        mask_natureza = df.get("natureza_juridica", pd.Series(dtype=str)).isin(NATUREZAS_CONDO)
        
        # Filtro de texto para Associações (3999) ou CNAE de Associações (9499500)
        def is_condo_text(row):
            text = (str(row.get("nome_fantasia", "")) + " " + str(row.get("razao_social", ""))).upper()
            return any(k in text for k in KEYWORDS_CONDO)
        
        mask_text = df.apply(is_condo_text, axis=1)
        
        # Regra: Se for Natureza de Condomínio (3085/2054) ou CNAE de Condomínio (8112500), passa.
        # Se for Associação (3999/9499500), precisa ter a palavra-chave no nome.
        is_hard_condo = df.get("natureza_juridica", pd.Series(dtype=str)).isin({"2054", "3085"}) | \
                        df.get("cnae", pd.Series(dtype=str)).isin({"8112500", "6822600"})
        
        df = df[(is_hard_condo) | (mask_natureza & mask_text) | (mask_cnae & mask_text)]
        
    elif not all_cnaes:
        mask_cnae = df.get("cnae", pd.Series(dtype=str)).isin(CNAES_ALVO.keys())
        mask_natureza = df.get("natureza_juridica", pd.Series(dtype=str)).isin(NATUREZAS_CONDOMINIO)

        if incluir_condominios:
            df = df[mask_cnae | mask_natureza]
        else:
            df = df[mask_cnae]
    else:
        log.info("  Filtro de CNAE desativado (Extração Global).")

    log.info(f"  Após filtros: {len(df):,}")

    def montar_tel(row, ddd_col, tel_col):
        ddd = str(row.get(ddd_col, "") or "").strip()
        tel = str(row.get(tel_col, "") or "").strip()
        if ddd and tel: return f"{ddd}{tel}"
        return tel or ""

    df["telefone_completo_1"] = df.apply(lambda r: montar_tel(r, "ddd1", "tel1"), axis=1)
    df["telefone_completo_2"] = df.apply(lambda r: montar_tel(r, "ddd2", "tel2"), axis=1)

    df["endereco"] = (
        df.get("logradouro", "").fillna("") + ", " +
        df.get("numero", "").fillna("") + " — " +
        df.get("bairro", "").fillna("")
    ).str.strip(", —")

    df["municipio"] = municipio.upper()

    for col in ["tel_maps", "site", "whatsapp", "instagram", "facebook", "email_site", "score", "status", "socios", "tel_opencnpj", "email_opencnpj", "site_google"]:
        if col not in df.columns: df[col] = ""

    df["status"] = "pendente"
    df["atualizado_em"] = datetime.now().isoformat()

    df.to_csv(FILTRADO_CSV, index=False, encoding="utf-8")
    log.info(f"✓ Base filtrada salva: {FILTRADO_CSV} ({len(df):,})")
    update_status(2, 100, f"Filtragem finalizada. {len(df)} prospectos encontrados.")


# ─────────────────────────────────────────────
# PASSO 3 — ENRIQUECIMENTO OPENCNPJ
# ─────────────────────────────────────────────

def _consultar_cnpj_api(cnpj: str) -> dict:
    cnpj_clean = re.sub(r"\D", "", str(cnpj))
    if len(cnpj_clean) != 14: return {}
    try:
        # Usamos minhareceita.org pois o QSA é mais detalhado (com CPF mascarado)
        resp = requests.get(f"https://minhareceita.org/{cnpj_clean}", timeout=10)
        if resp.status_code == 200: return resp.json()
        else: log.warning(f"  API Error {resp.status_code} for {cnpj_clean}")
    except Exception as e: log.error(f"  API Exception: {e}")
    return {}

def step3_enriquecer_opencnpj(limit: int = 0):
    log.info("=== PASSO 3: Enriquecimento via OpenCNPJ ===")
    if not FILTRADO_CSV.exists(): return

    df = pd.read_csv(FILTRADO_CSV, dtype=str)
    if limit: df = df.head(limit)

    novos = []
    total = len(df)
    for i, (_, row) in enumerate(tqdm(df.iterrows(), total=total, desc="Enrich")):
        if i % 10 == 0:
            update_status(3, int((i/total)*100), f"Enriquecendo CNPJ {i}/{total}...", {"current": i, "total": total})

        cnpj = str(row.get("cnpj", "")).strip()
        dados = _consultar_cnpj_api(cnpj)
    log.info(f"DEBUG INDIVIDUAL API: {dados}")
        row_dict = row.to_dict()

        if dados:
            log.info(f"DEBUG API RESPONSE: {dados}")
            # Dados de Contato (Colecionador)
            tels = []
            if dados.get("ddd_telefone_1"): tels.append(str(dados.get("ddd_telefone_1")).strip())
            if dados.get("ddd_telefone_2"): tels.append(str(dados.get("ddd_telefone_2")).strip())
            
            # Limpa e formata os novos telefones
            novos_tels = " | ".join(tels)
            row_dict["tel_opencnpj"] = novos_tels
            row_dict["email_opencnpj"] = str(dados.get("email", "")).lower().strip()
            
            # Tenta mesclar com telefones já existentes no CSV se possível
            current_tel = str(row.get("telefone_completo_1", "")).strip()
            if current_tel and current_tel != "nan":
                # Une as listas removendo duplicatas
                all_tels = list(dict.fromkeys([t.strip() for t in (current_tel + " | " + novos_tels).split("|") if t.strip()]))
                row_dict["telefone_completo_1"] = " | ".join(all_tels)
            else:
                row_dict["telefone_completo_1"] = novos_tels
                
            if not row_dict.get("email"): row_dict["email"] = row_dict["email_opencnpj"]
            
            # Inteligência de Sócios (OSINT)
            socios_raw = dados.get("qsa", [])
            natureza = str(dados.get("codigo_natureza_juridica", ""))
            razao = str(dados.get("razao_social", ""))
            
            # Se for MEI/Individual (2135) e QSA estiver vazio, extraímos do nome
            if not socios_raw and (natureza == "2135" or "2135" in natureza or dados.get("opcao_pelo_mei")):
                # Extrair CPF do final da razão social (padrão MEI: NOME DO SOCIO 12345678900)
                cpf_match = re.search(r"(\d{11})$", razao)
                cpf_extraido = cpf_match.group(1) if cpf_match else ""
                nome_extraido = razao
                if cpf_extraido:
                    nome_extraido = razao.replace(cpf_extraido, "").strip()
                    # Mascarar CPF para manter padrão
                    cpf_extraido = f"***{cpf_extraido[3:9]}**"
                
                socios_raw = [{
                    "nome_socio": nome_extraido,
                    "cnpj_cpf_do_socio": cpf_extraido,
                    "qualificacao_socio": "Empresário Individual (Titular)"
                }]
                log.info(f"  [MEI Detectado] Extraído responsável: {nome_extraido}")

            if socios_raw:
                nomes = [s.get("nome_socio", "") for s in socios_raw]
                row_dict["socios"] = " | ".join(n for n in nomes if n)
                
                qsa_limitado = []
                for s in socios_raw:
                    qsa_limitado.append({
                        "nome": s.get("nome_socio"),
                        "cpf": s.get("cnpj_cpf_do_socio") or s.get("cpf"),
                        "qualificacao": s.get("qualificacao_socio") or s.get("qualificacao"),
                        "entrada": s.get("data_entrada_sociedade") or ""
                    })
                row_dict["qsa_completo"] = json.dumps(qsa_limitado)
            
            row_dict["responsavel_qualificacao"] = dados.get("qualificacao_do_responsavel", "Não informada")
            
            # Dados Cadastrais Adicionais
            row_dict["cnae_descricao"] = dados.get("cnae_fiscal_descricao", "")
            
            # Formatação dos CNAEs Secundários
            secundarios = dados.get("cnaes_secundarios", [])
            sec_list = []
            for s in secundarios:
                sec_list.append(f"{s.get('codigo')} - {s.get('descricao')}")
            row_dict["cnaes_secundarios"] = "\n".join(sec_list)
            
            site_rcf = dados.get("website", "") or dados.get("site", "")
            if site_rcf and not row_dict.get("site"): row_dict["site"] = site_rcf
            
            row_dict["status"] = "enriquecido_ok"
        else:
            row_dict["status"] = "enriquecido_failed"

        novos.append(row_dict)
        time.sleep(0.3)

    pd.DataFrame(novos).to_csv(ENRICH_CNPJ_CSV, index=False, encoding="utf-8")
    update_status(3, 100, "Enriquecimento CNPJ finalizado.")


# ─────────────────────────────────────────────
# PASSO 4 — ENRIQUECIMENTO GOOGLE MAPS
# ─────────────────────────────────────────────

def _buscar_google_places(nome: str, cidade: str):
    if not GOOGLE_MAPS_API_KEY: return {}
    try:
        # Usamos textsearch pois é mais flexível que findplacefromtext
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        resp = requests.get(url, params={
            "query": f"{nome} {cidade}",
            "key": GOOGLE_MAPS_API_KEY,
        }, timeout=10)
        results = resp.json().get("results", [])
        if not results: return {}
        
        place_id = results[0].get("place_id")
        if not place_id: return {}

        det_resp = requests.get("https://maps.googleapis.com/maps/api/place/details/json", params={
            "place_id": place_id,
            "fields": "name,formatted_phone_number,website,url",
            "key": GOOGLE_MAPS_API_KEY,
        }, timeout=10)
        return det_resp.json().get("result", {})
    except Exception: return {}

def step4_enriquecer_maps(municipio: str, limit: int = 0):
    log.info("=== PASSO 4: Enriquecimento via Google Maps ===")
    origem = ENRICH_CNPJ_CSV if ENRICH_CNPJ_CSV.exists() else FILTRADO_CSV
    if not origem.exists(): return

    if not GOOGLE_MAPS_API_KEY:
        log.warning("GOOGLE_MAPS_API_KEY ausente. Pulando.")
        import shutil
        shutil.copy(origem, ENRICH_MAPS_CSV)
        return

    df = pd.read_csv(origem, dtype=str)
    if limit: df = df.head(limit)

    novos = []
    total = len(df)
    for i, (_, row) in enumerate(tqdm(df.iterrows(), total=total, desc="Maps")):
        if i % 5 == 0:
            update_status(4, int((i/total)*100), f"Enriquecendo Google Maps {i}/{total}...", {"current": i, "total": total})

        nome = str(row.get("nome_fantasia") or row.get("razao_social", "")).strip()
        row_dict = row.to_dict()
        if nome:
            res = _buscar_google_places(nome, municipio)
            if res:
                tel = re.sub(r"\D", "", res.get("formatted_phone_number", ""))
                if tel: row_dict["tel_maps"] = tel
                if res.get("website"):
                    row_dict["site_google"] = res.get("website")
                    if not row_dict.get("site"): row_dict["site"] = res.get("website")
                row_dict["status"] = "maps_ok"
        novos.append(row_dict)
        time.sleep(0.2)

    pd.DataFrame(novos).to_csv(ENRICH_MAPS_CSV, index=False, encoding="utf-8")
    update_status(4, 100, "Consulta ao Google Maps concluída.")

# ─────────────────────────────────────────────
# PASSO 5 — SCRAPING
# ─────────────────────────────────────────────

def step5_scraping(limit: int = 0):
    log.info("=== PASSO 5: Scraping de sites via Playwright ===")
    origem = ENRICH_MAPS_CSV if ENRICH_MAPS_CSV.exists() else (ENRICH_CNPJ_CSV if ENRICH_CNPJ_CSV.exists() else FILTRADO_CSV)
    if not origem.exists(): return

    df = pd.read_csv(origem, dtype=str)
    if limit: df = df.head(limit)

    from playwright.sync_api import sync_playwright

    def extrair_contatos(page, url):
        contatos = {"whatsapp": "", "email_site": "", "instagram": "", "facebook": ""}
        try:
            log.info(f"  Visitando: {url}")
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            time.sleep(2) # Espera renderização básica
            
            html = page.content()
            
            # 1. WhatsApp links
            wa_match = re.search(r"(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d{10,13})", html)
            if wa_match:
                contatos["whatsapp"] = wa_match.group(1)
            
            # 2. Emails (Regex simples)
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)
            if emails:
                # Filtra extensões comuns de imagem/assets que parecem email
                validos = [e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]
                if validos: contatos["email_site"] = validos[0].lower()

            # 3. Social Media
            insta = re.search(r"instagram\.com/([a-zA-Z0-9._-]+)", html)
            if insta: contatos["instagram"] = insta.group(1)
            
            face = re.search(r"facebook\.com/([a-zA-Z0-9._-]+)", html)
            if face: contatos["facebook"] = face.group(1)

        except Exception as e:
            log.warning(f"  Falha ao carregar {url}: {e}")
        return contatos

    total = len(df)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = context.new_page()

        for i, (idx, row) in enumerate(df.iterrows()):
            if i % 5 == 0:
                update_status(5, int((i/total)*100), f"Scraping {i}/{total}...", {"current": i, "total": total})

            url = str(row.get("site", "")).strip()
            if url and (url.startswith("http") or "." in url):
                if not url.startswith("http"): url = "http://" + url
                
                results = extrair_contatos(page, url)
                
                if results["whatsapp"]: df.at[idx, "whatsapp"] = results["whatsapp"]
                if results["email_site"]: df.at[idx, "email_site"] = results["email_site"]
                if results["instagram"]: df.at[idx, "instagram"] = results["instagram"]
                if results["facebook"]: df.at[idx, "facebook"] = results["facebook"]

        browser.close()

    # Limpeza final de nans e strings inválidas
    for col in ["whatsapp", "tel_maps", "site", "email_site", "instagram", "facebook"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: "" if str(x).lower() in ["nan", "none", "null", "undefined"] else str(x).strip())

    # Fallback: Se não achou WhatsApp no site, usa o telefone do Maps
    def apply_fallback(r):
        wa = str(r.get("whatsapp", "")).strip()
        tm = str(r.get("tel_maps", "")).strip()
        if not wa and tm:
            # Se tm tem 10 ou 11 dígitos, é um candidato a WhatsApp
            if 10 <= len(tm) <= 12: # Suporta 12 para prefixo 55
                return tm
        return wa

    log.info("  Aplicando fallback de contatos (Maps -> WhatsApp)...")
    df["whatsapp"] = df.apply(apply_fallback, axis=1)

    # Cálculo final de score
    def calc_score(r):
        s = 0
        w = str(r.get("whatsapp", "")).strip()
        tm = str(r.get("tel_maps", "")).strip()
        e = str(r.get("email", "")).strip() or str(r.get("email_site", "")).strip()
        si = str(r.get("site", "")).strip()
        
        # Só conta se não for "nan" ou vazio
        has_w = w and w.lower() != "nan"
        has_tm = tm and tm.lower() != "nan"
        has_e = e and e.lower() != "nan"
        has_si = si and si.lower() != "nan"

        if has_w or has_tm: s += 3
        if has_e: s += 1
        if has_si: s += 1
        return min(s, 5)

    df["score"] = df.apply(calc_score, axis=1)
    df.to_csv(FINAL_CSV, index=False, encoding="utf-8")
    update_status(5, 100, "Scraping e pontuação finalizados.")


# ─────────────────────────────────────────────
# PASSO 6 — SALVAR SUPABASE
# ─────────────────────────────────────────────

def step6_salvar_supabase():
    log.info("=== PASSO 6: Salvando no Supabase ===")
    if not USE_SUPABASE: return
    if not FINAL_CSV.exists(): return

    if not FINAL_CSV.exists(): return
    df = pd.read_csv(FINAL_CSV, dtype=str).fillna("")
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Colunas permitidas na tabela (conforme migração 015)
    ALLOWED_COLS = [
        "cnpj", "cnpj_basico", "razao_social", "nome_fantasia", "cnae", 
        "natureza_juridica", "endereco", "bairro", "municipio", "uf", 
        "cep", "ddd1", "tel1", "ddd2", "tel2", "telefone_completo_1", 
        "telefone_completo_2", "email", "email_site", "socios", "tel_maps", 
        "site", "whatsapp", "instagram", "facebook", "score", "status", 
        "tel_opencnpj", "email_opencnpj", "site_google", "notas_investigacao",
        "atualizado_em", "identificador_matriz_filial", "data_situacao_cadastral",
        "motivo_situacao_cadastral", "data_inicio_atividade", "logradouro",
        "numero", "complemento", "codigo_municipio", "municipio_import",
        "ddd_fax", "qualificacao_do_responsavel", "capital_social", "porte",
        "opcao_pelo_simples", "data_opcao_pelo_simples", "data_exclusao_do_simples",
        "opcao_pelo_mei", "situacao_especial", "data_situacao_especial",
        "cnae_descricao", "cnaes_secundarios", "responsavel_qualificacao"
    ]
    
    # Filtra e limpa colunas
    cols_to_use = [c for c in ALLOWED_COLS if c in df.columns]
    df_sync = df[cols_to_use].copy()

    # Tratamento especial para CAPITAL_SOCIAL (converter para número)
    if "capital_social" in df_sync.columns:
        df_sync["capital_social"] = pd.to_numeric(df_sync["capital_social"].str.replace(",", "."), errors="coerce").fillna(0)

    # Preencher vazios para evitar erro no Supabase
    df_sync = df_sync.fillna("")

    total = len(df_sync)
    for i in tqdm(range(0, total, 50), desc="Supabase"):
        update_status(6, int((i/total)*100), f"Sincronizando com Supabase {i}/{total}...", {"current": i, "total": total})
        batch = df_sync.iloc[i:i+50].to_dict(orient="records")
        # Remover campos vazios que podem conflitar com datas/números se necessário
        # Mas .fillna("") acima já ajuda para campos TEXT.
        try:
            client.table("empresas_sjc").upsert(batch, on_conflict="cnpj").execute()
        except Exception as e:
            log.error(f"Erro no batch {i}: {e}")

    log.info(f"✓ {total} registros enviados ao Supabase.")
    update_status(6, 100, "Dados sincronizados com o CRM.")


def enriquecer_cnpj_individual(cnpj: str):
    """
    Enriquece um único CNPJ e salva diretamente no Supabase.
    Retorna os dados enriquecidos ou None.
    """
    log.info(f"🚀 Iniciando enriquecimento individual: {cnpj}")
    dados = _consultar_cnpj_api(cnpj)
    # Dados de Contato (Colecionador)
    tels_api = []
    if dados.get("ddd_telefone_1"): tels_api.append(str(dados.get("ddd_telefone_1")).strip())
    if dados.get("ddd_telefone_2"): tels_api.append(str(dados.get("ddd_telefone_2")).strip())
    novos_tels = " | ".join(tels_api)

    # Mapeamento de campos para o Supabase
    row = {
        "cnpj": cnpj,
        "razao_social": dados.get("razao_social"),
        "nome_fantasia": dados.get("nome_fantasia"),
        "natureza_juridica": dados.get("natureza_juridica"),
        "logradouro": dados.get("logradouro"),
        "numero": dados.get("numero"),
        "complemento": dados.get("complemento"),
        "bairro": dados.get("bairro"),
        "cep": dados.get("cep"),
        "municipio": dados.get("municipio"),
        "uf": dados.get("uf"),
        "endereco": f"{dados.get('logradouro')}, {dados.get('numero')} - {dados.get('bairro')}",
        "email": dados.get("email"),
        "email_opencnpj": dados.get("email"),
        "telefone_completo_1": novos_tels,
        "tel_opencnpj": novos_tels,
        "status": dados.get("descricao_situacao_cadastral", "ATIVA"), # Usa descrição string
        "data_situacao_cadastral": dados.get("data_situacao_cadastral"),
        "qualificacao_do_responsavel": dados.get("qualificacao_do_responsavel"),
        "capital_social": float(str(dados.get("capital_social", 0)).replace(",", ".")),
        "porte": dados.get("porte"),
        "opcao_pelo_simples": "1" if dados.get("opcao_pelo_simples") else "0",
        "opcao_pelo_mei": "1" if dados.get("opcao_pelo_mei") else "0",
        "score": 5, # Lead que passou por OSINT ganha score máximo
        "cnae_descricao": dados.get("cnae_fiscal_descricao"),
        "cnaes_secundarios": "\n".join([f"{s.get('codigo')} - {s.get('descricao')}" for s in dados.get("cnaes_secundarios", [])]),
        "atualizado_em": datetime.now().isoformat()
    }

    # Processamento QSA (OSINT)
    socios_raw = dados.get("qsa", [])
    natureza = str(dados.get("codigo_natureza_juridica", ""))
    razao = str(dados.get("razao_social", ""))
    
    # Suporte a MEI
    if not socios_raw and (natureza == "2135" or "2135" in natureza or dados.get("opcao_pelo_mei")):
        cpf_match = re.search(r"(\d{11})$", razao)
        cpf_extraido = cpf_match.group(1) if cpf_match else ""
        nome_extraido = razao
        if cpf_extraido:
            nome_extraido = razao.replace(cpf_extraido, "").strip()
            cpf_extraido = f"***{cpf_extraido[3:9]}**"
        
        socios_raw = [{
            "nome_socio": nome_extraido,
            "cnpj_cpf_do_socio": cpf_extraido,
            "qualificacao_socio": "Empresário Individual (Titular)"
        }]

    if socios_raw:
        nomes = [s.get("nome_socio", "") for s in socios_raw]
        row["socios"] = " | ".join(n for n in nomes if n)
        
        qsa_com_dados = []
        for s in socios_raw:
            qsa_com_dados.append({
                "nome": s.get("nome_socio"),
                "cpf": s.get("cnpj_cpf_do_socio") or s.get("cpf"),
                "qualificacao": s.get("qualificacao_socio") or s.get("qualificacao"),
                "entrada": s.get("data_entrada_sociedade") or ""
            })
        row["qsa_completo"] = json.dumps(qsa_com_dados)
    row["responsavel_qualificacao"] = str(dados.get("qualificacao_do_responsavel", "Não informada"))

    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        client = create_client(url, key)
        
        # LÓGICA DE COLECIONADOR: Busca dados atuais antes de salvar
        current = client.table("empresas_sjc").select("whatsapp, tel_maps, tel_opencnpj, telefone_completo_1, telefone_completo_2").eq("cnpj", cnpj).execute()
        if current.data:
            c = current.data[0]
            # Função para mesclar strings de telefone separadas por |
            def merge(old, new):
                if not old: return new
                if not new: return old
                combined = list(dict.fromkeys([t.strip() for t in (str(old) + " | " + str(new)).split("|") if t.strip()]))
                return " | ".join(combined)
            
            row["whatsapp"] = merge(c.get("whatsapp"), row.get("whatsapp"))
            row["tel_maps"] = merge(c.get("tel_maps"), row.get("tel_maps"))
            row["tel_opencnpj"] = merge(c.get("tel_opencnpj"), row.get("tel_opencnpj"))
            row["telefone_completo_1"] = merge(c.get("telefone_completo_1"), row.get("telefone_completo_1"))
            row["telefone_completo_2"] = merge(c.get("telefone_completo_2"), row.get("telefone_completo_2"))

        res = client.table("empresas_sjc").upsert(row, on_conflict="cnpj").execute()
        log.info(f"✅ CNPJ {cnpj} sincronizado com sucesso!")
        return row
    except Exception as e:
        log.error(f"Erro ao salvar enriquecimento individual no Supabase: {e}")
        raise e # Repassa para o server capturar

def enriquecer_receitaws_individual(cnpj: str, ignore_proxy: bool = False):
    """
    Consulta a API ReceitaWS (Premium ou Free) e atualiza o lead.
    """
    from datetime import datetime
    import os
    import requests
    import json

    cnpj_clean = re.sub(r"\D", "", str(cnpj))
    token = os.getenv("RECEITAWS_TOKEN", "")
    proxy_url = os.getenv("PROXY_SCRAPING_URL")
    proxy_key = os.getenv("PROXY_SCRAPING_KEY")
    
    target_url = f"https://receitaws.com.br/v1/cnpj/{cnpj_clean}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if proxy_url and proxy_key and not ignore_proxy:
            log.info(f"[ReceitaWS] Usando PROXY WebScraping.AI para CNPJ {cnpj_clean}...")
            # Chamada via Proxy (Default/Datacenter para maior velocidade e estabilidade)
            resp = requests.get(proxy_url, params={
                "api_key": proxy_key,
                "url": target_url
            }, timeout=45)
        else:
            log.info(f"[ReceitaWS] Consultando CNPJ {cnpj_clean} diretamente...")
            resp = requests.get(target_url, headers=headers, timeout=15)

    except Exception as e:
        raise Exception(f"Erro na conexão com API/Proxy: {e}")
    
    if resp.status_code == 429:
        raise Exception("Limite de requisições do ReceitaWS atingido (3/min no plano grátis).")
    
    if resp.status_code != 200:
        raise Exception(f"Erro na API ReceitaWS: Status {resp.status_code}")
        
    dados = resp.json()
    if dados.get("status") == "ERROR":
        raise Exception(f"ReceitaWS retornou erro: {dados.get('message')}")

    # Mapeamento do Porte (String -> Código RFB)
    porte_map = {
        "DEMAIS": "05",
        "MICRO EMPRESA": "01",
        "EMPRESA DE PEQUENO PORTE": "03"
    }
    porte_str = dados.get("porte", "DEMAIS").upper()
    porte_code = porte_map.get(porte_str, "05")

    # Mapeamento da Abertura (DD/MM/YYYY -> YYYY-MM-DD)
    abertura_raw = dados.get("abertura", "")
    data_abertura = ""
    try:
        if abertura_raw:
            data_abertura = datetime.strptime(abertura_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
    except: pass

    # Mapeamento Natureza Jurídica (Pega apenas os números se possível)
    natureza_raw = dados.get("natureza_juridica", "")
    natureza_code = re.sub(r"\D", "", natureza_raw.split(" - ")[0]) if natureza_raw else ""

    row = {
        "cnpj": cnpj_clean,
        "razao_social": dados.get("nome"),
        "nome_fantasia": dados.get("fantasia"),
        "natureza_juridica": natureza_code,
        "data_inicio_atividade": data_abertura,
        "email": dados.get("email"),
        "email_opencnpj": dados.get("email"), # Compatibilidade
        "telefone_completo_1": str(dados.get("telefone", "")).split("/")[0].strip(),
        "tel_opencnpj": str(dados.get("telefone", "")).replace("/", " | "),
        "capital_social": float(str(dados.get("capital_social", 0)).replace(",", ".")),
        "porte": porte_code,
        "status": "enriquecido_premium",
        "score": 5,
        "cnae": re.sub(r"\D", "", dados.get("atividade_principal", [{}])[0].get("code", "")),
        "cnae_descricao": dados.get("atividade_principal", [{}])[0].get("text", ""),
        "cnaes_secundarios": "\n".join([f"{s.get('code')} - {s.get('text')}" for s in dados.get("atividades_secundarias", [])]),
        "atualizado_em": datetime.now().isoformat()
    }

    # Processamento QSA
    socios_raw = dados.get("qsa", [])
    
    # Suporte a MEI no ReceitaWS
    if not socios_raw and (row["natureza_juridica"] == "2135" or dados.get("mei")):
        razao = str(dados.get("nome", ""))
        cpf_match = re.search(r"(\d{11})$", razao)
        cpf_extraido = cpf_match.group(1) if cpf_match else ""
        nome_extraido = razao
        if cpf_extraido:
            nome_extraido = razao.replace(cpf_extraido, "").strip()
            cpf_extraido = f"***{cpf_extraido[3:9]}**"
        
        socios_raw = [{
            "nome": nome_extraido,
            "cpf": cpf_extraido,
            "qual": "Empresário Individual (Titular)"
        }]

    if socios_raw:
        nomes = [s.get("nome", "") for s in socios_raw]
        row["socios"] = " | ".join(n for n in nomes if n)
        
        qsa_com_dados = []
        for s in socios_raw:
            qsa_com_dados.append({
                "nome": s.get("nome"),
                "cpf": s.get("cpf") or "",
                "qualificacao": s.get("qual") or "",
                "entrada": ""
            })
        row["qsa_completo"] = json.dumps(qsa_com_dados)

    try:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        client = create_client(url, key)
        client.table("empresas_sjc").upsert(row, on_conflict="cnpj").execute()
        log.info(f"✅ CNPJ {cnpj} enriquecido via ReceitaWS com sucesso!")
        return row
    except Exception as e:
        log.error(f"Erro ao salvar ReceitaWS no Supabase: {e}")
        raise e


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Pipeline Extrator CNPJ")
    parser.add_argument("--municipio", default="SAO JOSE DOS CAMPOS", help="Município base")
    parser.add_argument("--step", choices=["1", "2", "3", "4", "5", "6", "all", "resume"], default="all")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--all_cnaes", action="store_true", help="Enriquece todas as empresas sem filtrar CNAE")
    parser.add_argument("--test_condo", action="store_true", help="Teste focado em Condomínios e Associações")
    args = parser.parse_args()

    m = args.municipio
    s = args.step
    l = args.limit
    ac = args.all_cnaes
    tc = args.test_condo

    start_step = 0

    if s == "resume":
        try:
            status = json.loads(STATUS_FILE.read_text())
            last_step = status.get("last_step", 0)
            progress = status.get("progress", 0)
            
            # Se terminou o ultimo step 100%, vai pro proximo
            if progress == 100:
                start_step = last_step + 1
            else:
                start_step = last_step

            if start_step > 6:
                log.info("Pipeline já estava 100% concluído.")
                return
        except Exception:
            start_step = 0
            
        s = "seq" # forçar execução sequencial

    if s == "all":
        s = "seq"
        start_step = 0

    if s == "seq":
        if start_step <= 0:
            # No modo seq completo, verificamos downloads base
            download_dir = Path(__file__).parent.parent / "socios-brasil" / "data" / "download"
            zips = list(download_dir.glob("DADOS_ABERTOS_CNPJ_*.zip"))
            parciais = list(download_dir.glob("*.aria2"))
            if len(zips) < 10 or len(parciais) > 0:
                step0_download_dumps()
        
        if start_step <= 1: step1_extrair_do_dump(m, l, all_cnaes=ac, test_condo=tc)
        if start_step <= 2: step2_filtrar(m, incluir_condominios=(not ac), all_cnaes=ac, test_condo=tc)
        if start_step <= 3: step3_enriquecer_opencnpj(l)
        if start_step <= 4: step4_enriquecer_maps(m, l)
        if start_step <= 5: step5_scraping(l)
        if start_step <= 6: step6_salvar_supabase()
    else:
        # Passos Individuais
        if s == "1": step1_extrair_do_dump(m, l, all_cnaes=ac, test_condo=tc)
        if s == "2": step2_filtrar(m, incluir_condominios=True, all_cnaes=ac, test_condo=tc)
        if s == "3": step3_enriquecer_opencnpj(l)
        if s == "4": step4_enriquecer_maps(m, l)
        if s == "5": step5_scraping(l)
        if s == "6": step6_salvar_supabase()

    log.info("--- PIPELINE FINALIZADO ---")

if __name__ == "__main__":
    main()
