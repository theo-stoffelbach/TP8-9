-- ─── Analytics DB Schema ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS pays (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL UNIQUE,
    slug        VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS produits (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(255) NOT NULL,
    prix        NUMERIC(10, 2) NOT NULL,
    categorie_id INTEGER REFERENCES categories(id)
);

CREATE TABLE IF NOT EXISTS commandes (
    id              SERIAL PRIMARY KEY,
    commande_id     INTEGER NOT NULL UNIQUE,
    customer_id     INTEGER NOT NULL,
    pays_id         INTEGER REFERENCES pays(id),
    date            TIMESTAMP NOT NULL,
    montant_total   NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS commande_produits (
    id              SERIAL PRIMARY KEY,
    commande_id     INTEGER REFERENCES commandes(id),
    produit_id      INTEGER REFERENCES produits(id),
    quantite        SMALLINT NOT NULL DEFAULT 1
);
