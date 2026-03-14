"""
geocoder_google_reprocess.py
─────────────────────────────
Reprocessa imóveis marcados com geocode_needs_review=True usando a
Google Maps Geocoding API (segundo motor).

Esses imóveis já foram tentados pelo Nominatim mas ficaram com precisão
apenas de bairro ou cidade. O Google Maps tem maior cobertura de
endereços brasileiros e costuma resolver esses casos.
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

from tools.geocoder_google import geocodificar_imovel_google, DELAY, STRATEGY_NAME
import tools.geocode_signals as geocode_signals

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

LOTE = 1000
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def main():
    """
    Busca imóveis com geocode_needs_review=True e tenta resolver com Google Maps.
    Quando bem-sucedido: atualiza coordenadas e marca geocode_needs_review=False.
    """
    print("♻️  Reprocessamento com Google Maps API")
    print("   Alvo: imóveis com geocode_needs_review = True\n")

    if not GOOGLE_MAPS_API_KEY:
        print("❌ GOOGLE_MAPS_API_KEY não configurada no .env! Abortando.")
        return

    geocode_signals.IS_RUNNING = True
    geocode_signals.STOP_SIGNAL = False

    try:
        response = supabase.table('imoveis')\
            .select("id, rua, bairro, cidade, estado, geocode_strategy, numero, cep, nome_condominio")\
            .eq("ativo", True)\
            .eq("geocode_needs_review", True)\
            .not_.is_("rua", "null")\
            .limit(LOTE)\
            .execute()

        imoveis = response.data

        if not imoveis:
            print("✅ Nenhum imóvel com geocode_needs_review=True! Tudo resolvido.")
            return

        print(f"📋 {len(imoveis)} imóveis marcados para revisão. Processando com Google Maps...\n")

        resolvidos = 0
        persistem = 0
        por_estrategia: dict[str, int] = {}

        for im in imoveis:
            if geocode_signals.STOP_SIGNAL:
                print("🛑 Parada solicitada! Interrompendo reprocessamento Google...")
                break

            id_ = im['id']
            rua = (im.get('rua') or '').strip()
            bairro = (im.get('bairro') or '').strip()
            cidade = (im.get('cidade') or '').strip()
            estado = (im.get('estado') or 'SP').strip()
            numero = (im.get('numero') or '').strip()
            cep = (im.get('cep') or '').strip()
            nome_condominio = (im.get('nome_condominio') or '').strip()
            estrategia_anterior = im.get('geocode_strategy') or 'nenhuma'

            if not cidade:
                print(f"[{id_}] Pulando — sem cidade.")
                continue

            print(f"[{id_}] (era: {estrategia_anterior}) | rua: {rua[:55]} {numero}")

            coords, nova_estrategia, precisao = geocodificar_imovel_google(
                rua, bairro, cidade, estado, numero, cep, nome_condominio
            )

            if not coords:
                print(f"  ❌ Google Maps também não resolveu. Mantém needs_review=True.\n")
                persistem += 1
                continue

            lat, lng = coords

            # Verifica se o Google resolveu com precisão aceitável para sair da revisão
            # ROOFTOP, RANGE_INTERPOLATED e GEOMETRIC_CENTER (para números/condos) são bons.
            # APPROXIMATE geralmente é bairro/cidade.
            eh_melhora = precisao in ['ROOFTOP', 'RANGE_INTERPOLATED', 'GEOMETRIC_CENTER']

            print(f"  ✅ ({lat:.5f}, {lng:.5f}) via '{nova_estrategia}' ({precisao}) {'⬆️ MELHORA!' if eh_melhora else ''}\n")
            por_estrategia[nova_estrategia] = por_estrategia.get(nova_estrategia, 0) + 1

            dados = {
                'latitude': lat,
                'longitude': lng,
                'geocode_strategy': nova_estrategia,
                'geocode_needs_review': not eh_melhora,  # False se melhorou, True se ainda impreciso
            }

            try:
                supabase.table('imoveis').update(dados).eq('id', id_).execute()
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar ID {id_}: {e}")
                continue

            if eh_melhora:
                resolvidos += 1
            else:
                persistem += 1

        print("─" * 50)
        print("📊 RESULTADO REPROCESSAMENTO GOOGLE MAPS")
        print(f"   Analisados        : {len(imoveis)}")
        print(f"   Resolvidos p/ rua : {resolvidos}")
        print(f"   Ainda imprecisos  : {persistem}")
        if por_estrategia:
            print("   Por estratégia:")
            for est, n in sorted(por_estrategia.items(), key=lambda x: -x[1]):
                print(f"     · {est}: {n}")

    finally:
        geocode_signals.IS_RUNNING = False
        geocode_signals.STOP_SIGNAL = False

    print("\nRode novamente para continuar o reprocessamento.")


if __name__ == "__main__":
    main()
