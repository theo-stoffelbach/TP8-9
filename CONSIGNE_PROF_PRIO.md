# TP — Data Warehouse & BI : Mini Zalando

---

## 1. Contexte

Vous avez développé un mini SI e-commerce composé de 3 microservices :

- **`catalog-service`** : produits, catégories, prix, stock
- **`customer-service`** : clients, adresses
- **`order-service`** : commandes, lignes de commande, total, statut

Ce SI est orienté **opérationnel / transactionnel** (OLTP).

Aujourd'hui, vous allez construire une architecture **Data Warehouse + BI** (OLAP).

---

## 2. Objectif du TP

Mettre en place la chaîne suivante :

```
Microservices Mini Zalando
        ↓
    ETL Python
        ↓
Data Warehouse PostgreSQL
        ↓
   Apache Superset
        ↓
    Dashboards BI
```

L'objectif est de permettre à une direction métier de suivre les ventes, les clients, les produits et les performances commerciales par pays.

---

## 3. Étape 1 — Comprendre les données sources

À partir de vos 3 microservices, identifiez les données disponibles.

### Questions

- Quelles données sont portées par `catalog-service` ?
- Quelles données sont portées par `customer-service` ?
- Quelles données sont portées par `order-service` ?
- Où trouve-t-on le prix d'un produit ?
- Où trouve-t-on le pays d'un client ?
- Où trouve-t-on le montant total d'une commande ?
- Pourquoi aucune base de données seule ne permet de répondre à toutes les questions BI ?

---

## 4. Étape 2 — Définir les besoins BI

Vous devez proposer des indicateurs utiles pour piloter l'activité commerciale.

### Indicateurs minimum attendus

| Indicateur | Description |
|------------|-------------|
| **CA total** | Somme de toutes les ventes |
| **Nombre total de commandes** | Volume de commandes |
| **Panier moyen** | CA total / Nombre de commandes |
| **Nombre de produits vendus** | Quantité totale vendue |
| **Top produits vendus** | Produits les plus rentables |
| **CA par catégorie** | Performance par segment |
| **CA par client** | Meilleurs clients |
| **CA par pays** | Performance géographique |
| **Nombre de commandes par pays** | Volume par marché |
| **Panier moyen par pays** | Comportement d'achat par pays |
| **Top produits par pays** | Préférences locales |
| **Répartition du CA par pays** | Parts de marché |
| **Évolution du CA dans le temps** | Tendance |

### Questions

- Quels indicateurs intéressent une direction commerciale ?
- Quels indicateurs intéressent une équipe marketing ?
- Quels indicateurs intéressent une équipe logistique ?
- Quels champs sont nécessaires pour calculer le chiffre d'affaires par pays ?
- Le pays doit-il venir du client ou de l'adresse de livraison ?
- Que faire si un client possède plusieurs adresses ?
- Quelle différence entre "pays du client" et "pays de livraison" ?
- Quels indicateurs peuvent être calculés uniquement avec `order-service` ?
- Quels indicateurs nécessitent de croiser plusieurs microservices ?

---

## 5. Étape 3 — Modéliser le Data Warehouse

Vous devez proposer un modèle décisionnel permettant d'analyser les ventes.

### Modèle attendu

Un **modèle en étoile**.

#### Table de faits : `fact_order_lines`

> **Grain** : une ligne = une ligne de commande.

| Champ | Description |
|-------|-------------|
| `order_id` | Identifiant de la commande |
| `order_line_id` | Identifiant de la ligne |
| `customer_id` | Identifiant du client |
| `product_id` | Identifiant du produit |
| `category_id` | Identifiant de la catégorie |
| `date_id` | Clé vers la dimension date |
| `country` | Pays de livraison / client |
| `quantity` | Quantité commandée |
| `unit_price` | Prix unitaire au moment de la commande |
| `line_total` | Total de la ligne (`quantity × unit_price`) |
| `order_status` | Statut de la commande |

#### Dimensions attendues

**`dim_customer`**
- `customer_id`
- `first_name`
- `last_name`
- `email`
- `phone`
- `is_active`
- `country`
- `city`

**`dim_product`**
- `product_id`
- `product_name`
- `slug`
- `category_id`
- `category_name`
- `is_active`

**`dim_category`**
- `category_id`
- `category_name`
- `category_slug`

**`dim_date`**
- `date_id`
- `date`
- `day`
- `month`
- `month_name`
- `quarter`
- `year`

### Questions

- Pourquoi choisir une table de faits basée sur les **lignes de commande** ?
- Pourquoi ne pas faire une table de faits avec une ligne par commande uniquement ?
- Quelle dimension permet l'analyse par pays ?
- Où stocker le pays : dans `dim_customer`, dans une dimension adresse, ou directement dans la table de faits ?
- Pourquoi peut-il être utile de copier le pays dans la table de faits ?
- Pourquoi le modèle décisionnel est-il volontairement différent du modèle transactionnel ?
- Pourquoi Superset sera plus à l'aise avec ce modèle qu'avec les tables microservices brutes ?

---

## 6. Étape 4 — Créer le Data Warehouse PostgreSQL

Vous devez créer une **nouvelle base PostgreSQL** dédiée à l'analyse.

### Travail demandé

Créer les tables :
- `fact_order_lines`
- `dim_customer`
- `dim_product`
- `dim_category`
- `dim_date`

### Questions

- Pourquoi créer une base PostgreSQL séparée ?
- Pourquoi ne pas connecter Superset directement aux bases des microservices ?
- Quels types SQL choisir pour les montants ?
- Pourquoi éviter les montants en `float` ?
- Quelles clés primaires et étrangères peut-on définir ?
- Faut-il imposer toutes les contraintes dans le Data Warehouse ou garder une certaine souplesse ?

---

## 7. Étape 5 — Coder les pipelines ETL en Python

Vous devez développer un ou plusieurs scripts Python permettant d'alimenter le Data Warehouse.

### Extraction

Les données peuvent être extraites :
- soit depuis les **APIs REST** des microservices ;
- soit directement depuis les **bases PostgreSQL** des microservices.

### Transformation

Le pipeline doit :
- récupérer les commandes ;
- récupérer les lignes de commande ;
- récupérer les produits associés ;
- récupérer les catégories ;
- récupérer les clients ;
- récupérer les adresses ;
- déterminer le pays utilisé pour l'analyse ;
- calculer ou vérifier les montants ;
- préparer les dimensions ;
- préparer la table de faits.

### Chargement

Le pipeline doit charger les données dans PostgreSQL Data Warehouse.

### Questions

- Quelle méthode d'extraction avez-vous choisie : API ou base SQL ? Pourquoi ?
- Quels sont les avantages d'une extraction par API ?
- Quels sont les avantages d'une extraction directe en base ?
- Quels sont les risques de chaque approche ?
- Comment gérez-vous les données manquantes ?
- Que faites-vous si un produit commandé n'existe plus dans le catalogue ?
- Que faites-vous si un client n'a pas d'adresse ?
- Comment choisissez-vous le pays lorsqu'un client possède plusieurs adresses ?
- Comment vérifiez-vous que le total de ligne est correct ?
- Comment rendez-vous votre script rejouable sans dupliquer les données ?

---

## 8. Étape 6 — Connecter Apache Superset

Vous devez connecter Apache Superset au Data Warehouse PostgreSQL.

### Travail demandé

- Ajouter la connexion PostgreSQL dans Superset
- Déclarer les datasets nécessaires
- Créer les graphiques
- Construire un ou plusieurs dashboards

---

## 9. Étape 7 — Créer les dashboards BI

### Dashboard 1 — Vue globale

Graphiques attendus :
- CA total
- Nombre de commandes
- Nombre de produits vendus
- Panier moyen
- Évolution du CA dans le temps

### Dashboard 2 — Analyse produits

Graphiques attendus :
- Top 10 produits par chiffre d'affaires
- Top 10 produits par quantité vendue
- CA par catégorie
- Quantité vendue par catégorie

### Dashboard 3 — Analyse clients

Graphiques attendus :
- Top clients par chiffre d'affaires
- Nombre de commandes par client
- Panier moyen par client

### Dashboard 4 — Analyse géographique

Graphiques attendus :
- Chiffre d'affaires par pays
- Nombre de commandes par pays
- Panier moyen par pays
- Quantité de produits vendus par pays
- Top produits par pays
- Répartition du CA par pays

### Questions BI par pays

- Quel pays génère le plus de chiffre d'affaires ?
- Quel pays génère le plus grand nombre de commandes ?
- Le pays avec le plus de commandes est-il aussi celui avec le plus gros panier moyen ?
- Quels produits se vendent le mieux selon les pays ?
- Certaines catégories performent-elles mieux dans certains pays ?
- Y a-t-il des pays avec beaucoup de commandes mais un faible chiffre d'affaires ?
- Y a-t-il des pays avec peu de commandes mais un panier moyen élevé ?
- Comment expliquer les différences de performance entre pays ?

---

## 10. Analyse architecturale finale

### Questions

- Pourquoi séparer le SI opérationnel du SI décisionnel ?
- Pourquoi le Data Warehouse est-il une meilleure source pour Superset ?
- Pourquoi les microservices ne sont-ils pas adaptés aux requêtes analytiques ?
- Quelle est la différence entre une base OLTP et une base OLAP ?
- Quels problèmes avez-vous rencontrés lors du croisement des données ?
- Quelles incohérences avez-vous détectées ?
- Quelle donnée a été la plus difficile à intégrer ?
- Que faudrait-il améliorer pour passer à une architecture data plus industrielle ?

---

## 11. Livrables attendus

Chaque trinôme doit rendre :

- le code Python des pipelines ETL ;
- le script SQL de création du Data Warehouse ;
- un schéma du modèle décisionnel ;
- les dashboards Superset ;
- un README expliquant :
  - l'architecture globale ;
  - les sources de données ;
  - le modèle Data Warehouse ;
  - les choix de transformation ;
  - les indicateurs BI ;
  - les limites de la solution.

---

## 12. Critères d'évaluation

Vous serez évalués sur :

- la compréhension des données sources ;
- la qualité du modèle Data Warehouse ;
- la clarté du pipeline ETL ;
- la cohérence des transformations ;
- la capacité à croiser produits, clients, commandes et pays ;
- la pertinence des dashboards Superset ;
- la qualité de l'analyse architecturale finale.
