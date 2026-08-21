# Robô de Disponibilidade — CRM Imobiliário SJC

Automação para atualização de disponibilidade de imóveis via WhatsApp.

## Estrutura

```
robo_disponibilidade/
├── importar_planilha.py   # Etapa 2: importa .xlsx → Supabase
├── requirements.txt       # Dependências Python
├── .env.example           # Modelo de configuração
└── .env                   # Suas credenciais reais (não commitar!)
```

## Etapas do Robô

| Etapa | Arquivo | Descrição |
|-------|---------|-----------|
| 2 | `importar_planilha.py` | Lê .xlsx e faz upsert no Supabase ✅ |
| 3 | `enviar_mensagens.py` | Automação ZapZap com Playwright |
| 4 | `templates.py` | Templates de mensagem |
| 5 | `agendador.sh` | Cron job Linux |
| 6 | `ler_respostas.py` | Lê respostas e atualiza o banco |

## Configuração

```bash
# 1. Clone e entre na pasta
cd robo_disponibilidade

# 2. Crie o ambiente virtual
python -m venv .venv
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as credenciais
cp .env.example .env
# Edite o .env com sua URL e chave do Supabase
```

## Uso — Etapa 2

```bash
# Com o arquivo padrão (imoveis.xlsx na mesma pasta):
python importar_planilha.py

# Especificando outro caminho:
python importar_planilha.py --arquivo /caminho/para/planilha_junho.xlsx
```

### Exemplo de saída

```
🏠 Robô de Disponibilidade — Etapa 2: Importação de Planilha
   Início: 06/04/2026 10:30:00

====================================================
  RESUMO DA IMPORTAÇÃO — ETAPA 2
====================================================
  Total lido da planilha :    342
  Registros inseridos    :     15  ✅
  Registros atualizados  :    327  🔄
  Ignorados (sem ref.)   :      0  ⚠️
  Erros                  :      0  ❌
====================================================
```

## Lógica de Preservação de Dados

As colunas abaixo são **preservadas** se já tiverem valor no banco:

- `ultimo_contato` — data/hora do último contato via WhatsApp
- `resposta` — `'SIM'`, `'NÃO'` ou `NULL`
- `data_resposta` — quando o proprietário respondeu
- `proximo_contato` — data agendada para novo contato

Ou seja: importar a planilha atualizada **nunca apaga o histórico** do robô.
