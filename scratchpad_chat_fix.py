import re

def extract_list_id(url):
    m = re.search(r'-(\d+)$', url)
    if m:
        return m.group(1)
    return None

print(extract_list_id("https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/vendo-apto-1-dorm-mobiliado-jd-augusta-house-vale-em-sao-jose-dos-campos-sp-1486150508"))
