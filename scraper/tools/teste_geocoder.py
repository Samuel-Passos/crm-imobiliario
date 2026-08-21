import os
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
import time

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

HEADERS = {'User-Agent': 'CRM-Imobiliario-Diagnostico/1.0'}

def buscar_nominatim(query):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': query, 'format': 'json', 'limit': 1, 'countrycodes': 'br'}
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = r.json()
        if data:
            return data[0].get('lat'), data[0].get('lon'), data[0].get('display_name', '')
    except Exception as e:
        return None, None, str(e)
    return None, None, 'Não encontrado'

print("=" * 60)
print("🔬 TESTE DE GEOCODIFICAÇÃO EM AMOSTRA REAL")
print("=" * 60)

# Pegar 10 imóveis com rua preenchida mas sem coords
amostra = supabase.table('imoveis')\
    .select("id, rua, bairro, cidade, estado")\
    .eq("ativo", True)\
    .is_("latitude", "null")\
    .not_.is_("rua", "null")\
    .limit(10)\
    .execute()

acertos = 0
falhas_rua = []

for im in amostra.data:
    id_ = im['id']
    rua = im.get('rua', '').strip()
    bairro = im.get('bairro', '').strip()
    cidade = im.get('cidade', 'São José dos Campos')
    estado = im.get('estado', 'SP')

    query_original = f"{rua}, {bairro}, {cidade}, {estado}"
    lat, lon, nome = buscar_nominatim(query_original)
    time.sleep(1.5)

    if lat:
        print(f"\n✅ [ID {id_}] ACHOU com rua exata!")
        print(f"   Query: {query_original}")
        print(f"   Resultado: {nome[:80]}")
        acertos += 1
    else:
        # Tentar sem o "- de X ao fim" que o IBGE coloca
        rua_limpa = rua.split(' - de ')[0].split(' - ao ')[0].strip()
        query_limpa = f"{rua_limpa}, {cidade}, {estado}"
        lat2, lon2, nome2 = buscar_nominatim(query_limpa)
        time.sleep(1.5)

        if lat2:
            print(f"\n🟡 [ID {id_}] ACHOU com rua limpa (sem sufixo IBGE)")
            print(f"   Original: {rua}")
            print(f"   Limpa: {rua_limpa}")
            print(f"   Resultado: {nome2[:80]}")
            acertos += 1
        else:
            print(f"\n❌ [ID {id_}] NÃO ACHOU")
            print(f"   Rua original: {rua}")
            print(f"   Query full: {query_original}")
            falhas_rua.append(im)

print(f"\n📊 RESULTADO: {acertos}/10 encontrados com rua")
if falhas_rua:
    print("\n🔎 Imóveis que falharam na rua (vão cair no bairro):")
    for im in falhas_rua:
        print(f"   ID {im['id']}: {im['rua']} | Bairro: {im['bairro']}")
