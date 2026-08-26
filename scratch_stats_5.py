from scraper.config_db import supabase

# First get the ID of the Expirados kanban
kanban_res = supabase.table("kanban_colunas").select("id").eq("nome", "Expirados").execute()
if not kanban_res.data:
    print("Coluna 'Expirados' não encontrada!")
    exit(0)
    
expirados_id = kanban_res.data[0]["id"]

# Now find properties in this Kanban that would appear on the map:
# - kanban_coluna_id = expirados_id
# - latitude is not null
# - longitude is not null
# - anuncio_expirado is false or null

# Note: supabase-py doesn't have an easy way to express 'or' with python-like syntax directly in the query builder for nested logic easily sometimes, 
# so we can just query by kanban and georef, and then filter locally.

res = supabase.table("imoveis").select("id, titulo, anuncio_expirado, kanban_coluna_id").eq("kanban_coluna_id", expirados_id).not_.is_("latitude", "null").not_.is_("longitude", "null").execute()

imoveis = res.data
map_visible = []

for imv in imoveis:
    # Condition to appear on map: anuncio_expirado is False or None
    exp = imv.get("anuncio_expirado")
    if exp is False or exp is None:
        map_visible.append(imv)

print(f"Encontrados {len(map_visible)} imóveis na coluna 'Expirados' que estão visíveis no mapa.")
if len(map_visible) > 0:
    for imv in map_visible:
        print(f" - ID: {imv['id']} | Expirado Flag: {imv.get('anuncio_expirado')} | Título: {imv['titulo']}")

