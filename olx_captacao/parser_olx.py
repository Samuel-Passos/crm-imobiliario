"""
parser_olx.py
-------------
Funções de parse do HTML/JavaScript da OLX.

ESTRATÉGIA PRINCIPAL:
  O `window.dataLayer` é extraído diretamente via page.evaluate() no Playwright,
  o que é mais confiável do que parsear o HTML renderizado.

  Para páginas de listagem, usamos page.evaluate() para extrair impressions.
  Para anúncios individuais, usamos o dataLayer extraído via JS.

FALLBACK:
  Se o dataLayer não tiver os dados, recorre ao schema.org JSON-LD no HTML.
"""
import re
import json
from datetime import datetime, timezone
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# PARSE DE PÁGINA DE LISTAGEM (múltiplos anúncios)
# ──────────────────────────────────────────────────────────────────────────────

def extrair_links_do_datalayer(datalayer: list) -> list[dict]:
    """
    Extrai links e list_ids do window.dataLayer de uma página de listagem OLX.
    O dataLayer de listagem contém um campo 'ecommerce' com 'impressions'.
    
    Retorna lista de dicts com: {url, list_id}
    """
    links = []
    seen = set()

    for entry in datalayer:
        ecommerce = entry.get("ecommerce", {})
        impressions = (
            ecommerce.get("impressions") or
            ecommerce.get("items") or
            []
        )
        for item in impressions:
            list_id = str(item.get("id") or item.get("list_id") or "").strip()
            if list_id and list_id not in seen:
                seen.add(list_id)
                url = f"https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/{list_id}"
                links.append({"list_id": list_id, "url": url})

        # Alternativa: events de 'productClick' ou 'detail'
        for event_key in ["productClick", "detail"]:
            ev = ecommerce.get(event_key, {})
            for item in ev.get("products", []):
                list_id = str(item.get("id") or "").strip()
                if list_id and list_id not in seen:
                    seen.add(list_id)
                    url = f"https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/{list_id}"
                    links.append({"list_id": list_id, "url": url})

    return links


def extrair_links_do_html(html: str) -> list[dict]:
    """
    Fallback: extrai links de anúncios de imóveis via regex no HTML.
    Padrão OLX: URLs terminam com -<list_id> (8-12 dígitos).
    """
    pattern = r'href="(https://sp\.olx\.com\.br/vale-do-paraiba[^"]+?-(\d{8,12}))"'
    matches = re.findall(pattern, html)

    seen = set()
    links = []
    for url, list_id in matches:
        if list_id not in seen and "/imoveis/" in url:
            seen.add(list_id)
            links.append({"list_id": list_id, "url": url})

    return links





# ──────────────────────────────────────────────────────────────────────────────
# PARSE DE PÁGINA DE DETALHE (anúncio individual)
# ──────────────────────────────────────────────────────────────────────────────

def extrair_dados_do_datalayer(datalayer: list, url: str) -> Optional[dict]:
    """
    Extrai dados completos de um anúncio a partir do window.dataLayer.
    
    O dataLayer de páginas de detalhe contém:
      - entry['page']['detail']    → dados técnicos (list_id, price, etc.)
      - entry['page']['adDetail']  → dados exibíveis (título, bairro, vendedor, etc.)
      - entry['page']['adProperties'] → lista de propriedades do imóvel
    
    Retorna dict mapeado para colunas da tabela `imoveis`, ou None se falhar.
    """
    if not datalayer:
        return None

    # Busca a entrada com 'page' → 'adDetail'
    page_data = None
    for entry in datalayer:
        if entry.get("page", {}).get("adDetail"):
            page_data = entry["page"]
            break

    if not page_data:
        return None

    detail = page_data.get("detail", {})
    ad_detail = page_data.get("adDetail", {})
    ad_properties = page_data.get("adProperties", [])

    # Verifica se o anúncio foi encontrado (não é página de erro)
    subject = ad_detail.get("subject", "")
    if not subject or "não encontrado" in subject.lower():
        return None

    # Converte adProperties em dict para acesso fácil
    props = {p["name"]: p.get("value") for p in ad_properties if p.get("name")}

    # Extrai list_id (obrigatório)
    list_id = (
        detail.get("list_id") or
        ad_detail.get("listId") or
        _extrair_list_id_da_url(url)
    )
    if not list_id:
        return None

    dados = {
        # Identificação
        "list_id": int(list_id),
        "ad_id": _parse_ad_id(ad_detail.get("adId"), list_id),  # UUID ou int → bigint
        "url": url,
        "origem": "OLX",

        # Título e descrição
        "titulo": subject,

        # Tipo de negócio e imóvel
        "tipo_negocio": _inferir_tipo_negocio(
            props.get("real_estate_type") or ad_detail.get("real_estate_type") or ""
        ),
        "tipo_imovel": props.get("real_estate_type") or ad_detail.get("real_estate_type"),
        "categoria": ad_detail.get("subCategory") or ad_detail.get("category"),
        "categoria_id": detail.get("category_id"),
        "categoria_pai": ad_detail.get("mainCategory"),
        "subtipo": props.get("re_types") or ad_detail.get("re_types"),

        # Preço e Taxas (Financeiro)
        "preco": _parse_preco(detail.get("price") or ad_detail.get("price")),
        "preco_str": _formatar_preco_str(detail.get("price") or ad_detail.get("price")),
        "preco_label": _inferir_label_preco(
            props.get("real_estate_type") or ad_detail.get("real_estate_type") or ""
        ),
        "condominio": _parse_preco(props.get("condominio") or props.get("condominium") or ad_detail.get("condominio")),
        "condominio_str": _formatar_preco_str(props.get("condominio") or props.get("condominium") or ad_detail.get("condominio")),
        "iptu": _parse_preco(props.get("iptu") or ad_detail.get("iptu")),
        "iptu_str": _formatar_preco_str(props.get("iptu") or ad_detail.get("iptu")),

        # Características do imóvel
        "area_m2": props.get("size") or (f"{ad_detail.get('size')}m²" if ad_detail.get("size") else None),
        "area_construida_m2": _parse_int(props.get("size")),
        "area_terreno_m2": _parse_int(props.get("land_size")),
        "quartos": _parse_int(props.get("rooms") or ad_detail.get("rooms")),
        "banheiros": _parse_int(props.get("bathrooms") or ad_detail.get("bathrooms")),
        "vagas": _parse_int(props.get("garage_spaces") or ad_detail.get("garage_spaces")),
        "suites": _parse_int(props.get("suites")),
        "salas": _parse_int(props.get("rooms_count")),
        "andar": _parse_int(props.get("floor") or props.get("andar")),

        # Características (texto) e Outros
        "caracteristicas_imovel": props.get("re_features") or ad_detail.get("re_features"),
        "caracteristicas_condominio": props.get("re_complex_features") or ad_detail.get("re_complex_features"),
    }
    
    aceita_permuta = props.get("exchange")
    if aceita_permuta is not None:
        dados["aceita_permuta"] = "sim" if aceita_permuta in ["true", True] else "nao"
    
    dados.update({
        # Localização
        "bairro": ad_detail.get("neighbourhood"),
        "bairro_id": detail.get("neighbourhood_id"),
        "cidade": ad_detail.get("municipality"),
        "cidade_id": detail.get("city_id"),
        "cep": detail.get("zipcode"),
        "estado": ad_detail.get("state") or "SP",
        "rua": ad_detail.get("street") or ad_detail.get("address") or detail.get("street"),
        "numero": ad_detail.get("addressNumber") or detail.get("addressNumber"),
        "ddd": ad_detail.get("ddd"),
        "zona": detail.get("zone_name"),
        "regiao": ad_detail.get("region"),

        # Vendedor
        "vendedor_nome": ad_detail.get("sellerName"),
        # vendedor_account_id é bigint no banco — se OLX retornar UUID, descarta (None)
        "vendedor_account_id": _parse_bigint_or_none(ad_detail.get("sellerPublicAccountId")),
        "anuncio_profissional": bool(ad_detail.get("professionalAd")),

        # Controle
        "ativo": True,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "data_criacao_ts": detail.get("adDate"),
        "data_criacao": _parse_timestamp(ad_detail.get("adDate")),
        "telefone_pesquisado": False,
        "anuncio_expirado": False,
    })

    # Remove campos None para não sobrescrever dados existentes no upsert
    dados = {k: v for k, v in dados.items() if v is not None}

    return dados


def complementar_com_schema(dados: dict, html: str) -> dict:
    """
    Complementa os dados já extraídos do dataLayer com informações do
    schema.org (JSON-LD) presentes no HTML — principalmente fotos e descrição.
    """
    schema = _extrair_schema_org(html)
    if not schema:
        return dados

    # Descrição
    if "descricao" not in dados:
        obj = schema.get("Object", {})
        if obj.get("description"):
            dados["descricao"] = re.sub(r'<[^>]+>', ' ', obj["description"]).strip()

    # CEP
    if "cep" not in dados:
        addr = schema.get("location", {}).get("address", {})
        if addr.get("postalCode"):
            dados["cep"] = addr["postalCode"]

    # Fotos
    if "foto_capa" not in dados or "fotos" not in dados:
        images = schema.get("Object", {}).get("image", [])
        if images and isinstance(images, list):
            titulo = dados.get("titulo", "Imóvel OLX")
            fotos = []
            for img in images:
                url = img.get("contentUrl")
                if url:
                    url_limpa = url.split("?")[0]
                    fotos.append({"url": url_limpa, "alt": titulo})
                    
            if fotos:
                dados.setdefault("foto_capa", fotos[0]["url"])
                dados.setdefault("fotos", fotos)
                dados.setdefault("total_fotos", len(fotos))

    # 3. Tentativa de extrair a rua do INITIAL_STATE (HTML unescaped) caso o dataLayer não tenha
    if not dados.get("rua"):
        rua_html = _extrair_rua_do_html(html)
        if rua_html:
            dados["rua"] = rua_html

    return dados


# ──────────────────────────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ──────────────────────────────────────────────────────────────────────────────

def _extrair_schema_org(html_str: str) -> dict:
    """Extrai o JSON-LD de schema.org do HTML."""
    match = re.search(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html_str, re.DOTALL
    )
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    return {}


def _extrair_rua_do_html(html_str: str) -> Optional[str]:
    """
    Busca o endereço diretamente no INITIAL_STATE do HTML (mesmo que escapado).
    Contorna casos onde a OLX oculta a rua do dataLayer, mas envia no front-end.
    """
    import html as html_lib
    texto = html_lib.unescape(html_str)
    
    print("  [DEBUG] Procurando rua via HTML fallback...")
    
    # regex mais robusta
    match = re.search(r'"location"\s*:\s*\{[^}]*"address"\s*:\s*"([^"]+)"', texto)
    if match:
        rua = match.group(1).strip()
        print(f"  [DEBUG] Match regex encontrado: {rua}")
        if rua and rua.lower() not in ["null", "none", "undefined"]:
            return rua
    else:
        # tentar outra regex
        match2 = re.search(r'"address"\s*:\s*"([^"]+)"', texto)
        if match2:
            print(f"  [DEBUG] Segunda regex encontrou address: {match2.group(1)}")
            
    print("  [DEBUG] Nenhuma regex deu match na rua no HTML.")
    return None


def _extrair_list_id_da_url(url: str) -> Optional[str]:
    """Extrai list_id do final da URL OLX."""
    match = re.search(r'-(\d{8,12})(?:\?.*)?$', url)
    return match.group(1) if match else None


def _inferir_tipo_negocio(tipo_imovel_str: str) -> str:
    """Infere 'venda' ou 'aluguel' a partir do campo tipo_imovel."""
    s = tipo_imovel_str.lower()
    if "aluguel" in s or "locação" in s or "locacao" in s:
        return "aluguel"
    return "venda"


def _inferir_label_preco(tipo_imovel_str: str) -> str:
    """Retorna 'Aluguel' ou 'Venda'."""
    return "Aluguel" if _inferir_tipo_negocio(tipo_imovel_str) == "aluguel" else "Venda"


def _parse_preco(valor) -> Optional[float]:
    """Converte valor para float."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    limpo = re.sub(r'[^\d.,]', '', str(valor)).replace(',', '.')
    try:
        return float(limpo)
    except (ValueError, TypeError):
        return None


def _formatar_preco_str(valor) -> Optional[str]:
    """Formata preço como 'R$ X.XXX'."""
    preco = _parse_preco(valor)
    if preco is None:
        return None
    return f"R$ {preco:,.0f}".replace(",", ".")


def _parse_int(valor) -> Optional[int]:
    """Converte valor para int."""
    if valor is None:
        return None
    try:
        return int(str(valor).strip())
    except (ValueError, TypeError):
        return None


def _parse_timestamp(valor) -> Optional[str]:
    """Converte timestamp Unix para ISO 8601."""
    if not valor:
        return None
    try:
        ts = int(valor)
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return None


def _parse_ad_id(raw_ad_id, list_id_fallback) -> int:
    """
    Converte o adId do OLX para bigint.
    
    O OLX pode retornar adId como:
      - int ou string numérica → converte para int
      - UUID (ex: '1c618df6-7c30-4088-b92a-27dce788f018') → usa list_id como fallback
      - None → usa list_id como fallback
    
    A coluna `ad_id` na tabela `imoveis` é bigint NOT NULL.
    """
    if raw_ad_id is not None:
        try:
            return int(str(raw_ad_id).strip())
        except (ValueError, TypeError):
            pass
    return int(list_id_fallback)


def _parse_bigint_or_none(valor) -> Optional[int]:
    """
    Converte valor para bigint, ou retorna None se for UUID / não numérico.
    Usado para colunas bigint que o OLX pode retornar como UUID string.
    """
    if valor is None:
        return None
    try:
        return int(str(valor).strip())
    except (ValueError, TypeError):
        return None  # UUID ou formato não numérico — descarta silenciosamente
