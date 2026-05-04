#!/bin/bash
# Script d'export des dashboards Superset
# À lancer depuis la racine du projet

set -e

echo "Export des dashboards Superset..."

# Exporte tout (dashboards, charts, datasets) dans un ZIP
docker exec superset superset export-dashboards -p /tmp/superset_export.zip

# Copie le ZIP hors du conteneur
docker cp superset:/tmp/superset_export.zip analytics/superset_export.zip

echo "Export terminé : analytics/superset_export.zip"
echo "N'oublie pas de commit ce fichier pour tes collègues !"
