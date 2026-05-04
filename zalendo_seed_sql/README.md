# Jeu de données SQL - Mini Zalando

Fichiers SQL avec INSERT uniquement, un fichier par table.

## Tables et volumes

- category: 50 lignes
- product: 1000 lignes
- customer: 5000 lignes
- address: 5925 lignes
- orders: 50000 lignes
- order_line: 96245 lignes

## Hypothèses de nommage

- Table commandes nommée `orders` pour éviter le mot réservé SQL `order`.
- Prix et montants au format décimal texte compatible NUMERIC/DECIMAL.
- La catégorie `Lingerie fine` a volontairement les produits les plus vendus pour faire ressortir les dashboards BI.

## Top produits par quantité vendue

- 15 - Passionata Nuisette satin champagne: 2260
- 6 - Etam Guêpière satin bordeaux: 2259
- 8 - Aubade Body dos nu en dentelle: 2245
- 2 - Triumph Tanga satin rouge: 2234
- 16 - Passionata Body string manches longues dentelle: 2219
- 5 - Chantelle Porte-jarretelles dentelle noire: 2214
- 11 - Calvin Klein Body string effet seconde peau: 2207
- 20 - Triumph Body bustier string: 2172
- 10 - Calvin Klein Tanga taille haute dentelle: 2171
- 7 - Intimissimi Nuisette ajourée rose poudré: 2166

## CA confirmé par pays

- France: 6888914.10 sur 28301 commandes confirmées
- Germany: 2020327.90 sur 8267 commandes confirmées
- Spain: 1162865.10 sur 4727 commandes confirmées
- Italy: 884444.70 sur 3650 commandes confirmées
- Belgium: 547488.00 sur 2227 commandes confirmées
- Netherlands: 365406.80 sur 1403 commandes confirmées
- Switzerland: 182413.60 sur 659 commandes confirmées
- Portugal: 82077.30 sur 327 commandes confirmées
