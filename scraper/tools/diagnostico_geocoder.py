import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

print("=" * 60)
print("📊 DIAGNÓSTICO DE QUALIDADE DE ENDEREÇOS NO BANCO DE DADOS")
print("=" * 60)

# Contagem geral de ativos
total = supabase.table('imoveis').select("id", count="exact").eq("ativo", True).execute()
total_ativos = total.count
print(f"\n🏠 Total de imóveis ativos: {total_ativos}")

# Sem coordenadas
sem_coords = supabase.table('imoveis').select("id", count="exact")\
    .eq("ativo", True).is_("latitude", "null").execute()
print(f"📍 Imóveis SEM coordenadas (precisam geocodificar): {sem_coords.count}")

# Com coordenadas
com_coords = supabase.table('imoveis').select("id", count="exact")\
    .eq("ativo", True).not_.is_("latitude", "null").execute()
print(f"✅ Imóveis COM coordenadas: {com_coords.count}")

print("\n--- ANÁLISE DO CAMPO 'RUA' ---")

# Busca amostra real para inspecionar o campo rua
amostra = supabase.table('imoveis')\
    .select("id, rua, bairro, cidade")\
    .eq("ativo", True)\
    .is_("latitude", "null")\
    .limit(200)\
    .execute()

imoveis = amostra.data
total_amostra = len(imoveis)

# Contar campos
com_rua = [i for i in imoveis if i.get('rua') and i['rua'].strip()]
sem_rua = [i for i in imoveis if not i.get('rua') or not i['rua'].strip()]
com_bairro = [i for i in imoveis if i.get('bairro') and i['bairro'].strip()]

print(f"\nAmostra analisada (sem coords): {total_amostra} imóveis")
print(f"  ✅ COM campo 'rua' preenchido: {len(com_rua)} ({int(len(com_rua)/total_amostra*100)}%)")
print(f"  ❌ SEM campo 'rua' (vazio/null): {len(sem_rua)} ({int(len(sem_rua)/total_amostra*100)}%)")
print(f"  🏘️  COM campo 'bairro' preenchido: {len(com_bairro)} ({int(len(com_bairro)/total_amostra*100)}%)")

print("\n--- EXEMPLOS DE RUAS ENCONTRADAS (primeiros 20) ---")
for i in com_rua[:20]:
    print(f"  [ID {i['id']}] rua='{i['rua']}' | bairro='{i['bairro']}' | cidade='{i['cidade']}'")

print("\n--- EXEMPLOS SEM RUA (imóveis que SÓ TÊM BAIRRO) ---")
for i in sem_rua[:10]:
    print(f"  [ID {i['id']}] rua=VAZIO | bairro='{i['bairro']}' | cidade='{i['cidade']}'")

print("\n" + "=" * 60)
print("FIM DO DIAGNÓSTICO")
