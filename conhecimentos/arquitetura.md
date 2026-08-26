# Arquitetura do Sistema: CRM Imobiliário & Scraper

Este documento serve como mapa mental para ferramentas de IA (como Graphify) e desenvolvedores entenderem a estrutura do ecossistema.

## Visão Geral dos Serviços

O projeto principal é dividido em múltiplos microserviços/módulos que rodam simultaneamente. O script principal de orquestração é o `start_all.sh`.

### 1. Scraper Backend (Porta 8765)
- **Diretório:** `/scraper`
- **Tecnologia:** FastAPI (Python)
- **Responsabilidade:** Gerencia o banco de dados principal, serve endpoints de status e provavelmente interage com os scripts de raspagem e banco de dados.

### 2. CRM Frontend (Porta 5173)
- **Diretório:** `/crm-imobiliario`
- **Tecnologia:** React/Vue via Vite (Node.js)
- **Responsabilidade:** Interface do usuário (Kanban e gestão de leads). É exposto publicamente usando localtunnel (ex: `samuel.loca.lt`).

### 3. API Captador OLX (Porta 8768)
- **Diretório:** `/olx_captacao`
- **Tecnologia:** Python
- **Responsabilidade:** Extração de dados da OLX (`api_captador.py`). Também conta com robôs paralelos para baixar fotos de imóveis cujos proprietários aceitaram contato (`fase3_baixar_fotos_aceitou.py`).

### 4. Robô de Disponibilidade (Porta 8766)
- **Diretório:** `/robo_disponibilidade`
- **Tecnologia:** FastAPI + Cloudflare Tunnel
- **Responsabilidade:** Escuta webhooks via túnel Cloudflare e automatiza a verificação de disponibilidade de imóveis.

### 5. Monitor de Chat / Prospecção
- **Diretório:** `/robo_chat_prospeccao`
- **Tecnologia:** Python (`orquestrador_reverso.py`)
- **Responsabilidade:** Robô (Drip Campaign) que monitora o chat e faz envios automatizados.
- **Atenção (Regra Crítica):** Ao enviar mensagens via chat, NÃO se deve utilizar loops de digitação humana simulada (como `page.keyboard.press()`). Deve-se usar o método nativo de preenchimento (`await locator.fill(texto)`) e enviar com `Enter`, pois a digitação humana simulada causa bugs com caracteres acentuados.

## Ferramentas e Integrações Externas
- **Túneis:** `loca.lt` (para o CRM) e `cloudflared` (para webhooks do robô de disponibilidade).
- **APIs externas documentadas:** *casadosdados* (para prospecção ou enriquecimento de dados CNPJ).

## Regras e Fluxo de Desenvolvimento
- Nunca presumir que o túnel (ex: porta 5000 / loca.lt) está funcionando sem testá-lo primeiro.
- Para testes de inicialização local ou reset, utiliza-se `start_all.sh` e uma série de scripts que ficam na raiz (os arquivos `scratch_*.py`).

*(Este documento pode ser indexado pelo Graphify para trazer melhor contexto de pastas ao modificar a estrutura principal)*
