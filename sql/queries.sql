-- 1. ¿Hay algún vendedor con múltiples publicaciones? ¿Con cuántas?
SELECT
    seller_id,
    COUNT(*) AS cantidad_publicaciones
FROM `meli_samsung.items`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.items`)
GROUP BY seller_id
HAVING COUNT(*) > 1
ORDER BY cantidad_publicaciones DESC;


-- 2. ¿Promedio de ventas por seller?
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


-- 3. ¿Cuál es el precio promedio en dólares?
SELECT
    ROUND(AVG(price_usd), 2) AS precio_promedio_usd,
    ROUND(MIN(price_usd), 2) AS precio_minimo_usd,
    ROUND(MAX(price_usd), 2) AS precio_maximo_usd
FROM `meli_samsung.items`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.items`)
  AND price_usd IS NOT NULL;


-- 4. ¿Porcentaje de artículos con garantía?
SELECT
    COUNTIF(has_warranty = TRUE)                                        AS con_garantia,
    COUNTIF(has_warranty = FALSE)                                       AS sin_garantia,
    COUNT(*)                                                            AS total,
    ROUND(COUNTIF(has_warranty = TRUE) * 100.0 / COUNT(*), 2)          AS porcentaje_con_garantia
FROM `meli_samsung.items`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.items`);


-- 5. ¿Métodos de shipping que ofrecen?
SELECT
    shipping_mode,
    logistic_type,
    COUNT(*)                                            AS cantidad,
    COUNTIF(free_shipping = TRUE)                       AS con_envio_gratis,
    ROUND(COUNTIF(free_shipping = TRUE) * 100.0 / COUNT(*), 2) AS pct_envio_gratis
FROM `meli_samsung.shipping`
WHERE job_run = (SELECT MAX(job_run) FROM `meli_samsung.shipping`)
GROUP BY shipping_mode, logistic_type
ORDER BY cantidad DESC;
