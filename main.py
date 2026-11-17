import os
import logging
import yaml
from datetime import datetime, timezone
from dotenv import load_dotenv

from etl.extract import get_access_token, search_items, get_items_detail, get_sellers_detail, get_usd_rate
from etl.transform import transform
from etl.load import load_to_bigquery

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_config():
    with open("config/config.yaml") as f:
        return yaml.safe_load(f)


def main():
    load_dotenv()
    config = load_config()

    job_run = datetime.now(timezone.utc)
    logger.info(f"ETL iniciado - JOB_RUN: {job_run}")

    # Auth
    token = get_access_token(
        app_id=os.environ["MELI_APP_ID"],
        secret_key=os.environ["MELI_SECRET_KEY"],
        refresh_token=os.environ["MELI_REFRESH_TOKEN"],
    )

    # Extract
    search_cfg = config["search"]
    results = search_items(
        token=token,
        query=search_cfg["query"],
        condition=search_cfg["condition"],
        page_size=search_cfg["page_size"],
        max_records=search_cfg["max_records"],
    )
    logger.info(f"Total items extraídos del search: {len(results)}")

    item_ids = [r["id"] for r in results]
    seller_ids = list({str(r["seller"]["id"]) for r in results if r.get("seller")})

    items_detail = get_items_detail(token, item_ids)
    sellers_detail = get_sellers_detail(token, seller_ids)
    usd_rate = get_usd_rate(token)
    logger.info(f"Tasa USD: {usd_rate}")

    # Transform
    df_items, df_sellers, df_shipping = transform(results, items_detail, sellers_detail, usd_rate, job_run)
    logger.info(f"Items: {len(df_items)} | Sellers: {len(df_sellers)} | Shipping: {len(df_shipping)}")

    # Load
    bq_cfg = config["bigquery"]
    project_id = os.environ["BIGQUERY_PROJECT_ID"]
    dataset_id = bq_cfg["dataset_id"]

    load_to_bigquery(df_items, project_id, dataset_id, bq_cfg["tables"]["items"])
    load_to_bigquery(df_sellers, project_id, dataset_id, bq_cfg["tables"]["sellers"])
    load_to_bigquery(df_shipping, project_id, dataset_id, bq_cfg["tables"]["shipping"])

    logger.info("ETL finalizado exitosamente")


if __name__ == "__main__":
    main()
