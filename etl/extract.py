import os
import requests
import logging

logger = logging.getLogger(__name__)


def get_access_token(app_id: str, secret_key: str, refresh_token: str) -> str:
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": app_id,
        "client_secret": secret_key,
        "refresh_token": refresh_token,
    }
    r = requests.post(url, data=payload)
    r.raise_for_status()
    data = r.json()
    # Persistir el nuevo refresh_token para la próxima ejecución
    os.environ["MELI_REFRESH_TOKEN"] = data["refresh_token"]
    return data["access_token"]


def search_items(token: str, query: str, condition: str, page_size: int, max_records: int) -> list:
    url = "https://api.mercadolibre.com/sites/MLA/search"
    headers = {"Authorization": f"Bearer {token}"}
    items = []
    offset = 0

    while len(items) < max_records:
        params = {
            "q": query,
            "condition": condition,
            "limit": page_size,
            "offset": offset,
        }
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json()

        results = data.get("results", [])
        if not results:
            break

        items.extend(results)
        total = data["paging"]["total"]
        offset += page_size
        logger.info(f"Extraídos {len(items)}/{min(max_records, total)} items")

        if offset >= min(max_records, total):
            break

    return items[:max_records]


def get_items_detail(token: str, item_ids: list) -> list:
    url = "https://api.mercadolibre.com/items/bulk"
    headers = {"Authorization": f"Bearer {token}"}
    details = []

    # Bulk acepta hasta 20 ids por llamada
    for i in range(0, len(item_ids), 20):
        batch = item_ids[i:i + 20]
        params = {"ids": ",".join(batch)}
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        details.extend([item["body"] for item in r.json() if item.get("status_code") == 200])

    return details


def get_sellers_detail(token: str, seller_ids: list) -> list:
    url = "https://api.mercadolibre.com/users/bulk"
    headers = {"Authorization": f"Bearer {token}"}
    sellers = []

    for i in range(0, len(seller_ids), 20):
        batch = seller_ids[i:i + 20]
        params = {"ids": ",".join(str(s) for s in batch)}
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        sellers.extend([s["body"] for s in r.json() if s.get("status_code") == 200])

    return sellers


def get_usd_rate(token: str) -> float:
    url = "https://api.mercadolibre.com/currency_conversions/search"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, params={"from": "ARS", "to": "USD"})
    r.raise_for_status()
    return r.json().get("ratio", 1.0)
