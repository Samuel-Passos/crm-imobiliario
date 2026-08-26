import os
from dotenv import load_dotenv
from supabase import create_client

# Load the env from the scraper directory if not loaded
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    # try the parent folder if running from olx_captacao
    env_path_2 = os.path.join(os.path.dirname(__file__), "..", "scraper", ".env")
    load_dotenv(env_path_2)
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

try:
    supabase = create_client(supabase_url, supabase_key)
except:
    supabase = None

def get_config():
    """
    Retorna as configurações do scraper armazenadas no banco de dados.
    Caso haja erro ou a tabela não exista/não tenha dados, retorna valores padrão.
    """
    defaults = {
        "url_coleta_padrao": "https://www.olx.com.br/imoveis/estado-sp/vale-do-paraiba-e-litoral-norte/sao-jose-dos-campos?sf=1&f=p",
        "limite_paginas_fase1": 100,
        "lote_fase2": 50,
        "lote_geocoder": 20,
        "lote_extracao": 5,
        "lote_script1": 5,
        "lote_script2": 5,
        "lote_script3": 5,
        "lote_fase2_5": 50,
        "limite_repetidos_fase1": 60,
    }
    
    if not supabase:
        return defaults
        
    try:
        res = supabase.table("configuracoes_scraper").select("*").eq("id", 1).execute()
        if res.data and len(res.data) > 0:
            config = res.data[0]
            # Mescla com os defaults caso algum campo venha nulo
            for key in defaults:
                if config.get(key) is not None:
                    defaults[key] = config[key]
    except Exception as e:
        print(f"[config_db] Erro ao ler configuracoes do banco: {e}")
        
    return defaults
