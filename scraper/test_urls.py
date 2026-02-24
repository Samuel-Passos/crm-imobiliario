import asyncio
from tools.phone_extractor import extract_phones_from_olx

urls_to_test = [
    ("Kitnet c/ Tel Descricao", "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/kitnet-tatetuba-1479866449")
]

async def main():
    print("Iniciando testes de extração para 3 URLs...\n")
    for nome_cenario, url in urls_to_test:
        print(f"--- Testando Cenário: {nome_cenario} ---")
        print(f"URL: {url}")
        resultado = await extract_phones_from_olx(url)
        print(f"\n[X] RESULTADO {nome_cenario}:")
        print(resultado)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
