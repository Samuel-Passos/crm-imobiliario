import pandas as pd
from pathlib import Path

csv_path = Path("output/02_filtrado.csv")
if not csv_path.exists():
    print("Arquivo 02_filtrado.csv não encontrado!")
    exit(1)

df = pd.read_csv(csv_path, dtype=str)

# CNAEs de alto valor (Imobiliárias e Construtoras)
CNAE_IMOBILIARIA = "6821801"
CNAE_CONSTRUTORA = "4120400"

# Cria uma coluna de prioridade
def get_priority(cnae):
    if cnae == CNAE_IMOBILIARIA: return 0
    if cnae == CNAE_CONSTRUTORA: return 1
    return 2

df['priority'] = df['cnae'].apply(get_priority)

# Ordena por prioridade (os 0 e 1 no topo) e sorteia dentro da prioridade
df = df.sort_values('priority').drop(columns=['priority'])

# Salva de volta
df.to_csv(csv_path, index=False)
print(f"Base reorganizada: {len(df)} empresas. Imobiliárias agora estão no topo!")
