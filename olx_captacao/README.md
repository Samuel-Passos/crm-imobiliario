# OLX Captação — Módulo de Scraping Imobiliário

Módulo **completamente separado** do `/scraper/` existente.
Coleta imóveis à venda/aluguel em São José dos Campos da OLX.

---

## Estrutura

```
olx_captacao/
├── .env                    → Credenciais Supabase + configurações
├── pyproject.toml          → Dependências Python
├── main.py                 → CLI principal (ponto de entrada)
├── fase1_coleta_links.py   → Navega listagem OLX e coleta links
├── fase2_extrai_dados.py   → Extrai dados de cada anúncio
├── parser_olx.py           → Parse do HTML/JS da OLX
└── supabase_client.py      → Cliente Supabase
```

---

## Instalação (primeira vez)

```bash
cd olx_captacao/
python3 -m venv .venv
.venv/bin/pip install playwright supabase python-dotenv httpx
.venv/bin/playwright install chromium
```

---

## Uso

### Ativar o ambiente virtual
```bash
cd olx_captacao/
source .venv/bin/activate
```

### Fase 1 — Coleta de links
Navega pelas páginas de listagem e salva os links na tabela `links_anuncios` com `status='pendente'`.

```bash
python main.py fase1                  # Coleta até 50 páginas
python main.py fase1 --max-paginas 5  # Coleta apenas 5 páginas (teste)
```

### Fase 2 — Extração de dados
Para cada link pendente, entra no anúncio e extrai os dados para a tabela `imoveis`.

```bash
python main.py fase2              # Processa até 50 links pendentes
python main.py fase2 --lote 10   # Processa apenas 10 links (teste)
```

### Execução completa (Fase 1 + Fase 2)
```bash
python main.py tudo
python main.py tudo --max-paginas 10 --lote 100
```

### Teste de uma URL específica (sem salvar no banco)
```bash
python main.py teste --url "https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/ANUNCIO"
```

---

## Tabelas do Supabase utilizadas

### `links_anuncios`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `url` | TEXT | URL do anúncio |
| `list_id` | BIGINT | ID da listagem OLX |
| `status` | TEXT | `pendente` → `processado` / `expirado` / `erro` |

### `imoveis`
Upsert por `list_id`. Os principais campos preenchidos:
- `titulo`, `descricao`, `url`, `origem` (= "OLX")
- `tipo_negocio` (venda/aluguel), `tipo_imovel`, `categoria`
- `preco`, `preco_str`, `area_m2`, `quartos`, `banheiros`, `vagas`
- `bairro`, `cidade`, `estado`, `cep`, `zona`, `regiao`
- `vendedor_nome`, `vendedor_account_id`
- `foto_capa`, `fotos`, `total_fotos`
- `caracteristicas_imovel`, `caracteristicas_condominio`
- `ativo=True`, `scraped_at`, `data_criacao`, `telefone_pesquisado=False`

---

## Configurações (.env)

```env
SUPABASE_URL=https://dfpyxcpadhkywzivllpp.supabase.co
SUPABASE_KEY=sb_secret_...      # service_role key (escrita no banco)
CHROME_PROFILE_PATH=/home/samuel/.config/google-chrome
DELAY_MIN_SEGUNDOS=2            # Delay mínimo entre requisições
DELAY_MAX_SEGUNDOS=5            # Delay máximo entre requisições
MAX_PAGINAS=50                  # Máximo de páginas por execução
```

---

## Como funciona o anti-bot

1. **User-Agent** realístico (Chrome 124 em Linux)
2. **Oculta WebDriver** via JavaScript (`navigator.webdriver = undefined`)
3. **Delay aleatório** entre requisições (2-5s por padrão)
4. **Parada automática** após 5 falhas consecutivas (proteção contra ban)
5. **Detecção de Cloudflare** — links bloqueados permanecem `pendente` para retry

---

## Fluxo completo

```
OLX Listagem → fase1 → links_anuncios (status=pendente)
                               ↓
                fase2 → parser_olx → imoveis (upsert por list_id)
                               ↓
               links_anuncios (status=processado)
                               ↓
         (existente) scraper/phone_extractor → telefones
```
