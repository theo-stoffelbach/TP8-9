# Audit — Conformité au TP Data Warehouse & BI

> Date : 2026-05-04
> Basé sur la consigne : `CONSIGNE_PROF_PRIO.md`

---

## 📊 Bilan global

| # | Étape | Consigne | Actuel | Statut |
|---|-------|----------|--------|--------|
| 1 | **Compréhension sources** | Identifier données des 3 microservices | Microservices fonctionnels (catalog, customers, orders) | ✅ |
| 2 | **Besoins BI** | 13 indicateurs minimum (CA, panier moyen, top produits...) | Aucun dashboard complet, juste 1 chart "ventes par pays" | ❌ |
| 3 | **Modèle DW** | `fact_order_lines` (1 ligne = 1 ligne de commande) | `fact_sales` (1 ligne = 1 commande, avec le produit le plus cher) | ❌ **Écart majeur** |
| 3b | **Dimensions** | `dim_customer`, `dim_product`, `dim_category`, `dim_date` | `dim_pays`, `dim_produit`, `dim_categorie`, `dim_date`. **Pas de `dim_customer`** | ⚠️ |
| 4 | **Base BI** | Nouvelle base PostgreSQL dédiée | `bi_db` existe avec Docker | ✅ |
| 5 | **ETL Python** | Extraire, transformer, charger | `etl_sales.py` existe, extraction SQL directe | ⚠️ |
| 6 | **Superset** | Connecté au DW, datasets déclarés | Superset installé, 1 dataset créé, connexion OK | ⚠️ |
| 7 | **Dashboards** | 4 dashboards (Global, Produits, Clients, Géo) | Aucun dashboard complet | ❌ |
| 8 | **Analyse archi** | Questions sur OLTP vs OLAP, choix... | Pas documenté | ❌ |
| 9 | **Livrables** | ETL, SQL DW, schéma, dashboards, README | ETL ✅, SQL DW ❌, schéma ❌, dashboards ❌, README ✅ | ⚠️ |

---

## ✅ Ce qui est bien fait

- **Architecture globale** : 3 microservices + BI DB + Superset + ETL
- **ETL fonctionnel** : script Python qui tourne, connexions aux 4 BDs, idempotent (`ON CONFLICT`)
- **Dimensions de base** : `dim_date`, `dim_pays`, `dim_categorie`, `dim_produit` existent et sont alimentées
- **Superset installé** et accessible
- **Vues SQL** pour Superset créées (`vw_fact_sales_complete`, etc.)
- **Types SQL corrects** : `DECIMAL(10,2)` utilisé (pas de `float`)

---

## ❌ Ce qui est FAUX / manque complètement

### 🔴 1. La table de faits (écart majeur)

**Consigne** : `fact_order_lines` → **1 ligne = 1 ligne de commande**

```
order_id | order_line_id | product_id | quantity | unit_price | line_total | ...
```

**Actuel** : `fact_sales` → **1 ligne = 1 commande entière**

```
order_id | order_total | nb_order_lines | produit_id (le plus cher) | ...
```

**Problème** : Le prof demande explicitement le grain "ligne de commande" pour pouvoir analyser :
- Quels produits se vendent (par quantité)
- CA par produit
- Top 10 produits par quantité vendue
- Quantité vendue par catégorie
- etc.

Avec le modèle actuel, **impossible** de calculer la quantité vendue par produit (pas de colonne `quantity`).

---

### 🔴 2. Pas de dimension `dim_customer`

**Consigne** : `dim_customer` avec `customer_id`, `first_name`, `last_name`, `email`, `phone`, `is_active`, `country`, `city`

**Actuel** : Le client n'existe que comme `customer_id` dans `fact_sales`. Pas de dimension dédiée.

**Problème** : Impossible de faire les dashboards "Analyse clients" (top clients par CA, panier moyen par client...).

---

### 🔴 3. Les 4 dashboards sont vides

| Dashboard | Statut |
|-----------|--------|
| Vue globale (CA total, panier moyen, évolution...) | ❌ |
| Analyse produits (Top 10, CA par catégorie...) | ❌ |
| Analyse clients (Top clients, panier moyen par client...) | ❌ |
| Analyse géographique (CA par pays, top produits par pays...) | ⚠️ 1 chart seul |

---

## ⚠️ Ce qui doit être adapté

### 1. `dim_product` manque `category_name`

**Consigne** : `dim_product` doit avoir `category_name` (dénormalisé)

**Actuel** : `dim_produit` n'a que `categorie_id` (clé étrangère vers `dim_categorie`)

**Impact** : Acceptable si les vues SQL font le JOIN, mais le prof demande explicitement cette dénormalisation.

---

### 2. Le pays dans `dim_customer`

**Consigne** : Le pays doit être dans `dim_customer` (ou au moins géré proprement)

**Actuel** : Le pays est dans `dim_pays` (table séparée). L'ETL prend l'adresse par défaut du client, sinon la première.

**Impact** : Le choix actuel est acceptable en modèle en étoile, mais le prof demande une réflexion sur ce choix.

---

### 3. ETL : pas de documentation des choix

**Consigne** : Pourquoi SQL plutôt que API ? Comment gérer les données manquantes ?

**Actuel** : Rien n'est documenté. Le README parle de l'architecture mais pas des choix ETL.

---

### 4. Script SQL de création du DW

**Consigne** : Livrer un script SQL de création du Data Warehouse

**Actuel** : Le DDL est inline dans `etl_sales.py`. `analytics/bi_views.sql` existe mais c'est pour les vues, pas pour les tables du DW.

---

## 🎯 Priorité d'actions

| Priorité | Action | Complexité |
|----------|--------|------------|
| **P0** | **Refondre `fact_sales` en `fact_order_lines`** (grain = 1 ligne de commande) | 🔴 Élevée |
| **P0** | **Créer `dim_customer`** | 🟡 Moyenne |
| **P1** | **Adapter l'ETL** pour alimenter les nouvelles tables | 🟡 Moyenne |
| **P1** | **Créer les 4 dashboards** dans Superset | 🟡 Moyenne |
| **P2** | **Créer un script SQL `dw_schema.sql`** séparé | 🟢 Facile |
| **P2** | **Ajouter un schéma du modèle** (image ou Mermaid) dans le README | 🟢 Facile |
| **P2** | **Documenter les choix** (SQL vs API, gestion du pays, etc.) | 🟢 Facile |
