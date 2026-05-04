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
  - Orders: tables `orders_order`, `orders_orderline`

### React (Frontend)
- **Style inline uniquement** : pas de CSS modules ni de styled-components. Tous les styles sont des objets JS dans les composants.
- **API**: centralisée dans `frontend/src/api.js` (à créer/maintenir).
- **Routage**: `react-router-dom` avec `BrowserRouter`.
- **Conventions de nommage**: PascalCase pour les composants, camelCase pour les variables/fonctions.

### ETL (`etl/etl_sales.py`)
- Schéma en **étoile** : `dim_date`, `dim_pays`, `dim_categorie`, `dim_produit`, `fact_sales`.
- Connexions directes en psycopg2 vers les 4 PostgreSQL (hors Docker, ports exposés).
- Le script est idempotent (upsert via `ON CONFLICT`).

---

## Communication inter-services

- **Orders → Catalog** : HTTP via `requests.get()` vers `CATALOG_SERVICE_URL` (résolu via Docker hostname `catalog-web`).
- Le `orders-service` récupère le prix et le nom du produit en temps réel depuis le catalog lors de la création d'une commande.
- **Pas de service discovery** : URLs hardcodées dans `docker-compose.yml` via variables d'environnement.

---

## Base de données BI (ETL)

Dimensions et table de faits alimentées par `etl/etl_sales.py` :

```
dim_date       (date_id PK YYYYMMDD)
dim_pays       (pays_id, city, country)
dim_categorie  (categorie_id PK, name, slug)
dim_produit    (produit_id PK, name, price, categorie_id)
fact_sales     (order_id, date_id, pays_id, produit_id, categorie_id, customer_id, ...)
```

Pour lancer l'ETL (hors conteneur, Python local avec `psycopg2`) :
```bash
cd etl
python etl_sales.py
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
