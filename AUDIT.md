# Audit — Conformité au TP Data Warehouse & BI

> Date : 2026-05-04
> Basé sur la consigne : `CONSIGNE_PROF_PRIO.md`

---

## 📊 Bilan global

| # | Étape | Consigne | Actuel | Statut |
|---|-------|----------|--------|--------|
| 1 | **Compréhension sources** | Identifier données des 3 microservices | Microservices fonctionnels (catalog, customers, orders) | ✅ |
| 2 | **Besoins BI** | 13 indicateurs minimum (CA, panier moyen, top produits...) | Aucun dashboard complet, juste 1 chart "ventes par pays" | ❌ |
| 3 | **Modèle DW** | `fact_order_lines` (1 ligne = 1 ligne de commande) | `fact_order_lines` créée et alimentée (**152 317 lignes**) | ✅ |
| 3b | **Dimensions** | `dim_customer`, `dim_product`, `dim_category`, `dim_date` | `dim_customer` (10k), `dim_product` (94k), `dim_category` (50), `dim_date` (2316 jours) | ✅ |
| 4 | **Base BI** | Nouvelle base PostgreSQL dédiée | `bi_db` existe avec Docker | ✅ |
| 5 | **ETL Python** | Extraire, transformer, charger | `etl_sales.py` réécrit et fonctionnel (extraction SQL directe) | ✅ |
| 6 | **Superset** | Connecté au DW, datasets déclarés | Superset installé, connexion OK, vues SQL créées | ⚠️ |
| 7 | **Dashboards** | 4 dashboards (Global, Produits, Clients, Géo) | Aucun dashboard complet | ❌ |
| 8 | **Analyse archi** | Questions sur OLTP vs OLAP, choix... | Pas documenté | ❌ |
| 9 | **Livrables** | ETL, SQL DW, schéma, dashboards, README | ETL ✅, SQL DW ❌, schéma ❌, dashboards ❌, README ✅ | ⚠️ |

---

## ✅ Ce qui est bien fait

- **Architecture globale** : 3 microservices + BI DB + Superset + ETL
- **ETL fonctionnel** : script Python qui tourne, connexions aux 4 BDs, idempotent (`ON CONFLICT`)
- **Table de faits conforme** : `fact_order_lines` au grain "1 ligne = 1 ligne de commande" (152 317 lignes)
- **Dimensions complètes** :
  - `dim_customer` : 10 000 clients avec pays/ville
  - `dim_product` : 94 990 produits avec `category_name` dénormalisé
  - `dim_category` : 50 catégories
  - `dim_date` : 2 316 jours (2020 → 2026)
- **Superset installé** et accessible
- **Vues SQL** pour Superset créées et à jour (`vw_fact_order_lines_complete`, `vw_sales_by_country`, etc.)
- **Types SQL corrects** : `DECIMAL(10,2)` utilisé (pas de `float`)
- **Migration orders-service** : `0003_orderline_quantity.py` ajoute le champ `quantity` nécessaire au grain ligne de commande

---

## ❌ Ce qui manque complètement

### 🔴 1. Les 4 dashboards sont vides

| Dashboard | Statut |
|-----------|--------|
| Vue globale (CA total, panier moyen, évolution...) | ❌ |
| Analyse produits (Top 10, CA par catégorie...) | ❌ |
| Analyse clients (Top clients, panier moyen par client...) | ❌ |
| Analyse géographique (CA par pays, top produits par pays...) | ⚠️ 1 chart seul |

### 🔴 2. Livrables manquants

| Livrable | Statut |
|----------|--------|
| Script SQL de création du DW (`dw_schema.sql`) | ❌ |
| Schéma du modèle décisionnel | ❌ |
| Analyse architecturale (OLTP vs OLAP, choix...) | ❌ |

---

## ⚠️ Ce qui doit être adapté / complété

### 1. Superset : créer les datasets et dashboards

Les **vues SQL** existent mais les **datasets Superset** et les **dashboards** doivent encore être créés manuellement dans l'interface.

### 2. ETL : documentation des choix

**Consigne** : Pourquoi SQL plutôt que API ? Comment gérer les données manquantes ?

**Actuel** : Rien n'est documenté. Le README parle de l'architecture mais pas des choix ETL.

### 3. README à mettre à jour

Le README doit refléter le nouveau modèle en étoile (`fact_order_lines`, `dim_customer`, etc.) et non plus l'ancien modèle (`fact_sales`, `dim_pays`).

---

## 🎯 Priorité d'actions restantes

| Priorité | Action | Complexité |
|----------|--------|------------|
| **P1** | **Créer les 4 dashboards** dans Superset | 🟡 Moyenne |
| **P1** | **Mettre à jour le README** avec le nouveau modèle | 🟢 Facile |
| **P2** | **Créer un script SQL `dw_schema.sql`** séparé | 🟢 Facile |
| **P2** | **Ajouter un schéma du modèle** (Mermaid) dans le README | 🟢 Facile |
| **P2** | **Documenter les choix** (SQL vs API, gestion du pays, etc.) | 🟢 Facile |

---

## 📝 Journal / Évolution

### 2026-05-04 — P0 terminée

- ✅ Ajout du champ `quantity` sur `OrderLine` (migration `0003`)
- ✅ Refonte complète de l'ETL : `fact_sales` → `fact_order_lines`
- ✅ Création de `dim_customer`
- ✅ `dim_product` avec `category_name` dénormalisé
- ✅ `dim_date` simplifiée conforme à la consigne
- ✅ Mise à jour des vues SQL Superset
- ✅ 152 317 lignes de commande chargées dans la BI

### Avant 2026-05-04 — État initial

- `fact_sales` au grain "1 commande" (non conforme)
- Pas de `dim_customer`
- `dim_pays` séparé (non demandé par la consigne prof)
- `dim_produit` sans `category_name`
- 1 seul chart Superset créé
