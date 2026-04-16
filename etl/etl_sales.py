"""
ETL - Schéma en étoile BI
==========================
Dimensions : dim_date, dim_pays, dim_produit, dim_categorie
Fait       : fact_sales

Grain de fact_sales : 1 ligne = 1 commande
"""

import calendar
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

# ─── Connexions sources ────────────────────────────────────────────────────────

CATALOG_DB = {
    "host": "localhost", "port": 5432,
    "dbname": "catalog_db", "user": "catalog_user", "password": "catalog_pass",
}
CUSTOMERS_DB = {
    "host": "localhost", "port": 5432,
    "dbname": "customer_db", "user": "customer_user", "password": "customer_password",
}
ORDERS_DB = {
    "host": "localhost", "port": 5432,
    "dbname": "order_db", "user": "order_user", "password": "order_pass",
}

# ─── Connexion destination BI ─────────────────────────────────────────────────

BI_DB = {
    "host": "localhost", "port": 5434,
    "dbname": "bi_db", "user": "bi_user", "password": "bi_pass",
}

# ─── DDL ──────────────────────────────────────────────────────────────────────

DDL = """
-- 1. Dimension Date
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER     PRIMARY KEY,        -- clé YYYYMMDD
    full_date       DATE        NOT NULL UNIQUE,
    year            SMALLINT    NOT NULL,
    quarter         SMALLINT    NOT NULL,
    month           SMALLINT    NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    week            SMALLINT    NOT NULL,
    day_of_month    SMALLINT    NOT NULL,
    day_of_week     SMALLINT    NOT NULL,
    day_name        VARCHAR(20) NOT NULL,
    is_weekend      BOOLEAN     NOT NULL,
    is_month_start  BOOLEAN     NOT NULL,
    is_month_end    BOOLEAN     NOT NULL
);

-- 2. Dimension Pays / Ville
CREATE TABLE IF NOT EXISTS dim_pays (
    pays_id     SERIAL      PRIMARY KEY,
    city        VARCHAR(100),
    country     VARCHAR(100),
    CONSTRAINT uq_dim_pays UNIQUE (city, country)
);

-- 3. Dimension Catégorie
CREATE TABLE IF NOT EXISTS dim_categorie (
    categorie_id    INTEGER     PRIMARY KEY,        -- id issu du catalog
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(100) NOT NULL
);

-- 4. Dimension Produit
CREATE TABLE IF NOT EXISTS dim_produit (
    produit_id      INTEGER     PRIMARY KEY,        -- id issu du catalog
    name            VARCHAR(200) NOT NULL,
    price           DECIMAL(10,2) NOT NULL,
    categorie_id    INTEGER     REFERENCES dim_categorie(categorie_id)
);

-- 5. Table de faits
CREATE TABLE IF NOT EXISTS fact_sales (
    id              SERIAL      PRIMARY KEY,
    order_id        INTEGER     NOT NULL,
    order_status    VARCHAR(20),
    order_total     DECIMAL(10,2),
    nb_order_lines  INTEGER,

    -- Clés étrangères vers les dimensions
    date_id         INTEGER     REFERENCES dim_date(date_id),
    pays_id         INTEGER     REFERENCES dim_pays(pays_id),
    produit_id      INTEGER     REFERENCES dim_produit(produit_id),
    categorie_id    INTEGER     REFERENCES dim_categorie(categorie_id),

    -- Métadonnées ETL
    customer_id     INTEGER,
    etl_loaded_at   TIMESTAMP   DEFAULT NOW(),

    CONSTRAINT uq_fact_sales_order UNIQUE (order_id)
);
"""

# ─── HELPERS ──────────────────────────────────────────────────────────────────

MONTH_NAMES = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
DAY_NAMES = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


# ─── LOAD DIMENSIONS ──────────────────────────────────────────────────────────

def load_dim_date(conn, start: date, end: date) -> None:
    """Génère une ligne par jour entre start et end."""
    rows = []
    current = start
    while current <= end:
        last_day = calendar.monthrange(current.year, current.month)[1]
        rows.append((
            int(current.strftime("%Y%m%d")),
            current,
            current.year,
            (current.month - 1) // 3 + 1,
            current.month,
            MONTH_NAMES[current.month],
            current.isocalendar()[1],
            current.day,
            current.isoweekday(),
            DAY_NAMES[current.weekday()],
            current.isoweekday() >= 6,
            current.day == 1,
            current.day == last_day,
        ))
        current += timedelta(days=1)

    sql = """
        INSERT INTO dim_date (
            date_id, full_date, year, quarter, month, month_name,
            week, day_of_month, day_of_week, day_name,
            is_weekend, is_month_start, is_month_end
        ) VALUES %s
        ON CONFLICT (date_id) DO NOTHING
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
    conn.commit()
    log.info(f"  [dim_date] {len(rows)} jours chargés ({start} → {end})")


def load_dim_pays(conn, customers_conn) -> dict[tuple, int]:
    """
    Extrait les paires (city, country) uniques depuis customers_db
    et les insère dans dim_pays. Retourne un dict (city, country) → pays_id.
    """
    with customers_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT DISTINCT
                COALESCE(city, 'Inconnu')    AS city,
                COALESCE(country, 'Inconnu') AS country
            FROM catalog_address
        """)
        pairs = cur.fetchall()

    sql = """
        INSERT INTO dim_pays (city, country)
        VALUES %s
        ON CONFLICT (city, country) DO NOTHING
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, [(r["city"], r["country"]) for r in pairs])
    conn.commit()

    # Récupère tous les pays_id pour mapping
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT pays_id, city, country FROM dim_pays")
        mapping = {(r["city"], r["country"]): r["pays_id"] for r in cur.fetchall()}

    log.info(f"  [dim_pays] {len(mapping)} localisations chargées")
    return mapping


def load_dim_categorie(conn, catalog_conn) -> None:
    """Synchronise dim_categorie depuis catalog_db."""
    with catalog_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT id, name, slug FROM catalog_category")
        rows = cur.fetchall()

    sql = """
        INSERT INTO dim_categorie (categorie_id, name, slug)
        VALUES %s
        ON CONFLICT (categorie_id) DO UPDATE SET
            name = EXCLUDED.name,
            slug = EXCLUDED.slug
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, [(r["id"], r["name"], r["slug"]) for r in rows])
    conn.commit()
    log.info(f"  [dim_categorie] {len(rows)} catégories chargées")


def load_dim_produit(conn, catalog_conn) -> None:
    """Synchronise dim_produit depuis catalog_db."""
    with catalog_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, name, price, category_id
            FROM catalog_product
            WHERE is_active = TRUE
        """)
        rows = cur.fetchall()

    sql = """
        INSERT INTO dim_produit (produit_id, name, price, categorie_id)
        VALUES %s
        ON CONFLICT (produit_id) DO UPDATE SET
            name         = EXCLUDED.name,
            price        = EXCLUDED.price,
            categorie_id = EXCLUDED.categorie_id
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur, sql, [(r["id"], r["name"], float(r["price"]), r["category_id"]) for r in rows]
        )
    conn.commit()
    log.info(f"  [dim_produit] {len(rows)} produits chargés")


# ─── EXTRACT ──────────────────────────────────────────────────────────────────

def extract_orders(orders_conn) -> list[dict]:
    with orders_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                o.id            AS order_id,
                o.customer_id,
                o.status,
                o.total_amount,
                o.created_at,
                COUNT(ol.id)            AS nb_lines,
                ARRAY_AGG(ol.product_id) AS product_ids
            FROM orders_order o
            LEFT JOIN orders_orderline ol ON ol.order_id = o.id
            GROUP BY o.id
            ORDER BY o.id
        """)
        rows = [dict(r) for r in cur.fetchall()]
    log.info(f"  [orders] {len(rows)} commandes extraites")
    return rows


def extract_customers(customers_conn) -> dict[int, dict]:
    """Retourne un dict customer_id → {city, country}."""
    with customers_conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT
                c.id,
                COALESCE(
                    (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                    (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1),
                    'Inconnu'
                ) AS city,
                COALESCE(
                    (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                    (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1),
                    'Inconnu'
                ) AS country
            FROM catalog_customer c
            WHERE c.is_active = TRUE
        """)
        return {r["id"]: dict(r) for r in cur.fetchall()}


def extract_main_product(product_ids: list, catalog_products: dict) -> dict | None:
    """Retourne le produit le plus cher parmi les lignes d'une commande."""
    prods = [catalog_products[pid] for pid in (product_ids or []) if pid in catalog_products]
    return max(prods, key=lambda p: p["price"]) if prods else None


# ─── TRANSFORM + LOAD FACT ────────────────────────────────────────────────────

def load_fact_sales(
    bi_conn,
    orders: list[dict],
    customers: dict[int, dict],
    catalog_products: dict[int, dict],
    pays_mapping: dict[tuple, int],
) -> tuple[int, int]:

    upsert_sql = """
        INSERT INTO fact_sales (
            order_id, order_status, order_total, nb_order_lines,
            date_id, pays_id, produit_id, categorie_id,
            customer_id, etl_loaded_at
        ) VALUES (
            %(order_id)s, %(order_status)s, %(order_total)s, %(nb_order_lines)s,
            %(date_id)s, %(pays_id)s, %(produit_id)s, %(categorie_id)s,
            %(customer_id)s, NOW()
        )
        ON CONFLICT (order_id) DO UPDATE SET
            order_status   = EXCLUDED.order_status,
            order_total    = EXCLUDED.order_total,
            nb_order_lines = EXCLUDED.nb_order_lines,
            pays_id        = EXCLUDED.pays_id,
            produit_id     = EXCLUDED.produit_id,
            categorie_id   = EXCLUDED.categorie_id,
            etl_loaded_at  = NOW()
    """

    inserted = updated = skipped = 0

    with bi_conn.cursor() as cur:
        for order in orders:
            customer = customers.get(order["customer_id"])
            if not customer:
                skipped += 1
                continue

            order_date = order["created_at"]
            date_id    = int(order_date.strftime("%Y%m%d")) if order_date else None
            pays_id    = pays_mapping.get((customer["city"], customer["country"]))
            main_prod  = extract_main_product(order["product_ids"], catalog_products)

            cur.execute("SELECT 1 FROM fact_sales WHERE order_id = %s", (order["order_id"],))
            exists = cur.fetchone() is not None

            cur.execute(upsert_sql, {
                "order_id":      order["order_id"],
                "order_status":  order["status"],
                "order_total":   float(order["total_amount"]),
                "nb_order_lines": order["nb_lines"] or 0,
                "date_id":       date_id,
                "pays_id":       pays_id,
                "produit_id":    main_prod["id"]          if main_prod else None,
                "categorie_id":  main_prod["category_id"] if main_prod else None,
                "customer_id":   order["customer_id"],
            })
            updated += exists
            inserted += not exists

    bi_conn.commit()
    log.info(f"  [fact_sales] {inserted} insérées, {updated} mises à jour, {skipped} ignorées")
    return inserted, updated


# ─── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────

def run_etl() -> None:
    start = datetime.now()
    log.info("=" * 60)
    log.info("Démarrage ETL — schéma en étoile")
    log.info("=" * 60)

    # Ouvre les connexions sources
    conn_orders    = psycopg2.connect(**ORDERS_DB)
    conn_customers = psycopg2.connect(**CUSTOMERS_DB)
    conn_catalog   = psycopg2.connect(**CATALOG_DB)
    conn_bi        = psycopg2.connect(**BI_DB)

    try:
        # Initialise le schéma BI
        with conn_bi.cursor() as cur:
            cur.execute(DDL)
        conn_bi.commit()
        log.info("  [bi] Schéma initialisé")

        # ── Dimensions ──────────────────────────────────────────
        log.info("LOAD DIMENSIONS")
        load_dim_date(conn_bi, date(2020, 1, 1), date.today())
        pays_mapping = load_dim_pays(conn_bi, conn_customers)
        load_dim_categorie(conn_bi, conn_catalog)
        load_dim_produit(conn_bi, conn_catalog)

        # ── Extract sources ──────────────────────────────────────
        log.info("EXTRACT")
        orders = extract_orders(conn_orders)
        customers = extract_customers(conn_customers)

        with conn_catalog.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT id, name, price, category_id FROM catalog_product WHERE is_active = TRUE")
            catalog_products = {r["id"]: dict(r) for r in cur.fetchall()}
        log.info(f"  [catalog] {len(catalog_products)} produits extraits")

        # ── Fait ─────────────────────────────────────────────────
        log.info("LOAD FAIT")
        load_fact_sales(conn_bi, orders, customers, catalog_products, pays_mapping)

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
