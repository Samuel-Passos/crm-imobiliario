import bs4
import re

with open("dom_dump.txt", "r", encoding="utf-8") as f:
    html = f.read()

soup = bs4.BeautifulSoup(html, "html.parser")
els = soup.find_all(lambda tag: tag.has_attr("data-testid") and any(x in tag["data-testid"].lower() for x in ["message", "bubble", "chat"]))

for el in els:
    print(f"Tag: {el.name}, data-testid: {el['data-testid']}, class: {el.get('class')}")
    # print snippet of text if any
    text = el.get_text(strip=True)
    if text:
        print(f"  Text: {text[:50]}...")

