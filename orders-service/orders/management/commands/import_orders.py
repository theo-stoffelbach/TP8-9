import json
from django.core.management.base import BaseCommand
from django.db import transaction
from pathlib import Path


class Command(BaseCommand):
    help = "Import 20k orders and orderlines from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON file containing orders and orderlines",
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
            from orders.models import (
                Order,
                OrderLine,
            )  # ← CHANGE "your_app" par ton app
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Please update the import path in this script:\n"
                    "   from your_app.models import Order, OrderLine"
                )
            )
            return

        orders_data = data.get("orders", [])
        orderlines_data = data.get("orderlines", [])
        metadata = data.get("metadata", {})

        self.stdout.write(self.style.WARNING(f"\n📊 Metadata:"))
        self.stdout.write(f"   - Total orders: {metadata.get('total_orders')}")
        self.stdout.write(f"   - Total orderlines: {metadata.get('total_orderlines')}")
        self.stdout.write(f"   - Unique customers: {metadata.get('unique_customers')}")
        self.stdout.write(
            f"   - Avg products per order: {metadata.get('avg_products_per_order')}"
        )
        self.stdout.write(f"   - Generated at: {metadata.get('generated_at')}\n")

        # Importer les orders
        self.stdout.write("📦 Importing orders...")
        orders_created = 0
        orders_skipped = 0
        order_map = {}  # Pour mapper les IDs JSON aux IDs Django

        orders_to_create = []

        for idx, order_data in enumerate(orders_data, 1):
            try:
                order = Order(
                    customer_id=order_data["customer_id"],
                    status=order_data["status"],
                    created_at=order_data["created_at"],
                )
                orders_to_create.append(order)

                if idx % batch_size == 0 or idx == len(orders_data):
                    # Créer en batch
                    created = Order.objects.bulk_create(orders_to_create)
                    orders_created += len(created)

                    # Récupérer les orders créés pour la map
                    for orig_order in orders_to_create:
                        # Chercher l'ordre créé par customer_id et created_at
                        db_order = Order.objects.filter(
                            customer_id=orig_order.customer_id,
                            created_at=orig_order.created_at,
                        ).first()
                        if db_order:
                            order_map[order_data.get("id")] = db_order.id

                    orders_to_create = []
                    self.stdout.write(
                        f"   ✓ Created {orders_created}/{len(orders_data)}"
                    )

            except Exception as e:
                orders_skipped += 1
                if not skip_errors:
                    self.stdout.write(self.style.ERROR(f"❌ Error on order {idx}: {e}"))
                    raise
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Skipped order {idx}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Orders imported: {orders_created} created, {orders_skipped} skipped\n"
            )
        )

        # Importer les orderlines
        self.stdout.write("📍 Importing orderlines...")
        orderlines_created = 0
        orderlines_skipped = 0

        orderlines_to_create = []

        for idx, orderline_data in enumerate(orderlines_data, 1):
            try:
                order_json_id = orderline_data["order_id"]

                # Récupérer l'order Django
                if order_json_id not in order_map:
                    # Si pas en cache, chercher en base
                    order = Order.objects.get(id=order_json_id)
                else:
                    order_id = order_map[order_json_id]
                    order = Order.objects.get(id=order_id)

                orderline = OrderLine(
                    order=order, product_id=orderline_data["product_id"]
                )
                orderlines_to_create.append(orderline)

                if idx % batch_size == 0 or idx == len(orderlines_data):
                    # Créer en batch
                    created = OrderLine.objects.bulk_create(
                        orderlines_to_create,
                        ignore_conflicts=True,  # Ignorer les doublons si unique_together
                    )
                    orderlines_created += len(created)
                    orderlines_to_create = []
                    self.stdout.write(
                        f"   ✓ Created {orderlines_created}/{len(orderlines_data)}"
                    )

            except Order.DoesNotExist:
                orderlines_skipped += 1
                if not skip_errors:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Order not found for orderline {idx}")
                    )
                    raise
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Skipped orderline {idx}: Order not found"
                        )
                    )
            except Exception as e:
                orderlines_skipped += 1
                if not skip_errors:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error on orderline {idx}: {e}")
                    )
                    raise
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Skipped orderline {idx}: {e}")
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Orderlines imported: {orderlines_created} created, {orderlines_skipped} skipped\n"
            )
        )

        # Résumé final
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("📈 IMPORT SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"Orders: {orders_created} created, {orders_skipped} skipped")
        self.stdout.write(
            f"Orderlines: {orderlines_created} created, {orderlines_skipped} skipped"
        )
        self.stdout.write(f"Total records: {orders_created + orderlines_created}")
        self.stdout.write(self.style.SUCCESS("=" * 60))
