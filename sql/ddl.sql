-- DDL para BigQuery
-- Dataset: meli_samsung

CREATE TABLE IF NOT EXISTS `meli_samsung.items` (
    item_id             STRING      NOT NULL,
    title               STRING,
    price_ars           FLOAT64,
    price_usd           FLOAT64,
    currency_id         STRING,
    condition           STRING,
    seller_id           STRING,
    has_warranty        BOOL,
    warranty_description STRING,
    sold_quantity       INT64,
    job_run             TIMESTAMP   NOT NULL
);

CREATE TABLE IF NOT EXISTS `meli_samsung.sellers` (
    seller_id           STRING      NOT NULL,
    nickname            STRING,
    total_sales         INT64,
    level_id            STRING,
    power_seller_status STRING,
    job_run             TIMESTAMP   NOT NULL
);

CREATE TABLE IF NOT EXISTS `meli_samsung.shipping` (
    item_id             STRING      NOT NULL,
    seller_id           STRING,
    shipping_mode       STRING,
    free_shipping       BOOL,
    logistic_type       STRING,
    job_run             TIMESTAMP   NOT NULL
);
