import re

with open('/home/samuel/Desktop/Scraper_antigravity/crm-imobiliario/src/pages/kanban/ImovelModal.tsx', 'r') as f:
    content = f.read()

# Remove state
content = re.sub(r'const \[editando, setEditando\] = useState\(false\)', '', content)

# Replace simple ternaries: {editando ? <input ... /> : <div ...>...</div>}
# Note: we should match `{editando \? (<input[^>]+>) : <div[^>]*>.*?</div>}`
content = re.sub(r'\{editando \? (<input[^>]+>) : <div[^>]*>.*?</div>\}', r'\1', content, flags=re.DOTALL)

# Selects: {editando ? ( ... ) : <div... }
content = re.sub(r'\{editando \? \(\s*(<select.*?</select>)\s*\)\s*: <div[^>]*>.*?</div>\}', r'\1', content, flags=re.DOTALL)

# Checkboxes
content = re.sub(r'onChange=\{e => editando && set', r'onChange={e => set', content)
content = re.sub(r'onClick=\{.*?editando && set.*?', r'onClick={() => set', content)
content = re.sub(r'disabled=\{!editando\}', r'', content)
content = re.sub(r'cursor:\s*editando\s*\?\s*\'pointer\'\s*:\s*\'default\'', r"cursor: 'pointer'", content)

# !editando && conditions
content = re.sub(r'\{!editando && \((.*?)\) && \(', r'{(\1) && (', content)
content = re.sub(r'\{!editando && (\w+) && \(', r'{\1 && (', content)

# handleCancelar
content = re.sub(r'setEditando\(false\)', '', content)

# Footer buttons: 
# {!editando ? ( ... ) : ( <> ... </> )} 
footer_pattern = r'\{!editando \? \(\s*<button className="btn btn-primary" onClick=\{.*? \)\s*:\s*\(\s*<>\s*(<button.*?Salvar.*?</button>)\s*(<button.*?Cancelar.*?</button>)\s*</>\s*\)\}'
content = re.sub(footer_pattern, r'\1\n                                \2', content, flags=re.DOTALL)

with open('/home/samuel/Desktop/Scraper_antigravity/crm-imobiliario/src/pages/kanban/ImovelModal.tsx', 'w') as f:
    f.write(content)

print("Processamento concluído.")
