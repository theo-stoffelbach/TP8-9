"""
ETL - Table de faits BI : fact_sales
======================================
Ce script ETL extrait les données des 3 microservices (catalog, customers, orders),
les transforme en une table de faits dénormalisée et les charge dans une BDD BI.

Grain de la table : 1 ligne = 1 commande (Order)
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
    "host": "localhost",
    "port": 5432,
    "dbname": "catalog_db",
    "user": "catalog_user",
    "password": "catalog_pass",
}

CUSTOMERS_DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "customer_db",
    "user": "customer_user",
    "password": "customer_password",
}

ORDERS_DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "order_db",
    "user": "order_user",
    "password": "order_pass",
}

# ─── Connexion destination (BDD BI) ───────────────────────────────────────────

BI_DB = {
    "host": "localhost",
    "port": 5434,  # port mappé dans docker-compose pour la BDD BI
    "dbname": "bi_db",
    "user": "bi_user",
    "password": "bi_pass",
}

# ─── DDL tables BI ────────────────────────────────────────────────────────────

DDL_DIM_DATE = """
CREATE TABLE IF NOT EXISTS dim_date (
    date_id         INTEGER       PRIMARY KEY,  -- clé YYYYMMDD ex: 20240315

    -- Date brute
    full_date       DATE          NOT NULL UNIQUE,

    -- Décomposition
    year            SMALLINT      NOT NULL,
    quarter         SMALLINT      NOT NULL,  -- 1-4
    month           SMALLINT      NOT NULL,  -- 1-12
    month_name      VARCHAR(20)   NOT NULL,  -- 'Janvier', 'Février'…
    week            SMALLINT      NOT NULL,  -- numéro de semaine ISO
    day_of_month    SMALLINT      NOT NULL,  -- 1-31
    day_of_week     SMALLINT      NOT NULL,  -- 1=Lundi … 7=Dimanche (ISO)
    day_name        VARCHAR(20)   NOT NULL,  -- 'Lundi', 'Mardi'…

    -- Indicateurs pratiques
    is_weekend      BOOLEAN       NOT NULL,
    is_month_start  BOOLEAN       NOT NULL,
    is_month_end    BOOLEAN       NOT NULL
);
"""

DDL_FACT_SALES = """
CREATE TABLE IF NOT EXISTS fact_sales (
    id                  SERIAL PRIMARY KEY,

    -- Dimension Commande
    order_id            INTEGER       NOT NULL,
    order_date          TIMESTAMP,
    order_status        VARCHAR(20),
    order_total         DECIMAL(10,2),

    -- Dimension Client
    customer_id         INTEGER,
    customer_full_name  VARCHAR(200),
    customer_email      VARCHAR(254),
    customer_city       VARCHAR(100),
    customer_country    VARCHAR(100),

    -- Dimension Produit (produit le plus cher de la commande)
    product_id          INTEGER,
    product_name        VARCHAR(200),
    product_category    VARCHAR(100),
    product_price       DECIMAL(10,2),

    -- Métriques
    nb_order_lines      INTEGER,

    -- Lien vers dim_date
    date_id             INTEGER       REFERENCES dim_date(date_id),

    -- Métadonnées ETL
    etl_loaded_at       TIMESTAMP     DEFAULT NOW(),

    CONSTRAINT uq_fact_sales_order UNIQUE (order_id)
);
"""


MONTH_NAMES = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]
DAY_NAMES = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def generate_dim_date(conn, start: date, end: date) -> None:
    """
    Remplit dim_date pour chaque jour entre start et end (inclus).
    Ignore les dates déjà présentes (ON CONFLICT DO NOTHING).
    """
    sql = """
        INSERT INTO dim_date (
            date_id, full_date, year, quarter, month, month_name,
            week, day_of_month, day_of_week, day_name,
            is_weekend, is_month_start, is_month_end
        ) VALUES %s
        ON CONFLICT (date_id) DO NOTHING
    """
    rows = []
    current = start
    while current <= end:
        last_day = calendar.monthrange(current.year, current.month)[1]
        rows.append((
            int(current.strftime("%Y%m%d")),   # date_id  ex: 20240315
            current,                            # full_date
            current.year,
            (current.month - 1) // 3 + 1,      # quarter
            current.month,
            MONTH_NAMES[current.month],
            current.isocalendar()[1],           # week ISO
            current.day,
            current.isoweekday(),               # 1=Lundi … 7=Dimanche
            DAY_NAMES[current.weekday()],
            current.isoweekday() >= 6,          # is_weekend
            current.day == 1,                   # is_month_start
            current.day == last_day,            # is_month_end
        ))
        current += timedelta(days=1)

    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, rows)
    conn.commit()
    log.info(f"  [bi] dim_date remplie : {len(rows)} jours ({start} → {end})")


# ─── EXTRACT ──────────────────────────────────────────────────────────────────

def extract_orders(conn) -> list[dict]:
    """Extrait toutes les commandes avec leurs lignes depuis orders_db."""
    query = """
        SELECT
            o.id            AS order_id,
            o.customer_id,
            o.status,
            o.total_amount,
            o.created_at,
            COUNT(ol.id)    AS nb_lines,
            -- on garde tous les product_id comme liste pour le transform
            ARRAY_AGG(ol.product_id) AS product_ids
        FROM orders_order o
        LEFT JOIN orders_orderline ol ON ol.order_id = o.id
        GROUP BY o.id, o.customer_id, o.status, o.total_amount, o.created_at
        ORDER BY o.id
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(query)
        rows = [dict(r) for r in cur.fetchall()]
    log.info(f"  [orders] {len(rows)} commandes extraites")
    return rows


def extract_customers(conn) -> dict[int, dict]:
    """Extrait les clients avec leur ville principale depuis customers_db."""
    query = """
        SELECT
            c.id,
            c.first_name,
            c.last_name,
            c.email,
            -- adresse par défaut ou première disponible
            COALESCE(
                (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                (SELECT a.city    FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1)
            ) AS city,
            COALESCE(
                (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id AND a.is_default = TRUE LIMIT 1),
                (SELECT a.country FROM catalog_address a WHERE a.customer_id = c.id LIMIT 1)
            ) AS country
        FROM catalog_customer c
        WHERE c.is_active = TRUE
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()
    customers = {r["id"]: dict(r) for r in rows}
    log.info(f"  [customers] {len(customers)} clients extraits")
    return customers


def extract_products(conn) -> dict[int, dict]:
    """Extrait les produits avec leur catégorie depuis catalog_db."""
    query = """
        SELECT
            p.id,
            p.name,
            p.price,
            cat.name AS category
        FROM catalog_product p
        JOIN catalog_category cat ON cat.id = p.category_id
        WHERE p.is_active = TRUE
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute(query)
        rows = cur.fetchall()
    products = {r["id"]: dict(r) for r in rows}
    log.info(f"  [catalog] {len(products)} produits extraits")
    return products


# ─── TRANSFORM ────────────────────────────────────────────────────────────────

def transform(
    orders: list[dict],
    customers: dict[int, dict],
    products: dict[int, dict],
) -> list[dict]:
    """
    Joint les 3 sources et construit les lignes de la fact_sales.
    Règle métier : pour la dimension produit, on retient le produit
    le plus cher parmi les lignes de la commande.
    """
    rows = []
    skipped = 0

    for order in orders:
        customer = customers.get(order["customer_id"])
        if customer is None:
            log.debug(f"  Commande {order['order_id']} ignorée : client {order['customer_id']} introuvable")
            skipped += 1
            continue

        # Produit principal = le plus cher de la commande
        order_products = [
            products[pid]
            for pid in (order["product_ids"] or [])
            if pid in products
        ]
        main_product = max(order_products, key=lambda p: p["price"]) if order_products else None

        order_date = order["created_at"]
        date_id = int(order_date.strftime("%Y%m%d")) if order_date else None

        rows.append({
            "order_id":           order["order_id"],
            "order_date":         order_date,
            "order_status":       order["status"],
            "order_total":        float(order["total_amount"]),
            "customer_id":        customer["id"],
            "customer_full_name": f"{customer['first_name']} {customer['last_name']}",
            "customer_email":     customer["email"],
            "customer_city":      customer.get("city"),
            "customer_country":   customer.get("country"),
            "product_id":         main_product["id"]    if main_product else None,
            "product_name":       main_product["name"]  if main_product else None,
            "product_category":   main_product["category"] if main_product else None,
            "product_price":      float(main_product["price"]) if main_product else None,
            "nb_order_lines":     order["nb_lines"] or 0,
            "date_id":            date_id,
        })

    log.info(f"  [transform] {len(rows)} lignes prêtes, {skipped} commandes ignorées")
    return rows


# ─── LOAD ─────────────────────────────────────────────────────────────────────

def init_bi_schema(conn) -> None:
    """Crée les tables si elles n'existent pas encore (dim_date avant fact_sales pour la FK)."""
    with conn.cursor() as cur:
        cur.execute(DDL_DIM_DATE)
        cur.execute(DDL_FACT_SALES)
    conn.commit()
    log.info("  [bi] Schéma initialisé")


def load(conn, rows: list[dict]) -> tuple[int, int]:
    """
    Insère ou met à jour les lignes (upsert sur order_id).
    Retourne (inserted, updated).
    """
    if not rows:
        log.warning("  [load] Aucune ligne à charger")
        return 0, 0

    upsert_sql = """
        INSERT INTO fact_sales (
            order_id, order_date, order_status, order_total,
            customer_id, customer_full_name, customer_email,
            customer_city, customer_country,
            product_id, product_name, product_category, product_price,
            nb_order_lines, date_id, etl_loaded_at
        ) VALUES (
            %(order_id)s, %(order_date)s, %(order_status)s, %(order_total)s,
            %(customer_id)s, %(customer_full_name)s, %(customer_email)s,
            %(customer_city)s, %(customer_country)s,
            %(product_id)s, %(product_name)s, %(product_category)s, %(product_price)s,
            %(nb_order_lines)s, %(date_id)s, NOW()
        )
        ON CONFLICT (order_id) DO UPDATE SET
            order_status        = EXCLUDED.order_status,
            order_total         = EXCLUDED.order_total,
            customer_full_name  = EXCLUDED.customer_full_name,
            customer_email      = EXCLUDED.customer_email,
            customer_city       = EXCLUDED.customer_city,
            customer_country    = EXCLUDED.customer_country,
            product_id          = EXCLUDED.product_id,
            product_name        = EXCLUDED.product_name,
            product_category    = EXCLUDED.product_category,
            product_price       = EXCLUDED.product_price,
            nb_order_lines      = EXCLUDED.nb_order_lines,
            date_id             = EXCLUDED.date_id,
            etl_loaded_at       = NOW()
    """

    inserted = updated = 0
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                "SELECT 1 FROM fact_sales WHERE order_id = %s", (row["order_id"],)
            )
            exists = cur.fetchone() is not None
            cur.execute(upsert_sql, row)
            if exists:
                updated += 1
            else:
                inserted += 1

    conn.commit()
    log.info(f"  [bi] {inserted} insérées, {updated} mises à jour")
    return inserted, updated


# ─── PIPELINE PRINCIPAL ────────────────────────────────────────────────────────

def run_etl() -> None:
    start = datetime.now()
    log.info("=" * 60)
    log.info("Démarrage ETL fact_sales")
    log.info("=" * 60)

    # ── Extract ──────────────────────────────────────────────────
    log.info("EXTRACT")
    try:
        conn_orders = psycopg2.connect(**ORDERS_DB)
        orders = extract_orders(conn_orders)
    except Exception as e:
        log.error(f"Erreur connexion orders_db : {e}")
        raise
    finally:
        conn_orders.close()

    try:
        conn_customers = psycopg2.connect(**CUSTOMERS_DB)
        customers = extract_customers(conn_customers)
    except Exception as e:
        log.error(f"Erreur connexion customers_db : {e}")
        raise
    finally:
        conn_customers.close()

    try:
        conn_catalog = psycopg2.connect(**CATALOG_DB)
        products = extract_products(conn_catalog)
    except Exception as e:
        log.error(f"Erreur connexion catalog_db : {e}")
        raise
    finally:
        conn_catalog.close()

    # ── Transform ────────────────────────────────────────────────
    log.info("TRANSFORM")
    rows = transform(orders, customers, products)

    # ── Load ─────────────────────────────────────────────────────
    log.info("LOAD")
    try:
        conn_bi = psycopg2.connect(**BI_DB)
        init_bi_schema(conn_bi)
        # dim_date couvre 2020 → aujourd'hui
        generate_dim_date(conn_bi, date(2020, 1, 1), date.today())
        inserted, updated = load(conn_bi, rows)
    except Exception as e:
        log.error(f"Erreur connexion bi_db : {e}")
        raise
    finally:
        conn_bi.close()

    elapsed = (datetime.now() - start).total_seconds()
    log.info("=" * 60)
    log.info(f"ETL terminé en {elapsed:.2f}s — {inserted} insérées, {updated} mises à jour")
    log.info("=" * 60)


if __name__ == "__main__":
    run_etl()
