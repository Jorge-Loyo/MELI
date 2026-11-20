# ETL Samsung Galaxy - Mercado Libre

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![BigQuery](https://img.shields.io/badge/BigQuery-Google%20Cloud-orange)
![Status](https://img.shields.io/badge/Status-En%20desarrollo-yellow)

ETL en Python que extrae publicaciones de Samsung Galaxy S24 de la API pública de Mercado Libre Argentina, transforma los datos y los carga en BigQuery para su análisis y visualización en Looker Studio.

## Contexto del Desafío

El desafío consiste en desarrollar una automatización del tipo ETL que acceda a las APIs públicas de Mercado Libre para responder preguntas de negocio sobre publicaciones de Samsung Galaxy en Argentina:

1. ¿Hay algún vendedor con múltiples publicaciones?
2. ¿Cuál es el promedio de ventas por seller?
3. ¿Cuál es el precio promedio en dólares?
4. ¿Qué porcentaje de artículos tiene garantía?
5. ¿Qué métodos de shipping ofrecen?

## Arquitectura

```
API Mercado Libre
      │
      ├── /sites/MLA/search     ← búsqueda paginada de 50 registros
      ├── /items/bulk            ← detalle de items (hasta 20 por llamada)
      ├── /users/bulk            ← detalle de vendedores (hasta 20 por llamada)
      └── /currency_conversions  ← tipo de cambio ARS → USD
      │
      ▼
  extract.py       ← auth OAuth con refresh_token automático
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
      │
      ▼
  Looker Studio    ← dashboard de visualización
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
git clone https://github.com/Jorge-Loyo/MELI.git
cd MELI
pip install -r requirements.txt
```

## Configuración

### 1. Variables de entorno

```bash
cp .env.example .env
```

Completá `.env` con tus credenciales:

```env
MELI_APP_ID=tu_app_id
MELI_SECRET_KEY=tu_secret_key
MELI_REFRESH_TOKEN=tu_refresh_token

GOOGLE_APPLICATION_CREDENTIALS=Doc/service_account.json
BIGQUERY_PROJECT_ID=tu-proyecto-bigquery
```

### 2. Obtener el primer refresh_token de Mercado Libre

**Paso 1** — Autorizá la app en el navegador:

```
https://auth.mercadolibre.com.ar/authorization?response_type=code&client_id=APP_ID&redirect_uri=REDIRECT_URI
```

**Paso 2** — Con el `code` de la URL de redirección (`?code=TG-XXXXXXXX`):

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

El ETL extrae hasta 500 publicaciones nuevas de Samsung Galaxy S24, las transforma y las carga en BigQuery. Cada ejecución agrega registros con un nuevo `JOB_RUN`, manteniendo el historial completo.

## Configuración del ETL

Editá `config/config.yaml` para ajustar parámetros sin tocar el código:

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

- **BigQuery** como destino por integración nativa con Looker Studio y escalabilidad
- **WRITE_APPEND** en cada carga para mantener historial de ejecuciones y poder comparar entre corridas
- **Bulk endpoints** (`/items/bulk`, `/users/bulk`) para minimizar llamadas a la API y evitar rate limiting
- **refresh_token** para renovar el access_token automáticamente en cada ejecución sin intervención manual
- **config.yaml** para centralizar parámetros sin tocar el código fuente
- **Variables de entorno** para todas las credenciales, nunca hardcodeadas en el código
- **JOB_RUN** como campo de auditoría en todas las tablas para identificar cada ejecución del ETL

## Oportunidades de mejora

- Orquestar con **Cloud Scheduler** o **Apache Airflow** para ejecución periódica automática
- Agregar reintentos con **backoff exponencial** en las llamadas a la API
- **Particionar** las tablas de BigQuery por `job_run` para optimizar el costo de queries
- Extender a otros modelos de Samsung Galaxy (S23, S22, A54, etc.) via `config.yaml`
- Agregar **tests unitarios** para las funciones de transformación
- Implementar **alertas** cuando el ETL falla via Cloud Monitoring

## Estructura del proyecto

```
├── config/
│   └── config.yaml          ← parámetros del ETL
├── etl/
│   ├── extract.py           ← extracción con auth OAuth y paginado
│   ├── transform.py         ← transformación y modelado de datos
│   └── load.py              ← carga a BigQuery
├── sql/
│   ├── ddl.sql              ← CREATE TABLE statements
│   └── queries.sql          ← queries analíticas del desafío
├── Doc/
│   └── service_account.json ← NO subir a GitHub
├── .env                     ← NO subir a GitHub
├── .env.example             ← template de variables de entorno
├── .gitignore
├── main.py                  ← entry point del ETL
├── setup_bigquery.py        ← crea dataset y tablas en BigQuery
└── requirements.txt
```
