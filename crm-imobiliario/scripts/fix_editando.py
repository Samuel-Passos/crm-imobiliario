import re

with open('/home/samuel/Desktop/Scraper_antigravity/crm-imobiliario/src/pages/kanban/ImovelModal.tsx', 'r') as f:
    content = f.read()

# 1. Remove useState(false) for editando
content = re.sub(r'const \[editando, setEditando\] = useState\(false\)[^\n]*\n?', '', content)

# 2. Replace {editando ? <input ... /> : <div ...>...</div>}
content = re.sub(r'\{editando \?\s*(<input[^>]+>)\s*:\s*<div[^>]*>.*?</div>\}', r'\1', content, flags=re.DOTALL)

# 3. Replace {editando ? ( ... ) : <div... }
content = re.sub(r'\{editando \?\s*\(\s*(<select.*?</select>)\s*\)\s*:\s*<div[^>]*>.*?</div>\}', r'\1', content, flags=re.DOTALL)

# 4. Remove `editando &&` from onChange / onClick
content = re.sub(r'onChange=\{e => editando && set', r'onChange={e => set', content)
content = re.sub(r'onClick=\{.*?editando && set.*?', r'onClick={() => set', content)
content = re.sub(r'disabled=\{!editando\}', r'', content)
content = re.sub(r'cursor:\s*editando\s*\?\s*\'pointer\'\s*:\s*\'default\'', r"cursor: 'pointer'", content)

# 5. Remove `!editando && ` checks for the fast actions (so they are always visible)
content = re.sub(r'\{!editando && \((.*?)\) && \(', r'{(\1) && (', content)
content = re.sub(r'\{!editando && (\w+) && \(', r'{\1 && (', content)

# 6. Remove checking from checkboxes inside <span> expressions
content = re.sub(r'\{editando \? (.*?) : (.*?)\}', r'\1', content)

# 7. handleCancelar - remove setEditando 
content = re.sub(r'setEditando\(false\)[^\n]*\n?', '', content)

# 8. Rodapé: Replace {!editando ? <button> ... : <> ... </>} with just <> ... </>
content = re.sub(r'\{!editando \? \(\s*<button className="btn btn-primary" onClick=\{[^\}]*\}[^\>]*>\s*.*?Editar dados\s*</button>\s*\)\s*:\s*\(\s*<>\s*(<button.*?Salvar.*?</button>)\s*(<button.*?Cancelar.*?</button>)\s*</>\s*\)\}', 
    r'\n                                \1\n                                \2\n', content, flags=re.DOTALL)

# 9. In the complex field, we had {editando ? ( <Field label="Telefone"> <input... /> </Field> ) : ( ... )}
# We want just the read mode for the complex field, OR just keeping it editable. Let's make it always editable for the simple string, 
# But wait, the user's specific request was for the complicated layout (the Telefones section): 
# "os botões de ligar e enviar mensagem, quero que fiquem do lado de fora lado esquerdo do input, para cada telefone que tiver"
# "quando tiver apenas 1 telefone, colocar o nome do input Telefone origem, quando tiver 2 telefones colocar o nome Telefone Botão, Telefone Descrição"
# "Com o telefone dentro do input e os botões de ligar e enviar mensagem respectivamente do lado de fora"

with open('/home/samuel/Desktop/Scraper_antigravity/crm-imobiliario/src/pages/kanban/ImovelModal.tsx', 'w') as f:
    f.write(content)

print("Processamento base concluído.")
