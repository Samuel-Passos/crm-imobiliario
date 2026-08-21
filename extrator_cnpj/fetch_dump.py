import os
import json
import requests
import subprocess
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

# Configurações
MIRROR_URL = "https://data.brasil.io/mirror/socios-brasil"
# No momento da implementação, os arquivos costumam seguir este padrão:
# DADOS_ABERTOS_CNPJ_01.zip ... DADOS_ABERTOS_CNPJ_10.zip
# Vamos baixar todos os parciais de 01 a 10.
FILES = [f"DADOS_ABERTOS_CNPJ_{i:02d}.zip" for i in range(1, 11)]

DEST_DIR = Path(__file__).parent.parent / "socios-brasil" / "data" / "download"
DEST_DIR.mkdir(parents=True, exist_ok=True)

STATUS_FILE = Path(__file__).parent / "output" / "current_status.json"

def update_crm_status(progress, msg):
    try:
        status = {
            "last_step": 0,
            "progress": int(progress),
            "message": msg,
            "updated_at": datetime.now().isoformat()
        }
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATUS_FILE.write_text(json.dumps(status, indent=2))
    except Exception: pass

def download_file(url, dest, file_idx, total_files):
    base_progress = (file_idx / total_files) * 100
    step_weight = 100 / total_files

    if dest.exists():
        # Se o arquivo já existe e está completo (aria2c verifica isso pelo .aria2)
        # Por simplicidade aqui apenas pulamos se o arquivo .aria2 não existir
        aria_control = Path(str(dest) + ".aria2")
        if not aria_control.exists():
            print(f"Skipping {dest.name}, already exists.")
            update_crm_status(base_progress + step_weight, f"Já baixado: {dest.name}")
            return
    
    msg = f"Baixando {dest.name} ({file_idx+1}/{total_files})..."
    update_crm_status(base_progress, msg)
    print(msg)
    # Usando aria2c se disponível para velocidade, senão requests
    try:
        # Nota: aria2c não reporta progresso em JSON facilmente aqui, 
        # então o status no CRM vai atualizar por arquivo no modo aria2c, 
        # ou por megabyte no modo fallback (requests).
        subprocess.run(["aria2c", "-x", "8", "-s", "8", "-c", "-d", str(dest.parent), "-o", dest.name, url], check=True)
        update_crm_status(base_progress + step_weight, f"Concluído: {dest.name}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback para requests com reporte fino de percentual
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(dest, "wb") as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=dest.name) as pbar:
            for data in response.iter_content(chunk_size=1024*1024):
                f.write(data)
                downloaded += len(data)
                pbar.update(len(data))
                # Atualiza CRM a cada ~5MB
                if downloaded % (5*1024*1024) < (1*1024*1024):
                    file_perc = (downloaded / total_size) * step_weight
                    update_crm_status(base_progress + file_perc, msg)

def main():
    total = len(FILES)
    for i, filename in enumerate(FILES):
        url = f"{MIRROR_URL}/{filename}"
        dest = DEST_DIR / filename
        try:
            download_file(url, dest, i, total)
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
    
    update_crm_status(100, "Todos os dumps foram baixados.")

if __name__ == "__main__":
    main()
