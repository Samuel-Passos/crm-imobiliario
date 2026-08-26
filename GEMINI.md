# GEMINI.md — Instruções Específicas: Scraper & CRM Imobiliário

## Ambiente Técnico e Portas
- **Scraper Backend (FastAPI):** Porta `8765`
- **Robô Disponibilidade (FastAPI + Cloudflare):** Porta `8766`
- **API Captador OLX:** Porta `8768`
- **CRM Frontend (Vite/React):** Porta `5173`
- **Túnel Principal:** Localtunnel apontando para a porta 5173 (ex: `samuel.loca.lt`)

## Regras Críticas de Desenvolvimento
- **Monitor de Chat (Prospecção):** Ao enviar mensagens via chat, **NÃO utilize loops de digitação humana** (ex: `page.keyboard.press()`). Você deve usar o método nativo de inserção de texto (ex: `await locator.fill(texto)` ou similar) seguido de `Enter`. A digitação simulada quebra caracteres acentuados.
- **Túneis:** Antes de assumir que o sistema web está acessível remotamente, valide se o processo do Cloudflare ou loca.lt está ativo e respondendo.
- **Testes Locais:** Para subir os serviços, utilizar os scripts de inicialização, como `start_all.sh`.
- **Evolução de Conhecimento:** Novas descobertas arquiteturais devem ser gravadas na pasta `conhecimentos/` para que a ferramenta Graphify as indexe.
- **Workflow BDD + TDD + Karpathy:** Ao receber um pedido para uma nova feature, o agente DEVE, obrigatoriamente:
  1. Começar escrevendo o documento de especificação/plano (.md) para alinhar as regras de negócio.
  2. Pensar na arquitetura de testes antes de escrever o código.
  3. Escrever os testes automatizados seguindo a sequência lógica: Banco de Dados ➔ Regras de Negócio/Algoritmo ➔ Frontend.
  4. Somente após escrever os testes (que devem falhar inicialmente), escrever o código final usando a simplicidade e a precisão cirúrgica das *Karpathy Guidelines* para fazê-los passar.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
