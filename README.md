# Zalandouille — TP Architecture Logicielle

Projet éducatif d'architecture logicielle : application e-commerce découpée en **microservices** avec base de données analytique (BI) et ETL.

---

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │      │   Frontend      │      │   Frontend      │
│   (React/Vite)  │──────│   (React/Vite)  │──────│   (React/Vite)  │
│   Port 5173     │      │   Port 5173     │      │   Port 5173     │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Catalog Service │      │Customers Service│      │ Orders Service  │
│ Django + DRF    │      │ Django + DRF    │      │ Django + DRF    │
│ Port 8001       │      │ Port 8000       │      │ Port 8002       │
│ PostgreSQL 5431 │      │ PostgreSQL 5435 │      │ PostgreSQL 5433 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
         ▲                                               │
         │                                               │
         └───────────────────┬───────────────────────────┘
                             │ HTTP (requests)
                             ▼
                    ┌─────────────────┐
                    │      BI DB      │
                    │  PostgreSQL     │
                    │   Port 5434     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   Superset      │
                    │   Port 8088     │
                    └─────────────────┘
                             ▲
                             │ ETL Python
                    ┌────────┴────────┐
                    │  etl_sales.py   │
                    │ (psycopg2)      │
                    └─────────────────┘
```

### Services

| Service | Technologie | Port | Base de données | Rôle |
|---------|-------------|------|-----------------|------|
| **Catalog** | Django 4.2 + DRF | 8001 | PostgreSQL (5431) | Gestion des produits et catégories |
| **Customers** | Django 5.2 + DRF | 8000 | PostgreSQL (5435) | Gestion des clients et adresses |
| **Orders** | Django 5.2 + DRF | 8002 | PostgreSQL (5433) | Gestion des commandes (appelle Catalog pour les prix) |
| **Frontend** | React 18 + Vite | 5173 | — | Interface de gestion (SPA) |
| **BI** | PostgreSQL | 5434 | — | Base analytique (schéma en étoile) |
| **Superset** | Apache Superset | 8088 | BI DB | Dashboards et visualisations |
| **pgAdmin** | pgAdmin 4 | 5050 | — | Administration des bases de données |

---

## 🚀 Démarrage rapide

### Prérequis

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Lancer l'application

```bash
# Cloner le projet (si pas déjà fait)
cd TP8-9

# Lancer toute la stack
docker-compose up --build -d
```

### Peupler les données (optionnel)

```bash
# Customers
ocker exec -it customers_service python manage.py loaddata catalog_import_10k.json

# Orders
docker exec -it orders_service python manage.py loaddata orders_import_20k.json
```

### Lancer l'ETL (alimentation de la BI)

```bash
cd etl
python -m venv venv
# Windows :
venv\Scripts\activate
# macOS/Linux :
# source venv/bin/activate

pip install -r requirements.txt
python etl_sales.py
```

### Créer les vues pour Superset

Après avoir lancé l'ETL, exécute ce script SQL dans la base `bi_db` (via pgAdmin ou `psql`) :

```bash
psql -h localhost -p 5434 -U bi_user -d bi_db -f analytics/bi_views.sql
# password: bi_pass
```

Cela crée des vues prêtes à l'emploi pour Superset :
- `vw_fact_sales_complete` — toutes les données jointes (faits + dimensions)
- `vw_sales_by_country` — ventes agrégées par pays
- `vw_sales_by_month` — ventes agrégées par mois
- `vw_sales_by_category` — ventes agrégées par catégorie

---

## 🌐 URLs et accès

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Frontend** | http://localhost:5173 | — |
| **API Catalog** | http://localhost:8001/api/ | — |
| **API Customers** | http://localhost:8000/api/customers/ | — |
| **API Orders** | http://localhost:8002/api/orders/ | — |
| **pgAdmin** | http://localhost:5050 | `admin@admin.com` / `admin` |
| **Superset** | http://localhost:8088 | `admin` / `admin` |

### Identifiants des bases de données (PostgreSQL)

Pour se connecter via **pgAdmin** ou en ligne de commande (`psql`) :

| Base de données | Host | Port | Database | Utilisateur | Mot de passe |
|-----------------|------|------|----------|-------------|--------------|
| **Catalog DB** | `localhost` | `5431` | `catalog_db` | `catalog_user` | `catalog_pass` |
| **Customers DB** | `localhost` | `5435` | `customer_db` | `customer_user` | `customer_password` |
| **Orders DB** | `localhost` | `5433` | `order_db` | `order_user` | `order_pass` |
| **BI DB** | `localhost` | `5434` | `bi_db` | `bi_user` | `bi_pass` |

---

## 📡 Endpoints API

### Catalog Service (`:8001`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/categories/` | Liste des catégories |
| `GET` | `/api/products/` | Liste des produits (filtres : `?category=`, `?search=`, `?is_active=`) |
| `GET` | `/api/products/<id>/` | Détail d'un produit |

### Customers Service (`:8000`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/customers/` | Liste paginée des clients |
| `POST` | `/api/customers/` | Créer un client |
| `GET` | `/api/customers/<id>/` | Détail d'un client |
| `PATCH` | `/api/customers/<id>/` | Modifier un client |
| `GET` | `/api/customers/<id>/addresses/` | Adresses d'un client |
| `POST` | `/api/customers/<id>/addresses/` | Ajouter une adresse |
| `PATCH` | `/api/customers/<id>/addresses/<addr_id>/` | Modifier une adresse |

### Orders Service (`:8002`)

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/orders/` | Liste des commandes |
| `POST` | `/api/orders/` | Créer une commande |

---

## 📊 Schéma en étoile (BI)

Le script ETL (`etl/etl_sales.py`) alimente une base analytique avec le schéma suivant :

```
                    ┌─────────────┐
                    │   dim_date  │
                    └──────┬──────┘
                           │
    ┌─────────────┐   ┌────┴────┐   ┌────────────────┐
    │  dim_pays   │───│fact_sales│───│  dim_produit   │
    └─────────────┘   └────┬────┘   └───────┬────────┘
                           │                │
                    ┌──────┴──────┐  ┌──────┴──────┐
                    │  dim_date   │  │ dim_categorie│
                    └─────────────┘  └─────────────┘
```

**Tables :**
- `dim_date` — dimension temporelle (année, mois, jour, semaine, etc.)
- `dim_pays` — localisations des clients (ville, pays)
- `dim_categorie` — catégories de produits
- `dim_produit` — produits actifs
- `fact_sales` — table de faits (1 ligne = 1 commande)

---

## 🛠️ Développement

### Arrêter les services

```bash
# Arrêter les conteneurs
docker-compose down

# Arrêter et supprimer les volumes (⚠️ perd les données)
docker-compose down -v
```

### Voir les logs

```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f [orders_web|customers_web|catalog_web|...]
```

### Faire une migration Django

```bash
docker exec -it <nom_du_container> python manage.py makemigrations
docker exec -it <nom_du_container> python manage.py migrate
```

---

## ⚠️ Notes importantes

- **CORS** est activé en mode `ALLOW_ALL_ORIGINS` (développement uniquement).
- **DEBUG** est à `True` sur tous les services Django.
- Le dossier `customers-sercice` contient une faute de frappe historique (`sercice` au lieu de `service`). Ne pas renommer sans adapter le `docker-compose.yml`.
- Le frontend utilise un **proxy Vite** pour rediriger les appels `/api/*` vers les bons services backend.

---

## 📚 Contexte

Projet réalisé dans le cadre d'un **TP d'Architecture Logicielle** (M1).

Objectifs pédagogiques :
- Architecture en microservices
- Communication inter-services (HTTP/REST)
- Conteneurisation avec Docker Compose
- Base de données analytique et ETL (schéma en étoile)
- Visualisation de données avec Superset
