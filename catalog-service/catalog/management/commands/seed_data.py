from django.core.management.base import BaseCommand
from catalog.models import Category, Product


class Command(BaseCommand):
    help = 'Charge les données de test dans la base de données'

    def handle(self, *args, **options):
        self.stdout.write('Chargement des catégories...')

        categories_data = [
            {'name': 'Sneakers', 'slug': 'sneakers'},
            {'name': 'Vestes', 'slug': 'vestes'},
            {'name': 'Accessoires', 'slug': 'accessoires'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name']}
            )
            categories[cat.slug] = cat
            status = 'Créé' if created else 'Existe déjà'
            self.stdout.write(f'  {status} : {cat.name}')

        self.stdout.write('Chargement des produits...')

        products_data = [
            {
                'name': 'Nike Air Zoom',
                'slug': 'nike-air-zoom',
                'description': 'Chaussure de running légère avec technologie Air Zoom.',
                'price': '129.90',
                'stock': 50,
                'category': categories['sneakers'],
            },
            {
                'name': 'Adidas Forum Low',
                'slug': 'adidas-forum-low',
                'description': 'Sneakers rétro Adidas Forum Low en cuir blanc.',
                'price': '109.90',
                'stock': 35,
                'category': categories['sneakers'],
            },
            {
                'name': 'Puma Rider',
                'slug': 'puma-rider',
                'description': 'Baskets Puma Rider au style vintage.',
                'price': '89.90',
                'stock': 40,
                'category': categories['sneakers'],
            },
            {
                'name': 'Veste en jean',
                'slug': 'veste-en-jean',
                'description': 'Veste en jean classique, coupe droite.',
                'price': '79.90',
                'stock': 25,
                'category': categories['vestes'],
            },
            {
                'name': 'Doudoune légère',
                'slug': 'doudoune-legere',
                'description': 'Doudoune légère et compressible, idéale pour la mi-saison.',
                'price': '119.90',
                'stock': 20,
                'category': categories['vestes'],
            },
            {
                'name': 'Sac sport',
                'slug': 'sac-sport',
                'description': 'Sac de sport spacieux avec compartiment chaussures.',
                'price': '49.90',
                'stock': 60,
                'category': categories['accessoires'],
            },
            {
                'name': 'Casquette noire',
                'slug': 'casquette-noire',
                'description': 'Casquette noire ajustable, style urbain.',
                'price': '24.90',
                'stock': 100,
                'category': categories['accessoires'],
            },
            {
                'name': 'Chaussettes running',
                'slug': 'chaussettes-running',
                'description': 'Lot de 3 paires de chaussettes techniques pour la course.',
                'price': '14.90',
                'stock': 150,
                'category': categories['accessoires'],
            },
        ]

        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults=prod_data
            )
            status = 'Créé' if created else 'Existe déjà'
            self.stdout.write(f'  {status} : {product.name}')

        self.stdout.write(self.style.SUCCESS('Données de test chargées avec succès !'))
