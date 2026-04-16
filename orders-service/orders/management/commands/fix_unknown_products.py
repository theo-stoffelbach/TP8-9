import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from orders.models import OrderLine


class Command(BaseCommand):
    help = "Corrige les lignes de commande avec product_name 'Unknown Product' en récupérant le vrai nom depuis le catalog-service."

    def handle(self, *args, **options):
        catalog_url = getattr(settings, 'CATALOG_SERVICE_URL', 'http://localhost:8001')
        lines = OrderLine.objects.filter(product_name="Unknown Product")
        count = lines.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("Aucune ligne à corriger."))
            return

        self.stdout.write(f"{count} ligne(s) à corriger…")

        fixed = 0
        errors = 0
        for line in lines:
            try:
                response = requests.get(
                    f"{catalog_url}/api/products/{line.product_id}/",
                    timeout=5,
                )
                response.raise_for_status()
                product = response.json()
                line.product_name = product['name']
                line.unit_price = float(product['price'])
                line.save(update_fields=['product_name', 'unit_price'])
                self.stdout.write(f"  Ligne {line.id}: produit {line.product_id} → {line.product_name}")
                fixed += 1
            except requests.RequestException as e:
                self.stderr.write(f"  Ligne {line.id}: erreur pour produit {line.product_id}: {e}")
                errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"Terminé : {fixed} corrigée(s), {errors} erreur(s).")
        )
