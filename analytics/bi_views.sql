-- ============================================================
-- Vues analytiques pour Superset
-- À exécuter une fois dans la base BI (bi_db)
-- ============================================================

-- Vue complète : fact_order_lines + toutes les dimensions
-- Utilisation dans Superset : créer un Dataset sur la table "vw_fact_order_lines_complete"
CREATE OR REPLACE VIEW vw_fact_order_lines_complete AS
SELECT
    fol.order_line_id,
    fol.order_id,
    fol.quantity,
    fol.unit_price,
    fol.line_total,
    fol.order_status,
    fol.country,

    -- Dimension Date
    dd.date_id,
    dd.full_date,
    dd.year,
    dd.quarter,
    dd.month,
    dd.month_name,
    dd.day,
    dd.day_name,

    -- Dimension Client
    dc.customer_id,
    dc.first_name,
    dc.last_name,
    dc.email,
    dc.phone,
    dc.is_active,
    dc.country AS customer_country,
    dc.city,

    -- Dimension Produit
    dp.product_id,
    dp.product_name,
    dp.slug,
    dp.category_id,
    dp.category_name,
    dp.is_active AS product_is_active,

    -- Dimension Catégorie
    dcat.category_name AS category_name_alt

FROM fact_order_lines fol
LEFT JOIN dim_date dd ON fol.date_id = dd.date_id
LEFT JOIN dim_customer dc ON fol.customer_id = dc.customer_id
LEFT JOIN dim_product dp ON fol.product_id = dp.product_id
LEFT JOIN dim_category dcat ON fol.category_id = dcat.category_id;


-- Vue agrégée par pays (prête à l'emploi pour un dashboard géographique)
CREATE OR REPLACE VIEW vw_sales_by_country AS
SELECT
    fol.country,
    COUNT(DISTINCT fol.order_id) AS nb_orders,
    SUM(fol.line_total) AS total_sales,
    AVG(fol.line_total) AS avg_line_value,
    SUM(fol.quantity) AS total_items_sold
FROM fact_order_lines fol
GROUP BY fol.country;


-- Vue agrégée par mois (prête à l'emploi pour un line chart)
CREATE OR REPLACE VIEW vw_sales_by_month AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    COUNT(DISTINCT fol.order_id) AS nb_orders,
    SUM(fol.line_total) AS total_sales,
    SUM(fol.quantity) AS total_quantity
FROM fact_order_lines fol
LEFT JOIN dim_date dd ON fol.date_id = dd.date_id
GROUP BY dd.year, dd.month, dd.month_name
ORDER BY dd.year, dd.month;


-- Vue agrégée par catégorie (prête à l'emploi pour un pie chart)
CREATE OR REPLACE VIEW vw_sales_by_category AS
SELECT
    dp.category_name,
    COUNT(DISTINCT fol.order_id) AS nb_orders,
    SUM(fol.line_total) AS total_sales,
    SUM(fol.quantity) AS total_quantity
FROM fact_order_lines fol
LEFT JOIN dim_product dp ON fol.product_id = dp.product_id
GROUP BY dp.category_name;


-- Vue agrégée par client (prête à l'emploi pour l'analyse clients)
CREATE OR REPLACE VIEW vw_sales_by_customer AS
SELECT
    dc.customer_id,
    dc.first_name,
    dc.last_name,
    dc.email,
    dc.country,
    COUNT(DISTINCT fol.order_id) AS nb_orders,
    SUM(fol.line_total) AS total_sales,
    AVG(fol.line_total) AS avg_line_value
FROM fact_order_lines fol
LEFT JOIN dim_customer dc ON fol.customer_id = dc.customer_id
GROUP BY dc.customer_id, dc.first_name, dc.last_name, dc.email, dc.country;


-- Vue top produits (prête à l'emploi pour l'analyse produits)
CREATE OR REPLACE VIEW vw_top_products AS
SELECT
    dp.product_id,
    dp.product_name,
    dp.category_name,
    COUNT(DISTINCT fol.order_id) AS nb_orders,
    SUM(fol.quantity) AS total_quantity,
    SUM(fol.line_total) AS total_sales
FROM fact_order_lines fol
LEFT JOIN dim_product dp ON fol.product_id = dp.product_id
GROUP BY dp.product_id, dp.product_name, dp.category_name;
