import re
from bs4 import BeautifulSoup

with open("chat_dump.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Procurar mensagens
# O OLX Chat costuma ter um <ul> ou lista de mensagens
messages = soup.find_all(lambda tag: tag.name == "div" and tag.text and "Samuel" in tag.text)
for m in messages[-5:]:
    print(f"[{m.name}] cls='{m.get('class', [])}': {m.text[:100]}")

print("---")
# Buscar spans ou divs com 'data-testid'
for el in soup.find_all(attrs={"data-testid": re.compile("message")}):
    print(f"data-testid={el.get('data-testid')} -> {el.text[:100]}")

