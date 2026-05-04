-- ============================================================
-- Vues analytiques pour Superset
-- À exécuter une fois dans la base BI (bi_db)
-- ============================================================

-- Vue complète : fact_sales + toutes les dimensions
-- Utilisation dans Superset : créer un Dataset sur la table "vw_fact_sales_complete"
CREATE OR REPLACE VIEW vw_fact_sales_complete AS
SELECT
    fs.order_id,
    fs.order_status,
    fs.order_total,
    fs.nb_order_lines,
    fs.customer_id,

    -- Dimension Date
    dd.date_id,
    dd.full_date,
    dd.year,
    dd.quarter,
    dd.month,
    dd.month_name,
    dd.week,
    dd.day_of_month,
    dd.day_of_week,
    dd.day_name,
    dd.is_weekend,

    -- Dimension Pays
    dp.pays_id,
    dp.city,
    dp.country,

    -- Dimension Catégorie
    dc.categorie_id,
    dc.name AS category_name,
    dc.slug AS category_slug,

    -- Dimension Produit
    dpr.produit_id,
    dpr.name AS product_name,
    dpr.price AS product_price

FROM fact_sales fs
LEFT JOIN dim_date dd ON fs.date_id = dd.date_id
LEFT JOIN dim_pays dp ON fs.pays_id = dp.pays_id
LEFT JOIN dim_categorie dc ON fs.categorie_id = dc.categorie_id
LEFT JOIN dim_produit dpr ON fs.produit_id = dpr.produit_id;


-- Vue agrégée par pays (prête à l'emploi pour un dashboard)
CREATE OR REPLACE VIEW vw_sales_by_country AS
SELECT
    dp.country,
    COUNT(DISTINCT fs.order_id) AS nb_orders,
    SUM(fs.order_total) AS total_sales,
    AVG(fs.order_total) AS avg_order_value,
    SUM(fs.nb_order_lines) AS total_items_sold
FROM fact_sales fs
LEFT JOIN dim_pays dp ON fs.pays_id = dp.pays_id
GROUP BY dp.country;


-- Vue agrégée par mois (prête à l'emploi pour un line chart)
CREATE OR REPLACE VIEW vw_sales_by_month AS
SELECT
    dd.year,
    dd.month,
    dd.month_name,
    COUNT(DISTINCT fs.order_id) AS nb_orders,
    SUM(fs.order_total) AS total_sales
FROM fact_sales fs
LEFT JOIN dim_date dd ON fs.date_id = dd.date_id
GROUP BY dd.year, dd.month, dd.month_name
ORDER BY dd.year, dd.month;


-- Vue agrégée par catégorie (prête à l'emploi pour un pie chart)
CREATE OR REPLACE VIEW vw_sales_by_category AS
SELECT
    dc.name AS category_name,
    COUNT(DISTINCT fs.order_id) AS nb_orders,
    SUM(fs.order_total) AS total_sales
FROM fact_sales fs
LEFT JOIN dim_categorie dc ON fs.categorie_id = dc.categorie_id
GROUP BY dc.name;
