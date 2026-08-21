"""
geocoder_google.py
──────────────────
Segundo motor de geocodificação usando a Google Maps Geocoding API.

Uso:
  - Chamado pelo geocoder_google_reprocess.py para resolver imóveis com
    geocode_needs_review=True (que o Nominatim não conseguiu resolver).
  - Também pode ser chamado via endpoint POST /geocode/google para processar
    imóveis sem coordenadas que o motor Nominatim ainda não tentou.

Requer: GOOGLE_MAPS_API_KEY no arquivo .env
"""

import os
import time
import requests
import unicodedata
from dotenv import load_dotenv
from supabase import create_client, Client
import tools.geocode_signals as geocode_signals
from tools.geocoder import remover_sufixo_ibge

load_dotenv()
signals = geocode_signals

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Erro: SUPABASE_URL ou SUPABASE_KEY não configuradas no .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
DELAY = 0.1  # Google suporta até 50 req/s no plano padrão
LOTE = 1000
STRATEGY_NAME = "Google Maps API"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    """Remove acentos para comparação."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()


def _validar_cidade(result: dict, cidade: str) -> bool:
    """
    Verifica se o resultado retornado pertence à cidade esperada,
    consultando os address_components do Google.
    """
    componentes = result.get('address_components', [])
    cidade_norm = _normalizar(cidade)
    for comp in componentes:
        tipos = comp.get('types', [])
        if 'administrative_area_level_2' in tipos or 'locality' in tipos:
            nome_norm = _normalizar(comp.get('long_name', ''))
            if cidade_norm in nome_norm or nome_norm in cidade_norm:
                return True
    # Fallback: verifica no formatted_address
    addr = _normalizar(result.get('formatted_address', ''))
    return cidade_norm in addr


def _nivel_precisao(result: dict) -> str:
    """
    Retorna o nível de precisão do resultado do Google.
    Tipos comuns: 'ROOFTOP', 'RANGE_INTERPOLATED', 'GEOMETRIC_CENTER', 'APPROXIMATE'
    """
    return result.get('geometry', {}).get('location_type', 'APPROXIMATE')


# ─── Função principal de geocodificação ───────────────────────────────────────

def geocodificar_imovel_google(
    rua: str,
    bairro: str,
    cidade: str,
    estado: str,
    numero: str = '',
    cep: str = '',
    nome_condominio: str = ''
) -> tuple[tuple[float, float] | None, str, str]:
    """
    Geocodifica um endereço usando a Google Maps Geocoding API.
    Tenta da query mais específica para a mais genérica (Sequência Otimizada).
    Retorna (coordenadas, estrategia, precisao) ou (None, '', '').
    """
    if not GOOGLE_MAPS_API_KEY:
        print("    ❌ GOOGLE_MAPS_API_KEY não configurada no .env!")
        return None, '', ''

    rua_limpa = remover_sufixo_ibge(rua)
    tentativas: list[tuple[str, str]] = []

    # T1: Estruturado Total (Limpo) - A mais provável de sucesso preciso
    if rua_limpa:
        query_t1 = f"{rua_limpa}"
        if numero: query_t1 += f", {numero}"
        if bairro: query_t1 += f", {bairro}"
        query_t1 += f", {cidade}, {estado}, Brasil"
        tentativas.append((query_t1, f"{STRATEGY_NAME} (total limpo)"))

    # T2: Precisão Postal (CEP) - Evita erros de grafia de rua
    if cep:
        query_postal = f"{numero}, {cep}, {cidade}, Brasil" if numero else f"{cep}, {cidade}, Brasil"
        tentativas.append((
            query_postal,
            f"{STRATEGY_NAME} (CEP + número)" if numero else f"{STRATEGY_NAME} (CEP)"
        ))

    # T3: Local Conhecido (Condomínio) - O Google Maps conhece muitos POIs
    if nome_condominio:
        tentativas.append((
            f"{nome_condominio}, {cidade}, {estado}, Brasil",
            f"{STRATEGY_NAME} (condomínio)"
        ))

    # T4: Rua + Cidade (Fallback/Fuzzy) - Remove ruído de bairro informal
    if rua_limpa:
        tentativas.append((
            f"{rua_limpa}, {cidade}, Brasil",
            f"{STRATEGY_NAME} (rua + cidade)"
        ))

    # Fallbacks de emergência (apenas se os acima falharem)
    if not tentativas:
        if bairro:
            tentativas.append((f"{bairro}, {cidade}, {estado}, Brasil", f"{STRATEGY_NAME} (bairro)"))
        tentativas.append((f"{cidade}, {estado}, Brasil", f"{STRATEGY_NAME} (cidade)"))

    for query, label in tentativas:
        print(f"    🔍 {label}: {query[:80]}")
        try:
            r = requests.get(
                GEOCODING_URL,
                params={'address': query, 'key': GOOGLE_MAPS_API_KEY, 'region': 'br'},
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"    ⚠️  Erro na requisição Google: {e}")
            time.sleep(DELAY)
            continue

        time.sleep(DELAY)

        status = data.get('status')
        if status == 'ZERO_RESULTS':
            continue
        if status != 'OK':
            print(f"    ⚠️  Google API status: {status}")
            continue

        results = data.get('results', [])
        if not results:
            continue

        # Tenta primeiro resultado válido para a cidade
        for res in results:
            if _validar_cidade(res, cidade):
                loc = res['geometry']['location']
                precisao = _nivel_precisao(res)
                print(f"    📍 Precisão Google: {precisao}")
                return (float(loc['lat']), float(loc['lng'])), label, precisao

        # Se nenhum passou na validação de cidade, usa o primeiro mesmo assim
        loc = results[0]['geometry']['location']
        precisao = _nivel_precisao(results[0])
        print(f"    📍 Precisão Google (sem validação cidade): {precisao}")
        return (float(loc['lat']), float(loc['lng'])), label

    return None, ''


# ─── Main (processa imóveis SEM coordenadas) ──────────────────────────────────

def main():
    """
    Processa imóveis sem coordenadas (latitude IS NULL) usando a Google Maps API.
    Complementar ao geocoder.py (Nominatim) — pode ser rodado antes ou depois.
    """
    print("🗺️  Iniciando Geocodificador Google Maps API...")

    if not GOOGLE_MAPS_API_KEY:
        print("❌ GOOGLE_MAPS_API_KEY não configurada no .env! Abortando.")
        return

    geocode_signals.IS_RUNNING = True
    geocode_signals.STOP_SIGNAL = False
    
    try:
        response = supabase.table('imoveis')\
            .select("id, rua, bairro, cidade, estado, numero, cep, nome_condominio")\
            .is_("latitude", "null")\
            .eq("ativo", True)\
            .limit(LOTE)\
            .execute()
        
        imoveis = response.data
        
        if not imoveis:
            print("✅ Nenhum imóvel sem coordenadas! Todos já possuem localização.")
            return

        print(f"📍 {len(imoveis)} imóveis sem coordenadas. Processando com Google Maps...\n")

        sucessos = 0
        falhas = 0
        por_estrategia: dict[str, int] = {}

        for imovel in imoveis:
            if signals.STOP_SIGNAL:
                print("🛑 Parada solicitada! Interrompendo...")
                break

            id_ = imovel['id']
            rua = (imovel.get('rua') or '').strip()
            bairro = (imovel.get('bairro') or '').strip()
            cidade = (imovel.get('cidade') or '').strip()
            estado = (imovel.get('estado') or 'SP').strip()
            numero = (imovel.get('numero') or '').strip()
            cep = (imovel.get('cep') or '').strip()
            nome_condominio = (imovel.get('nome_condominio') or '').strip()

            if not cidade:
                print(f"[{id_}] Pulando — sem cidade.")
                falhas += 1
                continue

            print(f"[{id_}] {rua[:50] or '(sem rua)'} {numero} | {bairro} | {cidade}")

            coords, estrategia, precisao = geocodificar_imovel_google(
                rua, bairro, cidade, estado, numero, cep, nome_condominio
            )

            if coords:
                lat, lng = coords
                print(f"  ✅ ({lat:.5f}, {lng:.5f}) via '{estrategia}'\n")
                por_estrategia[estrategia] = por_estrategia.get(estrategia, 0) + 1

                supabase.table('imoveis').update({
                    'latitude': lat,
                    'longitude': lng,
                    'geocode_strategy': estrategia,
                }).eq('id', id_).execute()

                sucessos += 1
            else:
                print(f"  ❌ Google Maps também não encontrou.\n")
                falhas += 1

        print("─" * 50)
        print("📊 RESULTADO GOOGLE MAPS")
        print(f"   Analisados : {len(imoveis)}")
        print(f"   Sucessos   : {sucessos}")
        print(f"   Falhas     : {falhas}")
        if por_estrategia:
            print("   Por estratégia:")
            for est, n in sorted(por_estrategia.items(), key=lambda x: -x[1]):
                print(f"     · {est}: {n}")

    finally:
        geocode_signals.IS_RUNNING = False
        geocode_signals.STOP_SIGNAL = False


if __name__ == "__main__":
    main()
