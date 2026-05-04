# TP — Data Warehouse & BI : Mini Zalando

> Réponses structurées par étape. Les questions nécessitant Apache Superset sont marquées `[TODO]`.

---

## Contexte du projet

L'application e-commerce **Zalandouille** repose sur trois microservices Django indépendants, chacun avec sa propre base PostgreSQL :

- **`catalog-service`** (port 8001) : référentiel produits et catégories.
- **`customers-sercice`** (port 8000) : gestion des clients et de leurs adresses.
- **`orders-service`** (port 8002) : gestion des commandes et de leurs lignes.

La base de données décisionnelle (BI) repose sur un **schéma en étoile** contenant les dimensions `dim_date`, `dim_pays`, `dim_categorie`, `dim_produit` et la table de faits `fact_sales` (grain : 1 commande). L'alimentation est assurée par le script `etl/etl_sales.py` via des connexions `psycopg2` directes.

---

## Étape 1 — Comprendre les données sources

### 1. Quelles données sont portées par catalog-service ?

Le `catalog-service` porte le référentiel marchand : les catégories (`catalog_category`) et les produits (`catalog_product`) avec leurs attributs nom, slug, description, prix, stock et statut actif. Il expose une API en lecture seule utilisée notamment par le `orders-service` pour récupérer le prix des produits lors de la création d'une commande.

### 2. Quelles données sont portées par customer-service ?

Le `customers-sercice` porte les données clients et leurs adresses de livraison. La table `catalog_customer` contient l'identité du client (prénom, nom, email, téléphone), tandis que la table `catalog_address` stocke les adresses postales (rue, code postal, ville, pays, indicateur `is_default`).

### 3. Quelles données sont portées par order-service ?

Le `orders-service` porte les données transactionnelles de vente. La table `orders_order` représente l'en-tête de commande (identifiant client, statut, montant total, date de création), et la table `orders_orderline` représente les lignes de commande, c'est-à-dire les produits inclus dans chaque commande.

### 4. Où trouve-t-on le prix d’un produit ?

Le prix d'un produit se trouve dans le `catalog-service`, dans la table `catalog_product` (champ `price`). Le `orders-service` ne stocke pas le prix localement dans ses lignes de commande : il effectue un appel HTTP temps réel vers le `catalog-service` au moment de la création pour calculer le montant total.

### 5. Où trouve-t-on le pays d’un client ?

Le pays d'un client se trouve dans le `customers-sercice`, dans la table `catalog_address` (champ `country`). Ce pays est associé au client via une clé étrangère ; le script ETL utilise l'adresse par défaut (`is_default = TRUE`) pour déterminer le pays d'un client, ou à défaut sa première adresse connue.

### 6. Où trouve-t-on le montant total d’une commande ?

Le montant total d'une commande se trouve dans le `orders-service`, dans la table `orders_order` (champ `total_amount`). Ce montant est calculé à la volée lors de la création de la commande en sommant les prix des produits obtenus depuis le `catalog-service`, puis stocké dans l'en-tête de la commande.

### 7. Pourquoi aucune base de données seule ne permet de répondre à toutes les questions BI ?

Chaque microservice possède sa propre base PostgreSQL isolée ; les données sont donc physiquement réparties. Une question BI comme "le chiffre d'affaires par pays et par catégorie de produit" nécessite de croiser le prix et la catégorie (catalog), le pays du client (customers) et le montant de la commande (orders), ce qu'aucune base seule ne peut fournir.

---

## Étape 2 — Définir les besoins BI

### 1. Quels indicateurs intéressent une direction commerciale ?

La direction commerciale s'intéresse au chiffre d'affaires global, au chiffre d'affaires par pays, par catégorie et par produit, ainsi qu'au panier moyen et à l'évolution temporelle des ventes (tendance mensuelle, trimestrielle, annuelle). Elle suivra également le taux de commandes annulées par rapport aux commandes confirmées.

### 2. Quels indicateurs intéressent une équipe marketing ?

L'équipe marketing cherchera à analyser le panier moyen, la fréquence d'achat par client, les produits et catégories les plus vendus, et la répartition géographique des clients pour cibler les campagnes. La saisonnalité des ventes (pics par mois, week-end, etc.) via `dim_date` est également un levier stratégique.

### 3. Quels indicateurs intéressent une équipe logistique ?

L'équipe logistique s'intéresse au volume de commandes par zone géographique (pays, ville), au nombre de lignes par commande (indicateur de complexité de préparation) et à la répartition des adresses de livraison. Ces indicateurs permettent d'anticiper les besoins en stock et en transport par région.

### 4. Quels champs sont nécessaires pour calculer le chiffre d’affaires par pays ?

Pour calculer le chiffre d'affaires par pays, il est nécessaire de disposer du montant total de la commande (`order_total` ou `total_amount` depuis `orders`), de l'identifiant du client pour faire le lien vers son adresse, et du pays issu de la dimension `dim_pays` (alimentée par `catalog_address`).

### 5. Le pays doit-il venir du client ou de l’adresse de livraison ?

Cela dépend du besoin analytique : pour une analyse de marché et de clientèle, le "pays du client" (résidence) est pertinent ; pour une analyse logistique, le "pays de livraison" (destination de la commande) est plus adapté. Dans le cadre de ce TP, le pays utilisé est celui de l'adresse du client telle qu'elle est stockée dans `customers-sercice`.

### 6. Que faire si un client possède plusieurs adresses ?

Il convient de définir une règle de gestion unique pour garantir la cohérence analytique. Le projet actuel adopte la règle suivante : utiliser l'adresse marquée `is_default = TRUE`, et à défaut la première adresse trouvée. Cela évite de compter un client dans plusieurs pays simultanément lors d'une analyse agrégée.

### 7. Quelle différence entre “pays du client” et “pays de livraison” ?

Le "pays du client" est une caractéristique démographique et marketing qui indique où le client réside habituellement. Le "pays de livraison" est une information opérationnelle indiquant où une commande spécifique a été envoyée ; les deux peuvent différer (expatriation, envoi de cadeaux, déménagement non encore reflété dans le profil).

### 8. Quels indicateurs peuvent être calculés uniquement avec order-service ?

On peut calculer le nombre total de commandes, le nombre moyen de lignes par commande, le montant total des ventes (si l'on considère le champ `total_amount` comme source de vérité locale) et la répartition des statuts de commande (confirmé, annulé). Ces indicateurs sont purement transactionnels et ne nécessitent pas de données externes.

### 9. Quels indicateurs nécessitent de croiser plusieurs microservices ?

Tout indicateur impliquant à la fois la vente et les attributs des produits ou des clients nécessite un croisement. Par exemple : le chiffre d'affaires par catégorie de produit (orders + catalog), le chiffre d'affaires par pays du client (orders + customers), ou l'analyse des produits les plus vendus avec leur nom et prix réel (orders + catalog).

---

## Étape 3 — Modéliser le Data Warehouse

### 1. Pourquoi choisir une table de faits basée sur les lignes de commande ?

Idéalement, une table de faits au grain "ligne de commande" permet d'analyser chaque produit vendu individuellement, d'attribuer précisément une catégorie et un prix à chaque ligne sans approximation, et de calculer des indicateurs fins (quantité, remise, marge par référence). C'est le grain recommandé dans la théorie du sujet car il préserve la richesse des données transactionnelles. Dans le projet actuel, ce grain n'a pas été retenu par simplification.

### 2. Pourquoi ne pas faire une table de faits avec une ligne par commande uniquement ?

Le projet actuel utilise précisément ce grain simplifié (1 ligne = 1 commande) pour faciliter l'analyse globale par pays et par date. Cependant, cette approche pose une limite dès qu'une commande contient des produits de catégories différentes : il devient impossible d'attribuer une seule catégorie ou un seul produit représentatif à la commande sans arbitrage (d'où la stratégie actuelle du "produit le plus cher"). On perd ainsi la capacité à analyser finement le panier.

### 3. Quelle dimension permet l’analyse par pays ?

C'est la dimension **`dim_pays`** qui permet l'analyse par pays. Elle est alimentée à partir des couples (ville, pays) extraits de la table `catalog_address` du `customers-sercice`, et est reliée à la table de faits via une clé étrangère (`pays_id`).

### 4. Où stocker le pays : dans dim_customer, dans une dimension adresse, ou directement dans la table de faits ?

Dans le modèle actuel, le pays est stocké dans **`dim_pays`** et référencé dans la table de faits. Une alternative serait d'intégrer le pays dans une dimension `dim_customer` ou `dim_adresse` pour suivre l'historicité du client. Stocker le pays directement dans la table de faits sous forme de clé étrangère vers `dim_pays` est également une pratique courante qui optimise les requêtes analytiques.

### 5. Pourquoi peut-il être utile de copier le pays dans la table de faits ?

Copier le pays (via une clé étrangère `pays_id`) dans la table de faits permet d'éviter de traverser plusieurs niveaux de jointure (client → adresse) à chaque requête analytique, ce qui améliore significativement les performances. Cela permet également de figer le contexte géographique au moment de la transaction : si un client déménage ultérieurement, la commande historique conserve le pays d'origine, garantissant la cohérence temporelle des indicateurs.

### 6. Pourquoi le modèle décisionnel est-il volontairement différent du modèle transactionnel ?

Le modèle transactionnel est normalisé (3NF) pour minimiser la redondance, garantir l'intégrité référentielle et optimiser les écritures. Le modèle décisionnel, en revanche, est volontairement dénormalisé (schéma en étoile) pour privilégier la rapidité des lectures analytiques, simplifier les requêtes métier et agréger efficacement des données issues de plusieurs sources hétérogènes.

### 7. Pourquoi Superset sera plus à l’aise avec ce modèle qu’avec les tables microservices brutes ?

Superset est un outil de visualisation conçu pour interroger des schémas relationnels dénormalisés via SQL. Le modèle en étoile centralisé dans la base BI lui offre un seul point de connexion avec des jointures simples et prévisibles (faits → dimensions). Interroger directement les tables microservices brutes impliquerait des requêtes complexes, potentiellement cross-database, qui ne sont pas supportées nativement et qui seraient peu performantes pour de l'exploration visuelle interactive.

---

## Étape 4 — Créer le Data Warehouse PostgreSQL

### 1. Pourquoi créer une base PostgreSQL séparée ?

Cela permet d'**isoler la charge analytique** (requêtes d'agrégation lourdes, rapports) de la charge transactionnelle des microservices (OLTP). On évite ainsi de ralentir les applications métier et on peut structurer un schéma dénormalisé optimisé pour la BI (schéma en étoile).

### 2. Pourquoi ne pas connecter Superset directement aux bases des microservices ?

Les bases opérationnelles sont **normalisées et réparties** entre plusieurs services, ce qui rend les requêtes BI complexes et lentes. De plus, connecter un outil de reporting directement aux bases métier viole le principe de séparation des responsabilités et peut impacter la disponibilité des services.

### 3. Quels types SQL choisir pour les montants ?

On utilise **`DECIMAL(10,2)`** (ou `NUMERIC`), comme défini dans le DDL pour `order_total` et `price`. Ce type garantit une précision exacte sur les deux décimales, ce qui est indispensable pour les données financières.

### 4. Pourquoi éviter les montants en float ?

Les types flottants (`REAL`, `DOUBLE PRECISION`) stockent les valeurs de manière **approximative**, ce qui peut provoquer des erreurs d'arrondi (ex. : `10.20` devenant `10.1999999`). En comptabilité et en BI, la précision monétaire doit être stricte.

### 5. Quelles clés primaires et étrangères peut-on définir ?

- **Clés primaires** : `dim_date(date_id)`, `dim_pays(pays_id)`, `dim_categorie(categorie_id)`, `dim_produit(produit_id)`, et `fact_sales(id)`.
- **Contrainte d'unicité** : `UNIQUE(order_id)` sur `fact_sales` pour éviter les doublons de commandes.
- **Clés étrangères** : depuis `fact_sales` vers les dimensions (`date_id`, `pays_id`, `produit_id`, `categorie_id`).

### 6. Faut-il imposer toutes les contraintes dans le Data Warehouse ou garder une certaine souplesse ?

Il faut **garder une souplesse partielle**. Les clés primaires et les contraintes d'unicité sont utiles pour garantir l'intégrité, mais les clés étrangères peuvent être relâchées ou gérées avec `ON DELETE SET NULL`. Le DWH peut contenir des données historiques avec des références à des dimensions qui n'existent plus (produits supprimés, etc.).

---

## Étape 5 — Coder les pipelines ETL en Python

### 1. Quelle méthode d’extraction avez-vous choisie : API ou base SQL ? Pourquoi ?

Nous avons choisi l'**extraction directe en base SQL via `psycopg2`**. Cette approche est plus performante pour traiter de gros volumes de données en batch et permet d'utiliser directement le langage SQL pour les agrégations et les jointures côté source (ex. : `COUNT`, `ARRAY_AGG`).

### 2. Quels sont les avantages d’une extraction par API ?

L'API garantit la **cohérence des données** via un contrat formalisé, renforce la sécurité en évitant l'accès direct à la base, et rend l'ETL indépendant de la technologie de persistance sous-jacente. Elle expose aussi une logique métier centralisée.

### 3. Quels sont les avantages d’une extraction directe en base ?

L'accès SQL direct offre une **meilleure performance** pour les extractions massives (bulk extract), la possibilité d'utiliser des fonctions SQL avancées (window functions, agrégations), et une simplicité de mise en œuvre pour des traitements batch internes sans dépendre de la disponibilité des endpoints REST.

### 4. Quels sont les risques de chaque approche ?

- **SQL direct** : risque de verrouillage sur les tables sources, exposition du schéma physique interne, et forte dépendance au schéma de la base (toute migration métier casse l'ETL).
- **API** : surcharge potentielle du service métier, latence plus élevée, gestion complexe de la pagination, et limitations liées au *rate limiting*.

### 5. Comment gérez-vous les données manquantes ?

On utilise **`COALESCE(..., 'Inconnu')`** pour les champs d'adresse manquants dans `extract_customers`, et on vérifie l'existence du client (`if not customer`) avant d'insérer une commande dans `load_fact_sales`. Cela évite les erreurs d'insertion et marque explicitement les données incomplètes.

### 6. Que faites-vous si un produit commandé n’existe plus dans le catalogue ?

La fonction `extract_main_product` retourne `None` si le `product_id` n'est pas présent dans le dictionnaire `catalog_products`. Par conséquent, les champs **`produit_id` et `categorie_id` sont insérés à `NULL`** dans `fact_sales`, ce qui préserve la commande sans forcer une référence erronée.

### 7. Que faites-vous si un client n’a pas d’adresse ?

Les sous-requêtes dans `extract_customers` utilisent `COALESCE` pour retourner la valeur **`'Inconnu'`** pour les colonnes `city` et `country` lorsqu'aucune adresse n'existe. Ce pays est alors mappé sur la dimension "Inconnu / Inconnu" dans `dim_pays`.

### 8. Comment choisissez-vous le pays lorsqu’un client possède plusieurs adresses ?

On applique une règle déterministe : on privilégie l'adresse marquée **`is_default = TRUE`**. Si aucune adresse par défaut n'existe, on sélectionne la **première adresse trouvée** (`LIMIT 1`). Cela garantit un résultat stable et cohérent avec la logique métier.

### 9. Comment vérifiez-vous que le total de ligne est correct ?

Dans l'ETL actuel, le modèle étant au **grain commande**, nous ne recalculons pas le total ligne par ligne. Nous utilisons le `total_amount` de la commande et le `nb_order_lines`. Dans un modèle idéal au grain **ligne de commande**, on recalculerait `quantity * unit_price` pour chaque ligne afin de vérifier la cohérence avec le total de la commande.

### 10. Comment rendez-vous votre script rejouable sans dupliquer les données ?

Le script utilise des requêtes **`INSERT ... ON CONFLICT`** (upsert) sur les clés naturelles : `ON CONFLICT (date_id) DO NOTHING` pour les dimensions, et `ON CONFLICT (order_id) DO UPDATE` pour la table de faits. Ainsi, le script peut être rejoué sans créer de doublons et met à jour les données existantes si elles ont changé.

---

## Étape 6 — Connecter Apache Superset

### Travail demandé

- Ajouter la connexion PostgreSQL dans Superset
- Déclarer les datasets nécessaires
- Créer les graphiques
- Construire un ou plusieurs dashboards

> **[TODO]** À réaliser manuellement dans l'interface Superset (http://localhost:8088).
> Connexion à utiliser : `postgresql://bi_user:bi_pass@host.docker.internal:5434/bi_db`

---

## Étape 7 — Créer les dashboards BI

### Dashboard 1 — Vue globale

- CA total
- Nombre de commandes
- Nombre de produits vendus
- Panier moyen
- Évolution du CA dans le temps

### Dashboard 2 — Analyse produits

- Top 10 produits par chiffre d’affaires
- Top 10 produits par quantité vendue
- CA par catégorie
- Quantité vendue par catégorie

### Dashboard 3 — Analyse clients

- Top clients par chiffre d’affaires
- Nombre de commandes par client
- Panier moyen par client

### Dashboard 4 — Analyse géographique

- Chiffre d’affaires par pays
- Nombre de commandes par pays
- Panier moyen par pays
- Quantité de produits vendus par pays
- Top produits par pays
- Répartition du CA par pays

### Questions BI par pays

1. **Quel pays génère le plus de chiffre d’affaires ?**
   > `[TODO]` Réponse à extraire du dashboard Superset (graphique "CA par pays").

2. **Quel pays génère le plus grand nombre de commandes ?**
   > `[TODO]` Réponse à extraire du dashboard Superset (graphique "Nombre de commandes par pays").

3. **Le pays avec le plus de commandes est-il aussi celui avec le plus gros panier moyen ?**
   > `[TODO]` Réponse à déduire en croisant les graphiques "Commandes par pays" et "Panier moyen par pays" dans Superset.

4. **Quels produits se vendent le mieux selon les pays ?**
   > `[TODO]` Réponse à extraire du graphique "Top produits par pays" dans Superset.

5. **Certaines catégories performent-elles mieux dans certains pays ?**
   > `[TODO]` Réponse à extraire en filtrant le dashboard par pays et catégorie dans Superset.

6. **Y a-t-il des pays avec beaucoup de commandes mais un faible chiffre d’affaires ?**
   > `[TODO]` Réponse à déduire en croisant "Commandes par pays" et "CA par pays" dans Superset.

7. **Y a-t-il des pays avec peu de commandes mais un panier moyen élevé ?**
   > `[TODO]` Réponse à déduire en croisant "Commandes par pays" et "Panier moyen par pays" dans Superset.

8. **Comment expliquer les différences de performance entre pays ?**
   > `[TODO]` Réponse à formuler après analyse des dashboards (facteurs possibles : pouvoir d'achat, offre produit locale, saisonnalité, frais de livraison).

---

## 10. Analyse architecturale finale

### 1. Pourquoi séparer le SI opérationnel du SI décisionnel ?

Le SI opérationnel (OLTP) est optimisé pour des transactions rapides, concurrentes et normalisées, tandis que le SI décisionnel (OLAP) est conçu pour des requêtes analytiques lourdes et agrégées sur de grands volumes historiques. Mélanger les deux sur la même infrastructure risquerait de dégrader les performances des applications métier et de bloquer les bases opérationnelles avec des requêtes longues. En outre, le décisionnel nécessite souvent des transformations, de l'historisation et une modélisation dénormalisée (schéma en étoile) incompatibles avec la fraîcheur et la normalisation du SI opérationnel. La séparation garantit donc la stabilité du système de production tout en autorisant des analyses complexes sans impact.

### 2. Pourquoi le Data Warehouse est-il une meilleure source pour Superset ?

Le Data Warehouse fournit un modèle unifié, dénormalisé et optimisé pour la lecture (schéma en étoile), ce qui élimine la nécessité pour Superset de joindre dynamiquement plusieurs bases opérationnelles distantes. Les données y sont pré-agrégées, nettoyées et historisées, garantissant la cohérence des indicateurs quel que soit l'état des sources opérationnelles. Connecter Superset directement aux microservices forcerait à reconstruire la logique métier dans chaque graphique, avec des risques d'incohérence et de performances dégradées. Le DW sert ainsi de *single source of truth* pour la BI.

### 3. Pourquoi les microservices ne sont-ils pas adaptés aux requêtes analytiques ?

Les microservices scindent les données dans des bases indépendantes et hétérogènes, ce qui rend impossible l'exécution de requêtes analytiques globales sans orchestration complexe (appels réseau, jointures applicatives, gestion de la latence). Chaque service expose son propre modèle de données, souvent normalisé pour des cas d'usage transactionnels précis, et non pas pour des agrégations cross-domain. Reconstruire un tableau de bord analytique en interrogeant trois APIs séparées serait lent, fragile et difficile à maintenir. Le Data Warehouse résout ce problème en centralisant et en restructurant les données pour l'analyse.

### 4. Quelle est la différence entre une base OLTP et une base OLAP ?

Une base **OLTP** (Online Transaction Processing) est conçue pour des opérations transactionnelles rapides (INSERT, UPDATE, DELETE) avec beaucoup d'utilisateurs simultanés ; elle est fortement normalisée (3NF) pour éviter la redondance et garantir l'intégrité. Une base **OLAP** (Online Analytical Processing) est orientée vers la lecture massive et les requêtes complexes agrégées (SUM, COUNT, GROUP BY) sur de larges plages temporelles ; elle est généralement dénormalisée (schéma en étoile ou en flocon) pour accélérer les jointures. En résumé, l'OLTP privilégie la fraîcheur et la cohérence transactionnelle, tandis que l'OLAP privilégie la performance des analyses historiques.

### 5. Quels problèmes avez-vous rencontrés lors du croisement des données ?

Le principal obstacle a été la **simplification du modèle `OrderLine`** par la migration `0002` : la suppression des champs `quantity`, `unit_price`, `line_total` et `product_name` a empêché l'ETL de calculer directement le chiffre d'affaires détaillé par ligne. Le serializer a dû compenser en appelant dynamiquement le `catalog-service` pour récupérer le prix et le nom du produit, introduisant une dépendance réseau et un point de fragilité. Par ailleurs, l'**absence de pagination** sur l'API Orders causait des timeouts ou des consommations mémoire excessives lors de l'extraction de l'historique complet des commandes. Enfin, les adresses clients étant stockées dans une table séparée (`catalog_address`), il a fallu mettre en place une logique de fallback (`is_default` puis première adresse disponible) pour associer une localisation géographique fiable à chaque commande.

### 6. Quelles incohérences avez-vous détectées ?

La plus grande incohérence résidait dans le **modèle `OrderLine` tronqué** : la base opérationnelle ne conservait plus que l'`order_id` et le `product_id`, sans quantité ni prix unitaire. Cela signifie que le `total_amount` stocké au niveau de la commande n'était pas vérifiable par une simple somme des lignes, et que l'historique des prix au moment de la commande était perdu si le produit changeait de prix dans le `catalog-service`. De plus, le script `superset-init.sh` livré avec des **retours à la ligne Windows (CRLF)** a empêché l'exécution correcte dans le conteneur Linux, bloquant l'initialisation de la métadonnée SQLite de Superset. Enfin, l'absence de pagination sur les endpoints exposait une incohérence entre le volume de données de test (20 000 commandes) et la capacité réelle de l'API à les servir de manière fiable.

### 7. Quelle donnée a été la plus difficile à intégrer ?

Les **lignes de commande (`OrderLine`)** ont été les plus difficiles à intégrer dans le schéma en étoile. La perte des champs `quantity` et `unit_price` a contraint l'ETL à ne pouvoir exploiter qu'un grain grossier (niveau commande) plutôt qu'un grain fin (niveau ligne). Pour peupler `fact_sales`, il a fallu agréger les `product_ids` par commande et retenir artificiellement le *produit le plus cher* comme représentant principal, ce qui masque la réalité des ventes multiples par panier. Cette approximation a été nécessaire car la base opérationnelle ne stockait plus les informations requises pour une analyse ligne par ligne. La reconstitution du prix réel au moment de l'achat a également nécessité des appels croisés vers le `catalog-service`, rendant l'intégration dépendante de la disponibilité d'un service tiers.

### 8. Que faudrait-il améliorer pour passer à une architecture data plus industrielle ?

Pour industrialiser cette architecture, plusieurs évolutions seraient nécessaires :

- **Orchestration ETL** : remplacer le script Python manuel par **Apache Airflow** (ou Prefect) afin de planifier, surveiller et relancer automatiquement les pipelines avec gestion des dépendances entre tâches.
- **Streaming et CDC** : introduire **Apache Kafka** (ou Debezium) pour capturer les changements des bases opérationnelles en temps réel et alimenter le DW en quasi-direct, plutôt qu'en batch nocturne.
- **Modélisation analytique dédiée** : séparer explicitement le modèle opérationnel (`OrderLine` allégé pour la transaction) du modèle analytique (`OrderLine` enrichi avec quantité, prix historisé, remises) afin de ne plus perdre d'information métier critique.
- **Tests automatisés** : ajouter des tests unitaires sur l'ETL (idempotence, règles métier) et des tests d'intégration sur les APIs (pagination, sérialisation) pour détecter les régressions dès le développement.
- **Monitoring et data quality** : mettre en place du logging structuré, des alertes sur la durée/fiabilité des pipelines, et des contrôles de qualité automatiques (nullité, unicité, cohérence des montants) via des outils comme Great Expectations ou des checks SQL dans Airflow.

---

## 11. Livrables

- ✅ Code Python des pipelines ETL (`etl/etl_sales.py`)
- ✅ Script SQL de création du Data Warehouse (DDL intégré dans `etl_sales.py`)
- ✅ Schéma du modèle décisionnel (voir sections Étape 3 et 4)
- ⚠️ Dashboards Superset → **[TODO]**
- ✅ README / Document de réponses (ce fichier `answer.md`)
