import os
import sys
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path

# Configura paths
ROOT = Path(__file__).parent.parent
env_path = ROOT / "scraper" / ".env"
load_dotenv(env_path)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def count_coords():
    # Tabelas prováveis de conter coordenadas
    targets = [
        {"table": "imoveis", "lat": "latitude", "lng": "longitude"},
        {"table": "condominios", "lat": "lat", "lng": "lng"},
        {"table": "condominios", "lat": "latitude", "lng": "longitude"},
        {"table": "disponibilidade", "lat": "lat", "lng": "lng"},
        {"table": "empresas_sjc", "lat": "latitude", "lng": "longitude"}
    ]
    
    found_any = False
    for target in targets:
        try:
            # Tenta contar registros onde lat/lng não são nulos
            res = supabase.table(target['table']).select('id', count='exact').not_.is_(target['lat'], 'null').execute()
            if res.count > 0:
                print(f"📍 Tabela '{target['table']}': {res.count} coordenadas encontradas (coluna {target['lat']})")
                found_any = True
        except:
            continue
            
    if not found_any:
        print("Nenhuma coordenada geográfica encontrada nas tabelas principais.")

if __name__ == "__main__":
    count_coords()
