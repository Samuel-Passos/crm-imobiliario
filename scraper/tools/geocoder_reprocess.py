"""
geocoder_reprocess.py
─────────────────────
Reprocessa imóveis que já tinham coordenadas mas foram geocodificados
pela versão antiga (sem a coluna geocode_strategy) OU que caíram em
"Centro do Bairro" / "Centro da Cidade", usando o algoritmo v3.

Objectivo:
  1. Melhorar a precisão para endereço de rua.
  2. Marcar com geocode_needs_review=true os que continuarem imprecisos,
     para uso futuro de outro motor (ex: Google Maps API).
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

# Importa todas as funções do geocoder principal para manter consistência
from tools.geocoder import geocodificar_imovel, DELAY
import tools.geocode_signals as signals

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

ESTRATEGIAS_IMPRECISAS = {'Centro do Bairro', 'Centro da Cidade', None}
LOTE = 1000


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    print("♻️  Geocodificador de Reprocessamento v3")
    print("   Alvos: sem geocode_strategy  OU  com estratégia imprecisa\n")

    signals.IS_RUNNING = True
    signals.STOP_SIGNAL = False

    try:
        # 1. Sem geocode_strategy (geocodificados antes do v2)
        r1 = supabase.table('imoveis')\
            .select("id, rua, bairro, cidade, estado, geocode_strategy")\
            .eq("ativo", True)\
            .not_.is_("latitude", "null")\
            .is_("geocode_strategy", "null")\
            .not_.is_("rua", "null")\
            .limit(LOTE)\
            .execute()

        # 2. Estratégia imprecisa
        r2 = supabase.table('imoveis')\
            .select("id, rua, bairro, cidade, estado, geocode_strategy")\
            .eq("ativo", True)\
            .not_.is_("latitude", "null")\
            .in_("geocode_strategy", ["Centro do Bairro", "Centro da Cidade"])\
            .not_.is_("rua", "null")\
            .limit(LOTE)\
            .execute()

        # Mescla, removendo duplicatas
        seen: set = set()
        imoveis = []
        for im in (r1.data or []) + (r2.data or []):
            if im['id'] not in seen:
                seen.add(im['id'])
                imoveis.append(im)
            if len(imoveis) >= LOTE:
                break

        if not imoveis:
            print("✅ Nenhum imóvel impreciso encontrado! Base já está atualizada.")
            return

        print(f"📋 {len(imoveis)} imóveis para reprocessar neste lote\n")

        melhorados = 0
        continuam_imprecisos = 0
        por_estrategia: dict[str, int] = {}

        for im in imoveis:
            if signals.STOP_SIGNAL:
                print("🛑 Parada solicitada via sinal! Interrompendo reprocessamento...")
                break

            id_ = im['id']
            rua = (im.get('rua') or '').strip()
            bairro = (im.get('bairro') or '').strip()
            cidade = (im.get('cidade') or '').strip()
            estado = (im.get('estado') or 'SP').strip()
            estrategia_anterior = im.get('geocode_strategy') or 'nenhuma'

            if not cidade:
                print(f"[{id_}] Pulando – sem cidade.")
                continue

            print(f"[{id_}] (era: {estrategia_anterior}) | rua: {rua[:55]}")

            coords, nova_estrategia = geocodificar_imovel(rua, bairro, cidade, estado)

            if not coords:
                print(f"  ❌ Nenhuma coordenada encontrada.\n")
                continuam_imprecisos += 1
                continue

            lat, lng = coords
            impreciso_ainda = nova_estrategia in ESTRATEGIAS_IMPRECISAS
            melhorou = estrategia_anterior in ESTRATEGIAS_IMPRECISAS and not impreciso_ainda

            print(f"  ✅ ({lat:.5f}, {lng:.5f}) via '{nova_estrategia}' {'⬆️ MELHORA!' if melhorou else ''}\n")
            por_estrategia[nova_estrategia] = por_estrategia.get(nova_estrategia, 0) + 1

            dados = {
                'latitude': lat,
                'longitude': lng,
                'geocode_strategy': nova_estrategia,
                'geocode_needs_review': impreciso_ainda,
            }

            try:
                supabase.table('imoveis').update(dados).eq('id', id_).execute()
            except Exception:
                try:
                    supabase.table('imoveis').update({
                        'latitude': lat, 'longitude': lng,
                        'geocode_strategy': nova_estrategia
                    }).eq('id', id_).execute()
                except Exception as e2:
                    print(f"  ⚠️ Erro ao salvar ID {id_}: {e2}")
                    continue

            if melhorou:
                melhorados += 1
            elif impreciso_ainda:
                continuam_imprecisos += 1

        print("─" * 50)
        print("📊 RESULTADO DO REPROCESSAMENTO")
        print(f"   Analisados          : {len(imoveis)}")
        print(f"   Melhorados p/ rua   : {melhorados}")
        print(f"   Ainda imprecisos    : {continuam_imprecisos} (marcados com geocode_needs_review=true)")
        print("   Por estratégia:")
        for est, n in sorted(por_estrategia.items(), key=lambda x: -x[1]):
            print(f"     · {est}: {n}")

    finally:
        signals.IS_RUNNING = False
        signals.STOP_SIGNAL = False

    print("\nRode novamente para continuar o reprocessamento em lotes.")


if __name__ == "__main__":
    main()
