# Fluxo de Trabalho Otimizado com IA

Este documento define a arquitetura de trabalho utilizando o ecossistema de agentes (Graphify, Skills e Karpathy Guidelines) instalado no projeto. O objetivo é garantir **economia de tokens, precisão de código e evolução contínua**.

---

## 1. O Triângulo de Ferramentas Instaladas

Nós configuramos 3 pilares fundamentais no seu repositório:

1. **Graphify (O Cartógrafo):** Cria um mapa (Árvore Sintática) do seu projeto. Em vez de a IA ler todos os arquivos (gastando milhares de tokens), ela lê apenas o mapa e vai direto ao ponto.
2. **CLI de Skills (A Biblioteca):** Permite adicionar novos "conhecimentos especialistas" (ex: bibliotecas específicas) via terminal usando `npx skills add`.
3. **Karpathy Guidelines (O Mentor):** Uma *skill* já instalada (`.agents/skills/karpathy-guidelines`) que obriga a IA a escrever código simples, fazer mudanças cirúrgicas e evitar "overengineering" (complicação desnecessária).

---

## 2. Como usar isso no dia a dia? (Passo a Passo do Desenvolvimento)

Para tirar o máximo proveito dessa estrutura, adote o seguinte fluxo quando me pedir uma nova funcionalidade no Scraper ou CRM:

### Fase A: O Pedido 
Seja direto no que você quer, mas **não precisa colar arquivos inteiros no chat**. 
* ✅ *Faça assim:* "Crie um endpoint no FastAPI para listar os leads expirados do banco."
* ❌ *Evite:* Colar o `app.py`, o `models.py` e o `schema.py` no chat. O Graphify fará com que eu encontre essas conexões sozinho de forma muito mais barata.

### Fase B: A Implementação (Modo Karpathy)
Você notará que, devido às *Karpathy Guidelines*, minhas respostas serão:
1. Mais curtas.
2. As edições serão feitas apenas nas linhas exatas (mudanças cirúrgicas), e não reescrevendo o arquivo todo.
3. Se o pedido for muito complexo, eu vou te apresentar minhas premissas e pedir sua aprovação antes de sair codando.

### Fase C: A Manutenção do Mapa (Graphify)
* **Automático:** Quando **eu** altero os arquivos de código para você, o meu sistema roda a atualização do grafo automaticamente em segundo plano.
* **Manual:** Se **você** fizer uma grande refatoração manual (ex: mudar o nome de dezenas de pastas ou arquivos pelo seu editor de código), é recomendado rodar `graphify update .` no terminal para que o "mapa" da IA não fique defasado.

### Fase D: A Evolução (O Botão "Aprender")
* **Adicionando novas Tecnologias:** Decidiu usar um banco diferente ou um pacote novo de UI no React? Rode `npx skills find <nome>` e instale a diretriz dele.
* **Corrigindo a IA:** Se eu cometer um erro comportamental, não apenas corrija o código. Digite no chat: `/learn Sempre que fizer X, faça Y`. Eu atualizarei o `GEMINI.md` de forma inteligente.

> [!TIP]
> **Dica de Ouro:** Quanto melhor alimentarmos a pasta `conhecimentos/` (como o arquivo `arquitetura.md` que criamos), mais autônomo o agente será para resolver bugs complexos envolvendo múltiplos serviços como o Robô de Chat e a API do Captador.
