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

from tools.geocoder_maps_scraper import geocodificar_imovel_maps_scraper, STRATEGY_NAME
import tools.geocode_signals as geocode_signals

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

LOTE = 1000
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


async def main():
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

            coords, nova_estrategia, precisao = await geocodificar_imovel_maps_scraper(
                rua, bairro, cidade, estado, numero, cep, nome_condominio
            )

            if not coords:
                print(f"  ❌ Google Maps também não resolveu. Mantém needs_review=True.\n")
                persistem += 1
                continue

            lat, lng = coords

            # Qualquer resposta do Google é considerada sucesso.
            # O objetivo é que cada endereço seja pesquisado apenas UMA vez por este robô.
            # ROOFTOP / RANGE_INTERPOLATED / GEOMETRIC_CENTER / APPROXIMATE — todos encerram a revisão.
            eh_melhora = coords is not None  # sempre True aqui, mas deixa explícito

            print(f"  ✅ ({lat:.5f}, {lng:.5f}) via '{nova_estrategia}' ({precisao})\n")
            por_estrategia[nova_estrategia] = por_estrategia.get(nova_estrategia, 0) + 1

            dados = {
                'latitude': lat,
                'longitude': lng,
                'geocode_strategy': nova_estrategia,
                'geocode_needs_review': False,  # Sempre False — Google já pesquisou, não tenta mais
            }

            try:
                supabase.table('imoveis').update(dados).eq('id', id_).execute()
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar ID {id_}: {e}")
                continue

            resolvidos += 1

        print("─" * 50)
        print("📊 RESULTADO REPROCESSAMENTO GOOGLE MAPS")
        print(f"   Analisados        : {len(imoveis)}")
        print(f"   Resolvidos (needs_review=False) : {resolvidos}")
        print(f"   Sem resposta (Google falhou)    : {persistem}")
        if por_estrategia:
            print("   Por precisão:")
            for est, n in sorted(por_estrategia.items(), key=lambda x: -x[1]):
                print(f"     · {est}: {n}")

    finally:
        geocode_signals.IS_RUNNING = False
        geocode_signals.STOP_SIGNAL = False

    print("\nRode novamente para continuar o reprocessamento.")


import asyncio
if __name__ == "__main__":
    asyncio.run(main())
