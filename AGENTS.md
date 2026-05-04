# AGENTS.md — TP Architecture Logicielle (Zalandouille)

## Contexte

Projet étudiant d'architecture logicielle (TP8-9). Application e-commerce "Zalandouille" découpée en **microservices** avec frontend React, base de données analytique (BI) et ETL.

---

## Architecture globale

| Service | Tech | Port | DB | Rôle |
|---------|------|------|----|------|
| `catalog-service` | Django 4.2 + DRF | 8001 | PostgreSQL (5431) | Produits & catégories (lecture seule API) |
| `customers-sercice` | Django 5.2 + DRF | 8000 | PostgreSQL (5435) | Clients & adresses |
| `orders-service` | Django 5.2 + DRF | 8002 | PostgreSQL (5433) | Commandes & lignes de commande |
| `frontend` | React 18 + Vite | 5173 | — | SPA de gestion (clients, catalogue, commandes) |
| `analytics` | Superset + Python ETL | 8088 | PostgreSQL BI (5434) | BI / schéma en étoile |
| `pgadmin` | pgAdmin 4 | 5050 | — | Admin des 4 PostgreSQL |

> **Note:** Le dossier `customers-sercice` contient une faute de frappe (`sercice` au lieu de `service`). Ne pas renommer sans mettre à jour le `docker-compose.yml` racine.

---

## Démarrage

```bash
# Lancer l'ensemble de la stack
docker-compose up --build -d

# Migrer orders-service (ajout du champ quantity)
docker exec orders_service python manage.py migrate

# Lancer l'ETL
cd etl
python etl_sales.py

# Créer les vues Superset
docker cp analytics/bi_views.sql bi_db:/tmp/bi_views.sql
docker exec bi_db psql -U bi_user -d bi_db -f /tmp/bi_views.sql

# URLs utiles
# - Frontend : http://localhost:5173
# - API Catalog : http://localhost:8001/api/
# - API Customers : http://localhost:8000/api/customers/
# - API Orders : http://localhost:8002/api/orders/
# - pgAdmin : http://localhost:5050 (admin@admin.com / admin)
# - Superset : http://localhost:8088
```

---

## Conventions de code

### Python (Django)
- **Style**: PEP 8, docstrings en français (projet école).
- **Imports**: `django` → tiers → locaux.
- **Sérialiseurs**: préférer `ModelSerializer`, gérer les relations en `read_only` quand approprié.
- **Views**: 
  - Catalog utilise des `ViewSet` (DRF) avec `DefaultRouter`.
  - Customers utilise des `@api_view` FBV avec `drf-spectacular` pour la doc OpenAPI.
  - Orders utilise un `ModelViewSet` restreint à `get`, `post`.
- **Modèles**: `default_auto_field = 'django.db.models.BigAutoField'` partout.
- **Bases de données**: 
  - Catalog: tables `catalog_category`, `catalog_product`
  - Customers: tables `catalog_customer`, `catalog_address` (legacy naming)
  - Orders: tables `orders_order`, `orders_orderline` (avec `quantity` depuis migration 0003)

### React (Frontend)
- **Style inline uniquement** : pas de CSS modules ni de styled-components. Tous les styles sont des objets JS dans les composants.
- **API**: centralisée dans `frontend/src/api.js` (à créer/maintenir).
- **Routage**: `react-router-dom` avec `BrowserRouter`.
- **Conventions de nommage**: PascalCase pour les composants, camelCase pour les variables/fonctions.

### ETL (`etl/etl_sales.py`)
- Schéma en **étoile** : `dim_date`, `dim_customer`, `dim_category`, `dim_product`, `fact_order_lines`.
- **Grain** : `fact_order_lines` = 1 ligne par ligne de commande (pas 1 ligne par commande).
- Connexions directes en psycopg2 vers les 4 PostgreSQL (hors Docker, ports exposés).
- Le script est idempotent (upsert via `ON CONFLICT`).
- `dim_product` contient `category_name` dénormalisé.

---

## Communication inter-services

- **Orders → Catalog** : HTTP via `requests.get()` vers `CATALOG_SERVICE_URL` (résolu via Docker hostname `catalog-web`).
- Le `orders-service` récupère le prix et le nom du produit en temps réel depuis le catalog lors de la création d'une commande.
- **Pas de service discovery** : URLs hardcodées dans `docker-compose.yml` via variables d'environnement.

---

## Base de données BI (ETL)

Dimensions et table de faits alimentées par `etl/etl_sales.py` :

```
dim_date         (date_id PK YYYYMMDD, year, quarter, month, month_name, day, day_name)
dim_customer     (customer_id PK, first_name, last_name, email, phone, is_active, country, city)
dim_category     (category_id PK, category_name, category_slug)
dim_product      (product_id PK, product_name, slug, category_id, category_name, is_active)
fact_order_lines (order_line_id PK, order_id, customer_id, product_id, category_id, date_id,
                  country, quantity, unit_price, line_total, order_status)
```

**Vues pour Superset** (`analytics/bi_views.sql`) :
- `vw_fact_order_lines_complete` — faits + dimensions jointes
- `vw_sales_by_country` — agrégation par pays
- `vw_sales_by_month` — agrégation par mois
- `vw_sales_by_category` — agrégation par catégorie
- `vw_sales_by_customer` — agrégation par client
- `vw_top_products` — top produits

Pour lancer l'ETL (hors conteneur, Python local avec `psycopg2`) :
```bash
cd etl
python etl_sales.py
```

---

## Superset — Export / Import

**Exporter les dashboards** (depuis la machine qui a les charts) :
```bash
bash analytics/export-superset.sh
```
Puis committer `analytics/superset_export.zip`.

**Importer les dashboards** (pour les collègues) :
```bash
bash analytics/import-superset.sh
```

---

## Points d'attention

1. **Dossier `customers-sercice`** : la faute est présente partout (`docker-compose.yml`, paths). Maintenir la cohérence si modifications.
2. **CORS** : activé partout (`CORS_ALLOW_ALL_ORIGINS = True` en dev).
3. **DEBUG** : tous les services Django sont en `DEBUG = True`.
4. **Entrées des services** : 
   - Catalog utilise un `entrypoint.sh` personnalisé.
   - Customers et Orders utilisent `python manage.py runserver` en CMD (dev uniquement).
5. **Imports JSON** : fichiers `catalog_import_10k.json` et `orders_import_20k.json` présents pour peupler les DB.
6. **Migration orders-service 0003** : ajoute le champ `quantity` sur `OrderLine`, nécessaire pour le grain ligne de commande dans le DW.

---

## Tests

- Pas de tests automatisés actuellement. Ajouter des tests Django (`python manage.py test`) ou React (Vitest) si demandé.

---

## Tâches typiques

- **Ajouter un endpoint API** : modifier `views.py`/`urls.py` dans le service concerné.
- **Modifier un modèle** : `models.py` → `makemigrations` → `migrate`.
- **Modifier le frontend** : composants dans `frontend/src/components/`, logique API dans `frontend/src/api.js`.
- **Modifier le schéma BI** : mettre à jour `DDL` dans `etl/etl_sales.py` + réinitialiser la DB BI.
- **Ajouter un service** : ajouter le service dans `docker-compose.yml` racine et créer son dossier.
