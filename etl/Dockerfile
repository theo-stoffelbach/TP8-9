FROM python:3.11-slim

WORKDIR /app

# Installation de psycopg2-binary
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Commande par défaut
CMD ["python", "etl_sales.py"]
