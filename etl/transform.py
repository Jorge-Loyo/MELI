from datetime import datetime
import pandas as pd


def transform(search_results: list, items_detail: list, sellers_detail: list, usd_rate: float, job_run: datetime):
    items_map = {item["id"]: item for item in items_detail}
    sellers_map = {str(s["id"]): s for s in sellers_detail}

    items_rows = []
    shipping_rows = []

    for result in search_results:
        item_id = result["id"]
        detail = items_map.get(item_id, {})
        seller_id = str(result.get("seller", {}).get("id", ""))

        price_ars = result.get("price") or 0
        price_usd = round(price_ars * usd_rate, 2) if usd_rate else None

        # Garantía: buscar en sale_terms
        sale_terms = detail.get("sale_terms", [])
        warranty = next((t.get("value_name") for t in sale_terms if t.get("id") == "WARRANTY_TYPE"), None)
        has_warranty = warranty is not None and warranty.lower() not in ("sin garantía", "no", "none", "")

        items_rows.append({
            "item_id": item_id,
            "title": result.get("title"),
            "price_ars": price_ars,
            "price_usd": price_usd,
            "currency_id": result.get("currency_id"),
            "condition": result.get("condition"),
            "seller_id": seller_id,
            "has_warranty": has_warranty,
            "warranty_description": warranty,
            "sold_quantity": detail.get("sold_quantity", 0),
            "job_run": job_run,
        })

        shipping = result.get("shipping", {})
        shipping_rows.append({
            "item_id": item_id,
            "seller_id": seller_id,
            "shipping_mode": shipping.get("mode"),
            "free_shipping": shipping.get("free_shipping", False),
            "logistic_type": shipping.get("logistic_type"),
            "job_run": job_run,
        })

    sellers_rows = []
    for s in sellers_detail:
        transactions = s.get("seller_reputation", {}).get("transactions", {})
        sellers_rows.append({
            "seller_id": str(s["id"]),
            "nickname": s.get("nickname"),
            "total_sales": transactions.get("total", 0),
            "level_id": s.get("seller_reputation", {}).get("level_id"),
            "power_seller_status": s.get("seller_reputation", {}).get("power_seller_status"),
            "job_run": job_run,
        })

    return (
        pd.DataFrame(items_rows),
        pd.DataFrame(sellers_rows),
        pd.DataFrame(shipping_rows),
    )
