import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_MAPS_API_KEY")
url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

query = "FERREIRINHA IMOVEIS LTDA SAO JOSE DOS CAMPOS"
params = {
    "query": query,
    "key": key
}

print(f"Buscando por: {query}")
res = requests.get(url, params=params)
data = res.json()

if data.get("status") == "OK":
    place = data["results"][0]
    place_id = place["place_id"]
    print(f"✓ Encontrado: {place['name']} (ID: {place_id})")
    
    # Busca detalhes (telefone, site)
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    details_params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,website,international_phone_number",
        "key": key
    }
    res_details = requests.get(details_url, params=details_params)
    details = res_details.json()
    
    if details.get("status") == "OK":
        result = details["result"]
        print(f"Telefone: {result.get('formatted_phone_number')}")
        print(f"Site: {result.get('website')}")
    else:
        print(f"Erro nos detalhes: {details.get('status')}")
else:
    print(f"Erro na busca: {data.get('status')}")
    if data.get("error_message"):
        print(f"Mensagem: {data['error_message']}")
