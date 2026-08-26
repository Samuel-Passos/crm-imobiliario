---
name: find-skills
description: "Pesquisa por novas habilidades, ferramentas e agentes na loja da comunidade (npx skills find)."
---

# /find-skills

Este atalho foi criado para ajudar na busca de novas habilidades.

## Como funciona
Quando o usuário acionar o `/find-skills` ou chamar essa habilidade:
1. Se ele já passou um termo de busca junto (ex: `/find-skills python`), imediatamente execute um comando no terminal: `npx skills find python` e reporte o resultado.
2. Se ele acionou sozinho, pergunte a ele: "Qual tecnologia ou ferramenta você deseja pesquisar na loja de skills?"
3. Se ele disser para instalar algo após a pesquisa, você pode usar `npx skills add <nome-da-skill>`.
