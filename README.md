# ETL Samsung Galaxy - Mercado Libre

ETL en Python que extrae publicaciones de Samsung Galaxy S24 de la API pública de Mercado Libre Argentina, transforma los datos y los carga en BigQuery para su análisis.

## Arquitectura

```
API Mercado Libre
      │
      ▼
  extract.py       ← paginado de 50 registros, auth OAuth, bulk items/sellers
      │
      ▼
  transform.py     ← modela 3 tablas: items, sellers, shipping
      │
      ▼
  load.py          ← carga a BigQuery (WRITE_APPEND)
      │
      ▼
  BigQuery
  meli_samsung
  ├── items
  ├── sellers
  └── shipping
```

## Modelo de Datos

### `items`
| Campo | Tipo | Descripción |
|---|---|---|
| item_id | STRING | ID único de la publicación |
| title | STRING | Título de la publicación |
| price_ars | FLOAT64 | Precio en pesos argentinos |
| price_usd | FLOAT64 | Precio convertido a dólares |
| currency_id | STRING | Moneda original |
| condition | STRING | Condición del producto (new) |
| seller_id | STRING | ID del vendedor |
| has_warranty | BOOL | Si tiene garantía |
| warranty_description | STRING | Descripción de la garantía |
| sold_quantity | INT64 | Cantidad vendida |
| job_run | TIMESTAMP | Fecha y hora de ejecución del ETL |

### `sellers`
| Campo | Tipo | Descripción |
|---|---|---|
| seller_id | STRING | ID único del vendedor |
| nickname | STRING | Nombre del vendedor |
| total_sales | INT64 | Total de ventas históricas |
| level_id | STRING | Nivel de reputación |
| power_seller_status | STRING | Estado MercadoLíder |
| job_run | TIMESTAMP | Fecha y hora de ejecución del ETL |

### `shipping`
| Campo | Tipo | Descripción |
|---|---|---|
| item_id | STRING | ID de la publicación |
| seller_id | STRING | ID del vendedor |
| shipping_mode | STRING | Modo de envío |
| free_shipping | BOOL | Si tiene envío gratis |
| logistic_type | STRING | Tipo de logística |
| job_run | TIMESTAMP | Fecha y hora de ejecución del ETL |

## Requisitos

- Python 3.10+
- Cuenta en Mercado Libre con app creada en el DevCenter
- Proyecto en Google Cloud con BigQuery habilitado
- Service Account con rol `BigQuery Admin`

## Instalación

```bash
git clone https://github.com/tu-usuario/etl-meli-samsung.git
cd etl-meli-samsung
pip install -r requirements.txt
```

## Configuración

### 1. Variables de entorno

Copiá el archivo de ejemplo y completá con tus credenciales:

```bash
cp .env.example .env
```

Editá `.env`:

```env
MELI_APP_ID=tu_app_id
MELI_SECRET_KEY=tu_secret_key
MELI_REFRESH_TOKEN=tu_refresh_token

GOOGLE_APPLICATION_CREDENTIALS=Doc/meli-514816-16a92379b1d3.json
BIGQUERY_PROJECT_ID=meli-514816
```

### 2. Obtener el primer refresh_token de Mercado Libre

**Paso 1** — Autorizá la app en el navegador (reemplazá `APP_ID` y `REDIRECT_URI`):

```
https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id=APP_ID&redirect_uri=REDIRECT_URI
```

**Paso 2** — Copiá el `code` de la URL de redirección (`?code=TG-XXXXXXXX`) y hacé el POST:

```bash
curl -X POST https://api.mercadolibre.com/oauth/token \
  -d "grant_type=authorization_code" \
  -d "client_id=APP_ID" \
  -d "client_secret=SECRET_KEY" \
  -d "code=TG-XXXXXXXX" \
  -d "redirect_uri=REDIRECT_URI"
```

**Paso 3** — Guardá el `refresh_token` de la respuesta en el `.env`.

### 3. Crear tablas en BigQuery

```bash
python setup_bigquery.py
```

## Ejecución

```bash
python main.py
```

El ETL extrae hasta 500 publicaciones nuevas de Samsung Galaxy S24, las transforma y las carga en BigQuery. Cada ejecución agrega registros con un nuevo `JOB_RUN`.

## Configuración del ETL

Editá `config/config.yaml` para ajustar parámetros:

```yaml
search:
  query: "Samsung Galaxy S24"
  condition: "new"
  page_size: 50       # registros por página (máx 50)
  max_records: 500    # límite total de registros
```

## Queries analíticas

### 1. ¿Hay algún vendedor con múltiples publicaciones?

```sql
SELECT
    seller_id,
    COUNT(*) AS cantidad_publicaciones
FROM `meli_samsung.items`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.items`)
GROUP BY seller_id
HAVING COUNT(*) > 1
ORDER BY cantidad_publicaciones DESC;
```

### 2. ¿Promedio de ventas por seller?

```sql
SELECT
    s.seller_id,
    s.nickname,
    s.total_sales,
    COUNT(i.item_id) AS publicaciones,
    ROUND(s.total_sales / NULLIF(COUNT(i.item_id), 0), 2) AS ventas_promedio_por_publicacion
FROM `meli_samsung.sellers` s
JOIN `meli_samsung.items` i ON s.seller_id = i.seller_id
WHERE s.job_run = (SELECT MAX(job_run) FROM `meli_samsung.sellers`)
  AND i.job_run = (SELECT MAX(job_run) FROM `meli_samsung.items`)
GROUP BY s.seller_id, s.nickname, s.total_sales
ORDER BY ventas_promedio_por_publicacion DESC;
```

### 3. ¿Cuál es el precio promedio en dólares?

```sql
SELECT
    ROUND(AVG(price_usd), 2) AS precio_promedio_usd,
    ROUND(MIN(price_usd), 2) AS precio_minimo_usd,
    ROUND(MAX(price_usd), 2) AS precio_maximo_usd
FROM `meli_samsung.items`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.items`)
  AND price_usd IS NOT NULL;
```

### 4. ¿Porcentaje de artículos con garantía?

```sql
SELECT
    COUNTIF(has_warranty = TRUE)                                AS con_garantia,
    COUNTIF(has_warranty = FALSE)                               AS sin_garantia,
    COUNT(*)                                                    AS total,
    ROUND(COUNTIF(has_warranty = TRUE) * 100.0 / COUNT(*), 2)  AS porcentaje_con_garantia
FROM `meli_samsung.items`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.items`);
```

### 5. ¿Métodos de shipping que ofrecen?

```sql
SELECT
    shipping_mode,
    logistic_type,
    COUNT(*)                                                    AS cantidad,
    COUNTIF(free_shipping = TRUE)                               AS con_envio_gratis,
    ROUND(COUNTIF(free_shipping = TRUE) * 100.0 / COUNT(*), 2) AS pct_envio_gratis
FROM `meli_samsung.shipping`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.shipping`)
GROUP BY shipping_mode, logistic_type
ORDER BY cantidad DESC;
```

## Decisiones técnicas

- **BigQuery** como destino por integración nativa con Looker Studio
- **WRITE_APPEND** en cada carga para mantener historial de ejecuciones
- **Bulk endpoints** (`/items/bulk`, `/users/bulk`) para minimizar llamadas a la API
- **refresh_token** para renovar el access_token automáticamente en cada ejecución
- **config.yaml** para centralizar parámetros sin tocar el código
- **Variables de entorno** para todas las credenciales, nunca hardcodeadas

## Oportunidades de mejora

- Orquestar con Apache Airflow o Cloud Scheduler para ejecución periódica
- Agregar reintentos con backoff exponencial en las llamadas a la API
- Particionar las tablas de BigQuery por `job_run` para optimizar queries
- Extender a otros modelos de Samsung Galaxy (S23, S22, A54, etc.)

## Estructura del proyecto

```
├── config/
│   └── config.yaml
├── etl/
│   ├── extract.py
│   ├── transform.py
│   └── load.py
├── sql/
│   ├── ddl.sql
│   └── queries.sql
├── Doc/
│   └── meli-514816-16a92379b1d3.json  ← NO subir a GitHub
├── .env                                ← NO subir a GitHub
├── .env.example
├── .gitignore
├── main.py
├── setup_bigquery.py
└── requirements.txt
```
