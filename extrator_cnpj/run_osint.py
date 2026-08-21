import os
from pipeline import step3_enriquecer_opencnpj, step6_salvar_supabase

# Vamos rodar apenas o enriquecimento e a sincronização para os top 5
print("Iniciando Enriquecimento OSINT (Step 3)...")
step3_enriquecer_opencnpj(limit=5)

print("Sincronizando com Supabase (Step 6)...")
step6_salvar_supabase()

print("Finalizado!")
