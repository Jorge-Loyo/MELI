from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'Doc/meli-514816-16a92379b1d3.json'
client = bigquery.Client(project='meli-514816')
dataset = 'meli-514816.meli_samsung'

tables = {
    "items": [
        bigquery.SchemaField("item_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING"),
        bigquery.SchemaField("price_ars", "FLOAT64"),
        bigquery.SchemaField("price_usd", "FLOAT64"),
        bigquery.SchemaField("currency_id", "STRING"),
        bigquery.SchemaField("condition", "STRING"),
        bigquery.SchemaField("seller_id", "STRING"),
        bigquery.SchemaField("has_warranty", "BOOL"),
        bigquery.SchemaField("warranty_description", "STRING"),
        bigquery.SchemaField("sold_quantity", "INT64"),
        bigquery.SchemaField("job_run", "TIMESTAMP", mode="REQUIRED"),
    ],
    "sellers": [
        bigquery.SchemaField("seller_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("nickname", "STRING"),
        bigquery.SchemaField("total_sales", "INT64"),
        bigquery.SchemaField("level_id", "STRING"),
        bigquery.SchemaField("power_seller_status", "STRING"),
        bigquery.SchemaField("job_run", "TIMESTAMP", mode="REQUIRED"),
    ],
    "shipping": [
        bigquery.SchemaField("item_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("seller_id", "STRING"),
        bigquery.SchemaField("shipping_mode", "STRING"),
        bigquery.SchemaField("free_shipping", "BOOL"),
        bigquery.SchemaField("logistic_type", "STRING"),
        bigquery.SchemaField("job_run", "TIMESTAMP", mode="REQUIRED"),
    ],
}

for table_name, schema in tables.items():
    table_ref = f"{dataset}.{table_name}"
    table = bigquery.Table(table_ref, schema=schema)
    client.create_table(table, exists_ok=True)
    print(f"Tabla creada: {table_name}")

print("Listo!")
