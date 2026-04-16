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

echo "Superset prêt !"
exec gunicorn --bind 0.0.0.0:8088 --workers 2 --timeout 120 "superset.app:create_app()"
