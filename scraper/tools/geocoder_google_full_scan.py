"""
geocoder_google_full_scan.py
─────────────────────────────
Varre TODOS os imóveis ativos e tenta geocodificar/revisar com Google Maps.
Ignora apenas os que o Google já resolveu com alta precisão (ROOFTOP).
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

from tools.geocoder_maps_scraper import geocodificar_imovel_maps_scraper, STRATEGY_NAME
import tools.geocode_signals as geocode_signals

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

LOTE = 10000
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

async def main():
    print("🚀 Iniciando REVISÃO GERAL com Google Maps API")
    print("   Alvo: todos os imóveis ativos (exceto já precisos por Google)\n")

    if not GOOGLE_MAPS_API_KEY:
        print("❌ GOOGLE_MAPS_API_KEY não configurada no .env! Abortando.")
        return

    geocode_signals.IS_RUNNING = True
    geocode_signals.STOP_SIGNAL = False

    try:
        # Busca imóveis que:
        # 1. Estão ativos e não expirados
        # 2. OU precisam de revisão (geocode_needs_review=True)
        # 3. OU nunca foram geocodificados (geocode_strategy is null)
        # 4. OU não foram geocodificados pelo motor Google
        response = supabase.table('imoveis')\
            .select("id, rua, bairro, cidade, estado, geocode_strategy, numero, cep, nome_condominio")\
            .eq("ativo", True)\
            .eq("anuncio_expirado", False)\
            .or_(f"geocode_needs_review.eq.true,geocode_strategy.is.null,not.geocode_strategy.ilike.*{STRATEGY_NAME}*")\
            .limit(LOTE)\
            .execute()

        imoveis = response.data

        if not imoveis:
            print("✅ Tudo resolvido ou nenhum imóvel encontrado.")
            return

        print(f"📋 Processando lote de {len(imoveis)} imóveis...\n")

        sucessos = 0
        mantidos = 0
        falhas = 0

        for im in imoveis:
            if geocode_signals.STOP_SIGNAL:
                print("🛑 Parada solicitada!")
                break

            id_ = im['id']
            rua = (im.get('rua') or '').strip()
            bairro = (im.get('bairro') or '').strip()
            cidade = (im.get('cidade') or '').strip()
            estado = (im.get('estado') or 'SP').strip()
            numero = (im.get('numero') or '').strip()
            cep = (im.get('cep') or '').strip()
            nome_condominio = (im.get('nome_condominio') or '').strip()

            if not cidade:
                continue

            print(f"[{id_}] Revisando: {rua[:40]} {numero} | {cidade}")

            res_google = await geocodificar_imovel_maps_scraper(
                rua, bairro, cidade, estado, numero, cep, nome_condominio
            )
            coords, nova_estrategia, precisao = res_google[0], res_google[1], res_google[2] if len(res_google) > 2 else 'APPROXIMATE'

            if coords:
                lat, lng = coords
                # Qualquer resposta do Google é considerada sucesso.
                # O objetivo é que cada endereço seja pesquisado apenas UMA vez por este robô.
                # ROOFTOP / RANGE_INTERPOLATED / GEOMETRIC_CENTER / APPROXIMATE — todos encerram a revisão.
                print(f"  ✅ ({lat:.5f}, {lng:.5f}) | {precisao}")

                supabase.table('imoveis').update({
                    'latitude': lat,
                    'longitude': lng,
                    'geocode_strategy': f"{nova_estrategia} ({precisao})",
                    'geocode_needs_review': False,  # Sempre False — Google já pesquisou, não tenta mais
                }).eq('id', id_).execute()
                
                sucessos += 1
            else:
                print(f"  ❌ Google não localizou.")
                falhas += 1

        print("\n📊 Resumo Lote:")
        print(f"   Sucessos: {sucessos}")
        print(f"   Falhas  : {falhas}")

    finally:
        geocode_signals.IS_RUNNING = False
        geocode_signals.STOP_SIGNAL = False

import asyncio
if __name__ == "__main__":
    asyncio.run(main())
