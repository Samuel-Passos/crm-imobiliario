import os
import time
import requests
import re
import unicodedata
from dotenv import load_dotenv
from supabase import create_client, Client
import tools.geocode_signals as signals

# Carrega variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Erro: SUPABASE_URL ou SUPABASE_KEY não configuradas no .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {'User-Agent': 'CRM-Imobiliario-Geocoder/3.0 (script de automacao)'}
DELAY = 1.5  # Respeitar o rate limit do Nominatim (max 1 req/s)


# ─── Funções de limpeza de endereços ─────────────────────────────────────────

def remover_sufixo_ibge(rua: str) -> str:
    """
    Remove todos os sufixos IBGE de faixa numérica e observações laterais.

    Exemplos cobertos:
      "Av Andrômeda - até 2531 - lado ímpar"   → "Av Andrômeda"
      "Av JK - de 6001/6002 ao fim"             → "Av JK"
      "Av Dom José - de 2000 a 3489 - lado par" → "Av Dom José"
      "Rua X - até 590/591"                     → "Rua X"
      "Rua Y (Antiga Rua Z)"                    → "Rua Y"
      "Rodovia Dutra - até km 140,999"          → "Rodovia Dutra"
    """
    if not rua:
        return rua

    # 1. Remove tudo após o primeiro hífen seguido de palavras-chave IBGE
    #    Cobre: "- de X", "- até X", "- a X", "- lado X", "- km X", "- ao fim"
    rua_limpa = re.sub(
        r'\s*-\s*(de |até |ate |a \d|ao |lado |km ).*$',
        '',
        rua,
        flags=re.IGNORECASE
    )

    # 2. Remove padrões de numeração isolada no final (ex: "- 1265/1266 ao fim")
    rua_limpa = re.sub(r'\s*-\s*\d[\d/,\. ]*.*$', '', rua_limpa, flags=re.IGNORECASE)

    # 3. Remove textos entre parênteses em qualquer posição
    rua_limpa = re.sub(r'\s*\(.*?\)', '', rua_limpa)

    return rua_limpa.strip()


def normalizar_sem_acento(texto: str) -> str:
    """
    Remove acentos do texto para variação de busca.
    Ex: "Ângelo" → "Angelo", "Chuí" → "Chui"
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


def limpar_nome_rua(rua: str) -> str:
    """
    Remove prefixos de logradouro (Rua, Av, Dr, etc.) para busca fuzzy.
    Mantém apenas o nome significativo da rua.
    """
    if not rua:
        return ""

    texto = rua.lower()

    prefixos = [
        r'\bavenida\b', r'\bav\.?\b', r'\brua\b', r'\br\.?\b',
        r'\bdr\.?\b', r'\bdoutor\b', r'\bprof\.?\b', r'\bprofessor\b',
        r'\bdon\b', r'\bdom\b', r'\bgeneral\b', r'\bgen\.?\b',
        r'\bcoronel\b', r'\bcel\.?\b', r'\balameda\b', r'\bal\.?\b',
        r'\bpraca\b', r'\bpraça\b', r'\btravessa\b', r'\btrav\.?\b',
        r'\bvereador\b', r'\bver\.?\b', r'\bprefeito\b', r'\bpref\.?\b',
        r'\bpresidente\b', r'\bpres\.?\b', r'\bsao\b', r'\bsão\b', r'\bsanto\b',
        r'\brodovia\b', r'\brod\.?\b', r'\bestrada\b', r'\best\.?\b',
        r'\bpraca\b', r'\bpraça\b',
    ]

    for prefixo in prefixos:
        texto = re.sub(prefixo + r'\s*', '', texto)

    texto = texto.replace('.', '').replace(',', '').strip()
    return texto if texto else rua


# ─── Funções de busca no Nominatim ────────────────────────────────────────────

def _validar_cidade(data: list, cidade: str) -> bool:
    """
    Verifica se o resultado retornado é realmente da cidade esperada.
    Evita falsos positivos de cidades homônimas em outros estados.
    """
    if not data:
        return False
    display = data[0].get('display_name', '').lower()
    cidade_norm = normalizar_sem_acento(cidade.lower())
    display_norm = normalizar_sem_acento(display)
    return cidade_norm in display_norm


def buscar_freetext(query: str, cidade: str = '') -> tuple[float, float] | None:
    """Busca free-text no Nominatim + valida cidade."""
    params = {
        'q': query,
        'format': 'json',
        'limit': 3,
        'countrycodes': 'br',
    }
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            # Se cidade fornecida, tenta validar; pega o primeiro resultado válido
            for item in data:
                if not cidade or cidade.lower() in item.get('display_name', '').lower():
                    return float(item['lat']), float(item['lon'])
            # Se nenhum passou na validação mas há resultados, usa o 1º mesmo assim
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"    ⚠️ Erro free-text '{query[:55]}': {e}")
    return None


def buscar_estruturado(street: str, city: str, state: str) -> tuple[float, float] | None:
    """
    Busca estruturada com campos separados (mais precisa para ruas brasileiras).
    O Nominatim processa melhor quando cada campo está separado.
    """
    params = {
        'street': street,
        'city': city,
        'state': state,
        'country': 'Brazil',
        'format': 'json',
        'limit': 3,
        'countrycodes': 'br',
    }
    try:
        r = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data:
            for item in data:
                if city.lower() in item.get('display_name', '').lower():
                    return float(item['lat']), float(item['lon'])
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"    ⚠️ Erro structured '{street[:40]}': {e}")
    return None


# ─── Lógica principal de geocodificação ───────────────────────────────────────

def geocodificar_imovel(
    rua_original: str,
    bairro: str,
    cidade: str,
    estado: str
) -> tuple[tuple[float, float] | None, str]:
    """
    Tenta geocodificar em múltiplas estratégias, do mais ao menos preciso.
    Retorna (coordenadas, nome_da_estrategia).
    """
    rua_sem_sufixo = remover_sufixo_ibge(rua_original)
    rua_fuzzy = limpar_nome_rua(rua_sem_sufixo)
    rua_sem_acento = normalizar_sem_acento(rua_sem_sufixo)
    rua_orig_sem_acento = normalizar_sem_acento(rua_original)

    tentativas: list[tuple[str, str, str]] = []
    # Formato: (tipo, query_ou_rua, estrategia_label)
    # tipo: 'structured' | 'freetext'

    if rua_sem_sufixo:
        # T1: Structured search – rua sem sufixo (melhor qualidade)
        tentativas.append(('structured', rua_sem_sufixo, 'Structured (sem sufixo)'))

        # T2: Structured search – rua original (sem limpeza)
        if rua_original and rua_original != rua_sem_sufixo:
            tentativas.append(('structured', rua_original, 'Structured (original)'))

        # T3: Free-text rua limpa + cidade
        tentativas.append(('freetext', f'{rua_sem_sufixo}, {cidade}, {estado}', 'Rua Limpa + Cidade'))

        # T4: Free-text rua original + bairro + cidade
        if rua_original and rua_original != rua_sem_sufixo:
            tentativas.append(('freetext', f'{rua_original}, {bairro}, {cidade}, {estado}', 'Rua Original + Bairro'))

        # T5: Structured sem acento (quando nome tem acentuação diferente no OSM)
        if rua_sem_acento != rua_sem_sufixo:
            tentativas.append(('structured', rua_sem_acento, 'Structured (sem acento)'))

        # T6: Free-text rua sem acento + cidade
        if rua_sem_acento != rua_sem_sufixo:
            tentativas.append(('freetext', f'{rua_sem_acento}, {cidade}, {estado}', 'Rua Sem Acento + Cidade'))

        # T7: Fuzzy – só nome da rua + cidade (sem prefixo)
        if rua_fuzzy and rua_fuzzy.strip() != rua_sem_sufixo.lower().strip():
            tentativas.append(('freetext', f'{rua_fuzzy}, {cidade}, {estado}', 'Rua Fuzzy + Cidade'))

    elif rua_original:
        # Se não há rua sem sufixo (sufixo era a rua toda?), tenta a original
        tentativas.append(('structured', rua_original, 'Structured (original)'))
        tentativas.append(('freetext', f'{rua_original}, {cidade}, {estado}', 'Rua Original + Cidade'))

    # T8: Só bairro (fallback de precisão média)
    if bairro:
        tentativas.append(('freetext', f'{bairro}, {cidade}, {estado}', 'Centro do Bairro'))

    # T9: Só cidade (último recurso)
    tentativas.append(('freetext', f'{cidade}, {estado}', 'Centro da Cidade'))

    for tipo, query_ou_rua, label in tentativas:
        print(f"    🔍 {label}: {query_ou_rua[:70]}")

        if tipo == 'structured':
            coordenadas = buscar_estruturado(query_ou_rua, cidade, estado)
        else:
            coordenadas = buscar_freetext(query_ou_rua, cidade)

        time.sleep(DELAY)

        if coordenadas:
            return coordenadas, label

    return None, ''


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("🚀 Iniciando Geocodificador v3 (Multi-estratégia)...")

    signals.IS_RUNNING = True
    signals.STOP_SIGNAL = False

    try:
        response = supabase.table('imoveis')\
            .select("id, titulo, rua, bairro, cidade, estado")\
            .is_("latitude", "null")\
            .eq("ativo", True)\
            .limit(1000)\
            .execute()

        imoveis = response.data

        if not imoveis:
            print("✅ Nenhum imóvel sem geocodificação! Todos já possuem coordenadas.")
            return

        print(f"📍 {len(imoveis)} imóveis sem coordenadas neste lote. Processando...\n")

        sucessos = 0
        falhas = 0
        por_estrategia: dict[str, int] = {}

        for imovel in imoveis:
            if signals.STOP_SIGNAL:
                print("🛑 Parada solicitada via sinal! Interrompendo geocoder...")
                break

            id_ = imovel['id']
            rua_original = (imovel.get('rua') or '').strip()
            bairro = (imovel.get('bairro') or '').strip()
            cidade = (imovel.get('cidade') or '').strip()
            estado = (imovel.get('estado') or 'SP').strip()

            if not cidade:
                print(f"[{id_}] Pulando — sem cidade.")
                falhas += 1
                continue

            print(f"[{id_}] Buscando: {rua_original[:55] or '(sem rua)'} | {bairro} | {cidade}")

            coordenadas, estrategia = geocodificar_imovel(rua_original, bairro, cidade, estado)

            if coordenadas:
                lat, lng = coordenadas
                print(f"  ✅ ({lat:.5f}, {lng:.5f}) via '{estrategia}'\n")
                por_estrategia[estrategia] = por_estrategia.get(estrategia, 0) + 1

                dados = {'latitude': lat, 'longitude': lng, 'geocode_strategy': estrategia}
                try:
                    supabase.table('imoveis').update(dados).eq('id', id_).execute()
                except Exception:
                    supabase.table('imoveis').update({'latitude': lat, 'longitude': lng}).eq('id', id_).execute()

                sucessos += 1
            else:
                print(f"  ❌ Nenhuma coordenada encontrada.\n")
                falhas += 1

        print("─" * 50)
        print("📊 RESULTADO FINAL DO LOTE")
        print(f"   Analisados : {len(imoveis)}")
        print(f"   Sucessos   : {sucessos}")
        print(f"   Falhas     : {falhas}")
        if por_estrategia:
            print("   Por estratégia:")
            for est, n in sorted(por_estrategia.items(), key=lambda x: -x[1]):
                pct = round(n / sucessos * 100) if sucessos else 0
                print(f"     · {est}: {n} ({pct}%)")

    finally:
        signals.IS_RUNNING = False
        signals.STOP_SIGNAL = False

    print("\nPara processar mais, basta rodar o script novamente.")


if __name__ == "__main__":
    main()
