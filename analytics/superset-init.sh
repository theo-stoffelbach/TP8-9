#!/bin/bash
set -e

echo "Initialisation de Superset..."

superset db upgrade

superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname Admin \
  --email admin@admin.com \
  --password admin 2>/dev/null || echo "Admin existe déjà, on continue."

superset init

# Import automatique des dashboards au premier démarrage
IMPORT_FLAG="/app/superset_home/.superset_import_done"
if [ -f /tmp/superset_export.zip ] && [ ! -f "$IMPORT_FLAG" ]; then
    echo "Import automatique des dashboards..."
    superset import-dashboards -f /tmp/superset_export.zip -u admin || echo "Import échoué ou partiel, on continue."
    touch "$IMPORT_FLAG"
fi

echo "Superset prêt !"
exec gunicorn --bind 0.0.0.0:8088 --workers 2 --timeout 120 "superset.app:create_app()"
