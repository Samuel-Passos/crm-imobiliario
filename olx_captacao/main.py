"""
main.py — Ponto de entrada do scraper OLX de captação
------------------------------------------------------
Módulo SEPARADO e ISOLADO do /scraper/ existente.
Não modifica nenhum arquivo fora da pasta /olx_captacao/.

Uso:
  python main.py fase1                  # Coleta links da listagem OLX
  python main.py fase2                  # Extrai dados dos links pendentes
  python main.py tudo                   # Executa fase1 + fase2 em sequência
  python main.py teste --url "URL"      # Testa extração de uma URL específica

  # Opções adicionais:
  python main.py fase1 --max-paginas 5  # Limita a 5 páginas
  python main.py fase2 --lote 10        # Processa apenas 10 links
"""
import asyncio
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Scraper OLX — Captação de imóveis em São José dos Campos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python main.py fase1                     # Coleta todos os links OLX
  python main.py fase1 --max-paginas 5     # Coleta apenas 5 páginas
  python main.py fase2                     # Extrai dados dos anúncios pendentes
  python main.py fase2 --lote 20           # Extrai apenas 20 anúncios
  python main.py tudo                      # Fase 1 + Fase 2 completos
  python main.py teste --url "URL_OLX"     # Testa uma URL específica
        """
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comando a executar")

    # Comando: fase1
    p1 = subparsers.add_parser("fase1", help="Coleta links da listagem OLX")
    p1.add_argument("--max-paginas", type=int, default=50, help="Máximo de páginas a percorrer (padrão: 50)")
    p1.add_argument("--url", type=str, help="URL de pesquisa personalizada da OLX (opcional)")

    # Comando: fase2
    p2 = subparsers.add_parser("fase2", help="Extrai dados dos anúncios pendentes")
    p2.add_argument("--lote", type=int, default=50, help="Quantidade de links a processar (padrão: 50)")

    # Comando: tudo
    pt = subparsers.add_parser("tudo", help="Executa fase1 + fase2 em sequência")
    pt.add_argument("--max-paginas", type=int, default=50, help="Máximo de páginas para fase1")
    pt.add_argument("--lote", type=int, default=50, help="Quantidade de links para fase2")

    # Comando: teste
    ptest = subparsers.add_parser("teste", help="Testa extração de uma URL específica")
    ptest.add_argument("--url", type=str, required=True, help="URL do anúncio OLX para testar")

    # Comando: extrair-unico
    pu = subparsers.add_parser("extrair-unico", help="Extrai e SALVA um anúncio específico")
    pu.add_argument("--url", type=str, required=True, help="URL do anúncio OLX para extrair e salvar")

    args = parser.parse_args()

    if not args.comando:
        parser.print_help()
        sys.exit(1)

    # ── Execução ──────────────────────────────────────────────────────────────

    if args.comando == "fase1":
        from fase1_coleta_links import coletar_links
        # Se vier args.url, repassa para coletar_links
        url_customizada = getattr(args, "url", None)
        resultado = asyncio.run(coletar_links(max_paginas=args.max_paginas, url_base=url_customizada))
        print(f"\n✅ Fase 1 concluída: {resultado}")

    elif args.comando == "fase2":
        from fase2_extrai_dados import extrair_dados
        resultado = asyncio.run(extrair_dados(lote=args.lote))
        print(f"\n✅ Fase 2 concluída: {resultado}")

    elif args.comando == "tudo":
        import time

        print("\n" + "=" * 60)
        print("🚀 EXECUÇÃO COMPLETA: FASE 1 + FASE 2")
        print("=" * 60)

        from fase1_coleta_links import coletar_links
        r1 = asyncio.run(coletar_links(max_paginas=args.max_paginas))
        print(f"\n✅ Fase 1 concluída: {r1['total_novos']} links novos coletados")

        if r1["total_novos"] > 0:
            print(f"\n⏳ Aguardando 5s antes de iniciar a Fase 2...")
            time.sleep(5)

            from fase2_extrai_dados import extrair_dados
            r2 = asyncio.run(extrair_dados(lote=args.lote))
            print(f"\n✅ Fase 2 concluída: {r2['salvos']} imóveis extraídos")
        else:
            print("\n⚠️ Nenhum link novo coletado — Fase 2 pulada.")

    elif args.comando == "teste":
        import json
        from fase2_extrai_dados import processar_url_unica
        resultado = asyncio.run(processar_url_unica(args.url))
        if resultado:
            print("\n📋 Dados extraídos:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False, default=str))
        else:
            print("\n❌ Não foi possível extrair dados desta URL")

    elif args.comando == "extrair-unico":
        from fase2_extrai_dados import processar_e_salvar_unico
        asyncio.run(processar_e_salvar_unico(args.url))


if __name__ == "__main__":
    main()
