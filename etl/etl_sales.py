"""
ETL - Schéma en étoile BI (Mini Zalando)
=========================================
Dimensions : dim_date, dim_customer, dim_product, dim_category
Fait       : fact_order_lines

Grain de fact_order_lines : 1 ligne = 1 ligne de commande
"""

import calendar
import os
import psycopg2
import psycopg2.extras
from datetime import datetime, date, timedelta
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Connexions sources
# ═══════════════════════════════════════════════════════════════════════════════

CATALOG_DB = {
    "host": os.getenv("CATALOG_DB_HOST", "localhost"),
    "port": int(os.getenv("CATALOG_DB_PORT", 5431)),
    "dbname": os.getenv("CATALOG_DB_NAME", "catalog_db"),
    "user": os.getenv("CATALOG_DB_USER", "catalog_user"),
    "password": os.getenv("CATALOG_DB_PASSWORD", "catalog_pass"),
}
CUSTOMERS_DB = {
    "host": os.getenv("CUSTOMERS_DB_HOST", "localhost"),
    "port": int(os.getenv("CUSTOMERS_DB_PORT", 5435)),
    "dbname": os.getenv("CUSTOMERS_DB_NAME", "customer_db"),
    "user": os.getenv("CUSTOMERS_DB_USER", "customer_user"),
    "password": os.getenv("CUSTOMERS_DB_PASSWORD", "customer_password"),
}
ORDERS_DB = {
    "host": os.getenv("ORDERS_DB_HOST", "localhost"),
    "port": int(os.getenv("ORDERS_DB_PORT", 5433)),
    "dbname": os.getenv("ORDERS_DB_NAME", "order_db"),
    "user": os.getenv("ORDERS_DB_USER", "order_user"),
    "password": os.getenv("ORDERS_DB_PASSWORD", "order_pass"),
}

# ═══════════════════════════════════════════════════════════════════════════════
# Connexion destination BI
# ═══════════════════════════════════════════════════════════════════════════════

BI_DB = {
    "host": os.getenv("BI_DB_HOST", "localhost"),
    "port": int(os.getenv("BI_DB_PORT", 5434)),
    "dbname": os.getenv("BI_DB_NAME", "bi_db"),
    "user": os.getenv("BI_DB_USER", "bi_user"),
    "password": os.getenv("BI_DB_PASSWORD", "bi_pass"),
}

# ═══════════════════════════════════════════════════════════════════════════════
# DDL
# ═══════════════════════════════════════════════════════════════════════════════

DDL = """
-- 1. Dimension Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER     PRIMARY KEY,        -- clé YYYYMMDD
    full_date       DATE        NOT NULL UNIQUE,
    year            SMALLINT    NOT NULL,
    quarter         SMALLINT    NOT NULL,
    month           SMALLINT    NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    day             SMALLINT    NOT NULL,
    day_name        VARCHAR(20) NOT NULL
);

-- 2. Dimension Client
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id     INTEGER     PRIMARY KEY,
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    email           VARCHAR(255),
    phone           VARCHAR(20),
    is_active       BOOLEAN     DEFAULT TRUE,
    country         VARCHAR(100),
    city            VARCHAR(100)
);

-- 3. Dimension Catégorie
CREATE TABLE IF NOT EXISTS dim_category (
    category_id     INTEGER     PRIMARY KEY,
    category_name   VARCHAR(100) NOT NULL,
    category_slug   VARCHAR(100) NOT NULL
);

-- 4. Dimension Produit (dénormalisée avec category_name)
CREATE TABLE IF NOT EXISTS dim_product (
    product_id      INTEGER     PRIMARY KEY,
    product_name    VARCHAR(200) NOT NULL,
    slug            VARCHAR(100),
    category_id     INTEGER     REFERENCES dim_category(category_id),
    category_name   VARCHAR(100),
    is_active       BOOLEAN     DEFAULT TRUE
);

-- 5. Table de faits (1 ligne = 1 ligne de commande)
CREATE TABLE IF NOT EXISTS fact_order_lines (
    order_line_id   INTEGER     PRIMARY KEY,
    order_id        INTEGER     NOT NULL,
    customer_id     INTEGER     NOT NULL,
    product_id      INTEGER     REFERENCES dim_product(product_id),
    category_id     INTEGER     REFERENCES dim_category(category_id),
    date_id         INTEGER     REFERENCES dim_date(date_id),
    country         VARCHAR(100),
    quantity        INTEGER     NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    line_total      DECIMAL(10,2) NOT NULL,
    order_status    VARCHAR(20)
);
"""

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

MONTH_NAMES = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]
DAY_NAMES = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DIMENSIONS
# ═══════════════════════════════════════════════════════════════════════════════


def load_dim_date(conn, start: date, end: date) -> None:
    """Génère une ligne par jour entre start et end."""
    rows = []
    current = start
    while current <= end:
        rows.append(
            (
                int(current.strftime("%Y%m%d")),
                current,
                current.year,
                (current.month - 1) // 3 + 1,
                current.month,
                MONTH_NAMES[current.month],
                current.day,
                DAY_NAMES[current.weekday()],
            )
        )
        current += timedelta(days=1)

    sql = """
        INSERT INTO dim_date (
            date_id, full_date, year, quarter, month, month_name,
            day, day_name
        ) VALUES %s
        ON CONFLICT (date_id) DO NOTHING
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
    conn.commit()
    log.info(f"  [dim_date] {len(rows)} jours chargés ({start} -> {end})")


def load_dim_customer(conn, customers_conn) -> None:
    """Synchronise dim_customer depuis customers_db."""
    with customers_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                c.id,
                c.first_name,
                c.last_name,
                c.email,
                c.phone,
                c.is_active,
                COALESCE(
                    (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                    (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1),
                    'Inconnu'
                ) AS country,
                COALESCE(
                    (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                    (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1),
                    'Inconnu'
                ) AS city
            FROM catalog_customer c
        """)
        rows = cur.fetchall()

    sql = """
        INSERT INTO dim_customer (
            customer_id, first_name, last_name, email, phone,
            is_active, country, city
        ) VALUES %s
        ON CONFLICT (customer_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name  = EXCLUDED.last_name,
            email      = EXCLUDED.email,
            phone      = EXCLUDED.phone,
            is_active  = EXCLUDED.is_active,
            country    = EXCLUDED.country,
            city       = EXCLUDED.city
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            sql,
            [
                (
                    r["id"],
                    r["first_name"],
                    r["last_name"],
                    r["email"],
                    r["phone"],
                    r["is_active"],
                    r["country"],
                    r["city"],
                )
                for r in rows
            ],
        )
    conn.commit()
    log.info(f"  [dim_customer] {len(rows)} clients chargés")


def load_dim_category(conn, catalog_conn) -> None:
    """Synchronise dim_category depuis catalog_db."""
    with catalog_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT id, name, slug FROM catalog_category")
        rows = cur.fetchall()

    sql = """
        INSERT INTO dim_category (category_id, category_name, category_slug)
        VALUES %s
        ON CONFLICT (category_id) DO UPDATE SET
            category_name = EXCLUDED.category_name,
            category_slug = EXCLUDED.category_slug
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur, sql, [(r["id"], r["name"], r["slug"]) for r in rows]
        )
    conn.commit()
    log.info(f"  [dim_category] {len(rows)} catégories chargées")


def load_dim_product(conn, catalog_conn) -> None:
    """Synchronise dim_product depuis catalog_db (avec category_name dénormalisé)."""
    with catalog_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                p.id,
                p.name,
                p.slug,
                p.category_id,
                c.name AS category_name,
                p.is_active
            FROM catalog_product p
            LEFT JOIN catalog_category c ON p.category_id = c.id
            WHERE p.is_active = TRUE
        """)
        rows = cur.fetchall()

    sql = """
        INSERT INTO dim_product (
            product_id, product_name, slug, category_id, category_name, is_active
        ) VALUES %s
        ON CONFLICT (product_id) DO UPDATE SET
            product_name = EXCLUDED.product_name,
            slug         = EXCLUDED.slug,
            category_id  = EXCLUDED.category_id,
            category_name= EXCLUDED.category_name,
            is_active    = EXCLUDED.is_active
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            sql,
            [
                (
                    r["id"],
                    r["name"],
                    r["slug"],
                    r["category_id"],
                    r["category_name"],
                    r["is_active"],
                )
                for r in rows
            ],
        )
    conn.commit()
    log.info(f"  [dim_product] {len(rows)} produits chargés")


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACT
# ═══════════════════════════════════════════════════════════════════════════════


def extract_order_lines(orders_conn) -> list[dict]:
    """Extrait toutes les lignes de commande avec leur commande associée."""
    with orders_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                ol.id           AS order_line_id,
                ol.order_id,
                ol.product_id,
                ol.quantity,
                o.customer_id,
                o.status        AS order_status,
                o.created_at
            FROM orders_orderline ol
            JOIN orders_order o ON ol.order_id = o.id
            ORDER BY ol.id
        """)
        rows = [dict(r) for r in cur.fetchall()]
    log.info(f"  [order_lines] {len(rows)} lignes de commande extraites")
    return rows


def extract_customers(customers_conn) -> dict[int, dict]:
    """Retourne un dict customer_id → {country, city, ...}."""
    with customers_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                c.id,
                c.first_name,
                c.last_name,
                c.email,
                c.phone,
                c.is_active,
                COALESCE(
                    (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                    (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1),
                    'Inconnu'
                ) AS country,
                COALESCE(
                    (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                    (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1),
                    'Inconnu'
                ) AS city
            FROM catalog_customer c
        """)
        return {r["id"]: dict(r) for r in cur.fetchall()}


def extract_products(catalog_conn) -> dict[int, dict]:
    """Retourne un dict product_id → {name, price, category_id, category_name}."""
    with catalog_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                p.id,
                p.name,
                p.price,
                p.category_id,
                c.name AS category_name
            FROM catalog_product p
            LEFT JOIN catalog_category c ON p.category_id = c.id
            WHERE p.is_active = TRUE
        """)
        return {r["id"]: dict(r) for r in cur.fetchall()}


# ═══════════════════════════════════════════════════════════════════════════════
# TRANSFORM + LOAD FACT
# ═══════════════════════════════════════════════════════════════════════════════


def load_fact_order_lines(
    bi_conn,
    order_lines: list[dict],
    customers: dict[int, dict],
    products: dict[int, dict],
) -> tuple[int, int]:

    # Vide la table pour faire un insert bulk rapide
    with bi_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE fact_order_lines;")
    bi_conn.commit()

    rows = []
    skipped = 0

    for line in order_lines:
        customer = customers.get(line["customer_id"])
        product = products.get(line["product_id"])

        if not customer or not product:
            skipped += 1
            continue

        order_date = line["created_at"]
        date_id = int(order_date.strftime("%Y%m%d")) if order_date else None
        unit_price = float(product["price"])
        quantity = line["quantity"] or 1
        line_total = unit_price * quantity

        rows.append(
            (
                line["order_line_id"],
                line["order_id"],
                line["customer_id"],
                line["product_id"],
                product["category_id"],
                date_id,
                customer["country"],
                quantity,
                unit_price,
                line_total,
                line["order_status"],
            )
        )

    insert_sql = """
        INSERT INTO fact_order_lines (
            order_line_id, order_id, customer_id, product_id, category_id,
            date_id, country, quantity, unit_price, line_total, order_status
        ) VALUES %s
    """

    with bi_conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, insert_sql, rows, page_size=5000)
    bi_conn.commit()

    inserted = len(rows)
    log.info(
        f"  [fact_order_lines] {inserted} insérées, {skipped} ignorées"
    )
    return inserted, skipped


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════


def run_etl() -> None:
    start = datetime.now()
    log.info("=" * 60)
    log.info("Démarrage ETL — Schéma en étoile")
    log.info("=" * 60)

    # Ouvre les connexions sources
    conn_orders = psycopg2.connect(**ORDERS_DB)
    conn_customers = psycopg2.connect(**CUSTOMERS_DB)
    conn_catalog = psycopg2.connect(**CATALOG_DB)
    conn_bi = psycopg2.connect(**BI_DB)

    try:
        # Initialise le schéma BI
        with conn_bi.cursor() as cur:
            cur.execute(DDL)
        conn_bi.commit()
        log.info("  [bi] Schéma initialisé")

        # ═══ Dimensions ═══
        log.info("LOAD DIMENSIONS")
        load_dim_date(conn_bi, date(2020, 1, 1), date.today())
        load_dim_customer(conn_bi, conn_customers)
        load_dim_category(conn_bi, conn_catalog)
        load_dim_product(conn_bi, conn_catalog)

        # ═══ Extract sources ═══
        log.info("EXTRACT")
        order_lines = extract_order_lines(conn_orders)
        customers = extract_customers(conn_customers)
        products = extract_products(conn_catalog)

        # ═══ Fait ═══
        log.info("LOAD FAIT")
        load_fact_order_lines(conn_bi, order_lines, customers, products)

        # ═══ Vues analytiques ═══
        views_path = "/app/bi_views.sql"
        if os.path.exists(views_path):
            with open(views_path, "r", encoding="utf-8") as f:
                views_sql = f.read()
            with conn_bi.cursor() as cur:
                cur.execute(views_sql)
            conn_bi.commit()
            log.info("  [bi] Vues analytiques créées/mises à jour")
        else:
            log.warning("  [bi] Fichier bi_views.sql non trouvé, vues ignorées")

    finally:
        conn_orders.close()
        conn_customers.close()
        conn_catalog.close()
        conn_bi.close()

    elapsed = (datetime.now() - start).total_seconds()
    log.info("=" * 60)
    log.info(f"ETL terminé en {elapsed:.2f}s")
    log.info("=" * 60)


if __name__ == "__main__":
    run_etl()
