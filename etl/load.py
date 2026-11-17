import logging
import pandas as pd
from google.cloud import bigquery

logger = logging.getLogger(__name__)


def load_to_bigquery(df: pd.DataFrame, project_id: str, dataset_id: str, table_name: str):
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=False,
    )

    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    logger.info(f"Cargados {len(df)} registros en {table_ref}")
