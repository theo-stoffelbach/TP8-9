#!/bin/bash
# Script d'injection des seeds SQL du prof dans les bases du projet
# À exécuter depuis la racine du projet

set -e

echo "=========================================="
echo " Injection des seeds - Mini Zalando"
echo "=========================================="

# --- 1. Vider les anciennes données ---
echo "[1/2] Vidage des tables existantes..."

# Catalog DB
docker exec catalog_db psql -U catalog_user -d catalog_db -c "
TRUNCATE TABLE catalog_category, catalog_product CASCADE;
"

# Customers DB
docker exec customers_db psql -U customer_user -d customer_db -c "
TRUNCATE TABLE catalog_customer, catalog_address CASCADE;
"

# Orders DB
docker exec orders_db psql -U order_user -d order_db -c "
TRUNCATE TABLE orders_order, orders_orderline CASCADE;
"

echo "[1/2] Tables videes."

# --- 2. Inserer les nouvelles seeds ---
echo "[2/2] Injection des seeds..."

# Copier les fichiers dans les conteneurs puis executer
docker cp zalendo_seed_sql/adapted/01_catalog_category.sql catalog_db:/tmp/01_catalog_category.sql
docker cp zalendo_seed_sql/adapted/02_catalog_product.sql catalog_db:/tmp/02_catalog_product.sql
docker cp zalendo_seed_sql/adapted/03_catalog_customer.sql customers_db:/tmp/03_catalog_customer.sql
docker cp zalendo_seed_sql/adapted/04_catalog_address.sql customers_db:/tmp/04_catalog_address.sql
docker cp zalendo_seed_sql/adapted/05_orders_order.sql orders_db:/tmp/05_orders_order.sql
docker cp zalendo_seed_sql/adapted/06_orders_orderline.sql orders_db:/tmp/06_orders_orderline.sql

# Executer dans l'ordre
docker exec catalog_db psql -U catalog_user -d catalog_db -f /tmp/01_catalog_category.sql
docker exec catalog_db psql -U catalog_user -d catalog_db -f /tmp/02_catalog_product.sql
docker exec customers_db psql -U customer_user -d customer_db -f /tmp/03_catalog_customer.sql
docker exec customers_db psql -U customer_user -d customer_db -f /tmp/04_catalog_address.sql
docker exec orders_db psql -U order_user -d order_db -f /tmp/05_orders_order.sql
docker exec orders_db psql -U order_user -d order_db -f /tmp/06_orders_orderline.sql

echo "=========================================="
echo " Seeds injectees avec succes !"
echo "=========================================="
echo ""
echo "Prochaine etape : relancer l'ETL"
echo "  cd etl && python etl_sales.py"
