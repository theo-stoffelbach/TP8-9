#!/bin/bash
set -e

echo "En attente de PostgreSQL..."
while ! python -c "
import psycopg2
try:
    psycopg2.connect(
        dbname='${DATABASE_NAME}',
        user='${DATABASE_USER}',
        password='${DATABASE_PASSWORD}',
        host='${DATABASE_HOST}',
        port='${DATABASE_PORT}'
    )
except psycopg2.OperationalError:
    exit(1)
" 2>/dev/null; do
    echo "PostgreSQL pas encore prêt, nouvelle tentative..."
    sleep 1
done
echo "PostgreSQL est prêt !"

echo "Application des migrations..."
python manage.py makemigrations catalog --noinput
python manage.py migrate --noinput

echo "Chargement des données de test..."
python manage.py seed_data

echo "Démarrage du serveur sur le port 8001..."
python manage.py runserver 0.0.0.0:8001
