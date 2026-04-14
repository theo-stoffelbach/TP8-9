# Catalog Service

Microservice de gestion du catalogue produit pour le projet Mini Zalando.

## Port

**8001**

## Lancement

```bash
docker compose up --build
```

Le service est accessible sur `http://localhost:8001`.

## Endpoints

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/api/categories/` | Liste des catégories |
| GET | `/api/categories/<id>/` | Détail d'une catégorie |
| GET | `/api/products/` | Liste des produits |
| GET | `/api/products/<id>/` | Détail d'un produit |

### Filtres (bonus)

| Paramètre | Exemple | Description |
|-----------|---------|-------------|
| `category` | `/api/products/?category=1` | Filtrer par catégorie |
| `is_active` | `/api/products/?is_active=true` | Produits actifs uniquement |
| `search` | `/api/products/?search=nike` | Recherche par nom |

## Données de test

3 catégories et 8 produits sont chargés automatiquement au démarrage.

## Stack technique

- Python 3.11
- Django 4.2
- Django REST Framework
- PostgreSQL 15
- Docker
