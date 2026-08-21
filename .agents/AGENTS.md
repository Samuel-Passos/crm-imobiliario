
## Nova Diretriz (Prevenção de Alucinação): Envio de Chat
Ao enviar mensagens de chat automatizadas (ex: OLX), **NÃO utilize loops de digitação humana** simulando o pressionamento tecla por tecla (ex: `page.keyboard.press()`). Você deve copiar e colar o texto completo no campo usando o método nativo de inserção (ex: `await locator.fill(texto)`) seguido de `Enter`. Essa abordagem já havia sido validada pelo usuário e a substituição por digitação simulada causou erros de formatação de caracteres acentuados.
