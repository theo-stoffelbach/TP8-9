from django.core.management.base import BaseCommand

from catalog.models import Address, Customer

CUSTOMERS = [
    {
        "first_name": "Sarah",
        "last_name": "Benali",
        "email": "sarah.benali@example.com",
        "phone": "0600000001",
        "is_active": True,
        "addresses": [
            {"street": "12 rue des Lilas", "postal_code": "38000", "city": "Grenoble", "country": "France", "is_default": True},
            {"street": "5 avenue Jean Jaurès", "postal_code": "69007", "city": "Lyon", "country": "France", "is_default": False},
        ],
    },
    {
        "first_name": "Thomas",
        "last_name": "Durand",
        "email": "thomas.durand@example.com",
        "phone": "0600000002",
        "is_active": True,
        "addresses": [
            {"street": "8 boulevard Haussmann", "postal_code": "75009", "city": "Paris", "country": "France", "is_default": True},
            {"street": "3 rue de la Paix", "postal_code": "06000", "city": "Nice", "country": "France", "is_default": False},
        ],
    },
    {
        "first_name": "Léa",
        "last_name": "Martin",
        "email": "lea.martin@example.com",
        "phone": "0600000003",
        "is_active": True,
        "addresses": [
            {"street": "22 rue du Faubourg Saint-Antoine", "postal_code": "75012", "city": "Paris", "country": "France", "is_default": True},
        ],
    },
    {
        "first_name": "Karim",
        "last_name": "Oubella",
        "email": "karim.oubella@example.com",
        "phone": "0600000004",
        "is_active": False,
        "addresses": [
            {"street": "14 allée des Roses", "postal_code": "33000", "city": "Bordeaux", "country": "France", "is_default": True},
        ],
    },
    {
        "first_name": "Emma",
        "last_name": "Petit",
        "email": "emma.petit@example.com",
        "phone": "0600000005",
        "is_active": True,
        "addresses": [
            {"street": "9 place du Capitole", "postal_code": "31000", "city": "Toulouse", "country": "France", "is_default": True},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the database with test customers and addresses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing customers and addresses before seeding",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            deleted, _ = Customer.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted} existing records"))

        created_customers = 0
        created_addresses = 0

        for data in CUSTOMERS:
            addresses = data.pop("addresses")
            customer, created = Customer.objects.get_or_create(
                email=data["email"],
                defaults=data,
            )
            if created:
                created_customers += 1
                self.stdout.write(f"  + Customer: {customer}")
            else:
                self.stdout.write(f"  ~ Skipped (already exists): {customer}")

            for addr_data in addresses:
                _, addr_created = Address.objects.get_or_create(
                    customer=customer,
                    street=addr_data["street"],
                    defaults=addr_data,
                )
                if addr_created:
                    created_addresses += 1

            # restore for potential re-runs
            data["addresses"] = addresses

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone — {created_customers} customer(s) and {created_addresses} address(es) created."
            )
        )
