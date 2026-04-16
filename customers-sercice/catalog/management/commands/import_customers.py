import json
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.exceptions import ValidationError
from pathlib import Path


class Command(BaseCommand):
    help = "Import 10k customers and addresses from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON file containing customers and addresses",
        )
        parser.add_argument(
            "--skip-errors",
            action="store_true",
            help="Skip invalid records instead of stopping",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Batch size for bulk_create (default: 1000)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        json_file = options["json_file"]
        skip_errors = options["skip_errors"]
        batch_size = options["batch_size"]

        # Vérifier que le fichier existe
        if not Path(json_file).exists():
            self.stdout.write(self.style.ERROR(f"❌ File not found: {json_file}"))
            return

        # Charger le JSON
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"❌ JSON parsing error: {e}"))
            return

        # Import models - À ADAPTER AU NOM DE TON APP !
        try:
            from catalog.models import (
                Customer,
                Address,
            )
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Please update the import path in this script:\n"
                    "   from your_app.models import Customer, Address"
                )
            )
            return

        customers_data = data.get("customers", [])
        addresses_data = data.get("addresses", [])
        metadata = data.get("metadata", {})

        self.stdout.write(self.style.WARNING(f"\n📊 Metadata:"))
        self.stdout.write(f"   - Total customers: {metadata.get('total_customers')}")
        self.stdout.write(f"   - Total addresses: {metadata.get('total_addresses')}")
        self.stdout.write(f"   - Countries: {metadata.get('countries_count')}")
        self.stdout.write(f"   - Generated at: {metadata.get('generated_at')}\n")

        # Importer les customers
        self.stdout.write("👥 Importing customers...")
        customers_created = 0
        customers_skipped = 0
        customer_map = {}  # Pour mapper les IDs JSON aux IDs Django

        customers_to_create = []

        for idx, customer_data in enumerate(customers_data, 1):
            try:
                customer = Customer(
                    first_name=customer_data["first_name"],
                    last_name=customer_data["last_name"],
                    email=customer_data["email"],
                    phone=customer_data["phone"],
                    is_active=customer_data.get("is_active", True),
                )
                customers_to_create.append(customer)

                if idx % batch_size == 0 or idx == len(customers_data):
                    # Créer en batch
                    created = Customer.objects.bulk_create(
                        customers_to_create, ignore_conflicts=False
                    )
                    customers_created += len(created)

                    # Récupérer les customers créés pour la map
                    for orig_customer in customers_to_create:
                        db_customer = Customer.objects.get(email=orig_customer.email)
                        customer_map[customer_data.get("id")] = db_customer.id

                    customers_to_create = []
                    self.stdout.write(
                        f"   ✓ Created {customers_created}/{len(customers_data)}"
                    )

            except ValidationError as e:
                customers_skipped += 1
                if not skip_errors:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error on customer {idx}: {e}")
                    )
                    raise
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Skipped customer {idx}: {e}")
                    )
            except Exception as e:
                customers_skipped += 1
                if not skip_errors:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Unexpected error on customer {idx}: {e}")
                    )
                    raise
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Skipped customer {idx}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Customers imported: {customers_created} created, {customers_skipped} skipped\n"
            )
        )

        # Importer les adresses
        self.stdout.write("📍 Importing addresses...")
        addresses_created = 0
        addresses_skipped = 0

        addresses_to_create = []

        for idx, address_data in enumerate(addresses_data, 1):
            try:
                customer_json_id = address_data["customer_id"]

                # Récupérer le customer Django
                if customer_json_id not in customer_map:
                    # Si pas en cache, chercher en base
                    customer = Customer.objects.get(id=customer_json_id)
                else:
                    customer_id = customer_map[customer_json_id]
                    customer = Customer.objects.get(id=customer_id)

                address = Address(
                    customer=customer,
                    street=address_data["street"],
                    postal_code=address_data["postal_code"],
                    city=address_data["city"],
                    country=address_data.get("country", "France"),
                    is_default=address_data.get("is_default", False),
                )
                addresses_to_create.append(address)

                if idx % batch_size == 0 or idx == len(addresses_data):
                    # Créer en batch
                    created = Address.objects.bulk_create(addresses_to_create)
                    addresses_created += len(created)
                    addresses_to_create = []
                    self.stdout.write(
                        f"   ✓ Created {addresses_created}/{len(addresses_data)}"
                    )

            except Customer.DoesNotExist:
                addresses_skipped += 1
                if not skip_errors:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Customer not found for address {idx}")
                    )
                    raise
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Skipped address {idx}: Customer not found"
                        )
                    )
            except Exception as e:
                addresses_skipped += 1
                if not skip_errors:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error on address {idx}: {e}")
                    )
                    raise
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Skipped address {idx}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Addresses imported: {addresses_created} created, {addresses_skipped} skipped\n"
            )
        )

        # Résumé final
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("📈 IMPORT SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            f"Customers: {customers_created} created, {customers_skipped} skipped"
        )
        self.stdout.write(
            f"Addresses: {addresses_created} created, {addresses_skipped} skipped"
        )
        self.stdout.write(f"Total records: {customers_created + addresses_created}")
        self.stdout.write(self.style.SUCCESS("=" * 60))
