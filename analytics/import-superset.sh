#!/bin/bash
# Script d'import des dashboards Superset
# À lancer après avoir pull le repo

set -e

ZIP_FILE="analytics/superset_export.zip"

if [ ! -f "$ZIP_FILE" ]; then
    echo "Erreur : $ZIP_FILE introuvable."
    echo "Assure-toi d'avoir fait 'git pull' pour récupérer l'export."
    exit 1
fi

echo "Import des dashboards Superset depuis $ZIP_FILE..."

# Copie le ZIP dans le conteneur
docker cp "$ZIP_FILE" superset:/tmp/superset_export.zip

# Importe tout
MSYS_NO_PATHCONV=1 docker exec superset superset import-dashboards -p /tmp/superset_export.zip -u admin

echo "Import terminé ! Rafraîchis Superset (http://localhost:8088)"
