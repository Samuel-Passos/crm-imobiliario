import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv("olx_captacao/.env")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Verifica as cidades diferentes de SJC
res = supabase.table("imoveis").select("id, cidade, titulo").execute()

count_sjc = 0
count_outras = 0
ids_to_delete = []

for imovel in res.data:
    cidade = imovel.get("cidade")
    # Trata variações de nome
    if cidade and "são josé dos campos" in cidade.lower():
        count_sjc += 1
    else:
        count_outras += 1
        ids_to_delete.append(imovel["id"])

print(f"Total de imóveis em SJC: {count_sjc}")
print(f"Total de imóveis em OUTRAS cidades (para excluir): {count_outras}")

# Opcional: Deleta em lotes (Supabase in/eq)
if ids_to_delete:
    print("Iniciando exclusão...")
    # Dividindo em lotes de 100 para não estourar o limite da URL da API
    batch_size = 100
    for i in range(0, len(ids_to_delete), batch_size):
        batch = ids_to_delete[i:i+batch_size]
        supabase.table("imoveis").delete().in_("id", batch).execute()
        print(f"Deletados {i + len(batch)} de {len(ids_to_delete)}")
    
    print("Exclusão concluída com sucesso!")
else:
    print("Nenhum imóvel para excluir.")
