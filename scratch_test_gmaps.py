from playwright.sync_api import sync_playwright
import re
import urllib.parse
import time

def test_gmaps(address):
    print(f"Buscando: {address}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        encoded = urllib.parse.quote(address)
        page.goto(f"https://www.google.com/maps/search/{encoded}")
        
        try:
            page.wait_for_url(lambda url: '/@' in url, timeout=10000)
            url = page.url
            print(f"URL: {url}")
            match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
            if match:
                lat, lon = match.groups()
                print(f"Coordenadas: {lat}, {lon}")
            else:
                print("Coordenadas não encontradas na URL.")
        except Exception as e:
            print(f"Erro: {e}")
            print(f"URL final: {page.url}")
        
        browser.close()

if __name__ == "__main__":
    test_gmaps("Rua dos Mutuns, Jardim Uirá, São José dos Campos, SP")
