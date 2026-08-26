from scraper.config_db import supabase

ids_to_fix = [3674, 3686, 3667, 179, 3364]

for imovel_id in ids_to_fix:
    try:
        res = supabase.table("imoveis").update({"anuncio_expirado": True}).eq("id", imovel_id).execute()
        print(f"ID {imovel_id} atualizado com sucesso.")
    except Exception as e:
        print(f"Erro ao atualizar ID {imovel_id}: {e}")

print("Correção concluída.")
