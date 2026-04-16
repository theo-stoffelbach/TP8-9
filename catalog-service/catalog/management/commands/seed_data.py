import random
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from catalog.models import Category, Product

TOTAL = 100_000
BATCH_SIZE = 1_000

# Listes de tailles réutilisables
CLOTHING_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SHOE_SIZES     = ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"]
JEAN_SIZES     = ["W28/L30", "W30/L30", "W30/L32", "W32/L30", "W32/L32", "W34/L32", "W34/L34", "W36/L32"]
KID_SIZES      = ["2 ans", "4 ans", "6 ans", "8 ans", "10 ans", "12 ans", "14 ans"]

# Listes de couleurs réutilisables
SPORT_COLORS   = ["Noir", "Blanc", "Rouge", "Bleu Marine", "Bleu Royal", "Gris", "Orange", "Vert", "Jaune", "Violet"]
FASHION_COLORS = ["Noir", "Blanc", "Beige", "Bleu Marine", "Bordeaux", "Gris Chiné", "Olive", "Caramel", "Rose Poudré", "Crème", "Anthracite", "Corail"]
HOME_COLORS    = ["Blanc", "Noir", "Gris", "Beige", "Naturel", "Anthracite", "Taupe", "Terracotta", "Bleu Canard"]
DENIM_COLORS   = ["Bleu Clair", "Bleu Foncé", "Gris", "Noir", "Bleu Délavé", "Blanc Cassé"]

# Format de chaque catégorie :
# (nom, slug, types_produits, marques, tailles_ou_None, couleurs_ou_None,
#  extras_ou_None, label_extra_ou_None)
#
# extras  = liste de valeurs spéciales (goûts, années, etc.)
# label_extra = préfixe affiché : "Goût", "Éd.", "Coloris"
CATEGORIES = [
    # ── Sports chaussures ───────────────────────────────────────────────
    ("Sneakers", "sneakers",
     ["Air Max", "Ultra Boost", "Chuck Taylor", "Old Skool", "Forum Low",
      "990v5", "Gel-Nimbus", "Superstar", "Stan Smith", "Classic Leather",
      "Cortez", "Gel-Kayano", "Wave Rider", "Cumulus", "Blazer Mid"],
     ["Nike", "Adidas", "Puma", "Reebok", "New Balance", "Asics",
      "Converse", "Vans", "Fila", "Skechers"],
     SHOE_SIZES, SPORT_COLORS, None, None),

    ("Running", "running",
     ["Chaussure de trail", "Chaussure de route", "Chaussure marathon",
      "Chaussure minimaliste", "Chaussure stabilité", "Chaussure amorti max",
      "Spike d'athlétisme", "Chaussure cross-training", "Chaussure légère"],
     ["Nike", "Adidas", "Asics", "New Balance", "Brooks", "Saucony",
      "Hoka", "On Running", "Mizuno", "Under Armour"],
     SHOE_SIZES, SPORT_COLORS, None, None),

    ("Basketball", "basketball",
     ["Chaussure de basketball haute", "Chaussure de basketball basse",
      "Maillot basketball", "Short basketball", "Débardeur basketball",
      "Veste warm-up", "Chaussette haute", "Genouillère", "Sac basketball"],
     ["Nike", "Adidas", "Jordan", "Puma", "Under Armour", "Reebok", "And1"],
     SHOE_SIZES, SPORT_COLORS, None, None),

    ("Football", "football",
     ["Crampons terrain souple", "Crampons terrain dur", "Chaussure indoor",
      "Maillot football", "Short football", "Chaussette football",
      "Protège-tibia", "Gants de gardien", "Survêtement football",
      "Ballon de football"],
     ["Nike", "Adidas", "Puma", "Umbro", "Hummel", "Kipsta", "Uhlsport"],
     CLOTHING_SIZES, SPORT_COLORS, None, None),

    ("Tennis", "tennis",
     ["Chaussure de tennis", "Raquette de tennis", "Polo tennis",
      "Short tennis", "Jupe tennis", "Survêtement tennis", "Sac de raquette",
      "Bandeau tennis", "Chaussette tennis"],
     ["Wilson", "Babolat", "Head", "Nike", "Adidas", "Lacoste",
      "Yonex", "Dunlop"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    # ── Mode haut ───────────────────────────────────────────────────────
    ("Vestes", "vestes",
     ["Veste bomber", "Veste en jean", "Veste en cuir", "Veste blazer",
      "Veste militaire", "Veste college", "Veste coupe-vent",
      "Veste softshell", "Veste zippée", "Veste à capuche"],
     ["Zara", "H&M", "Uniqlo", "Mango", "Hugo Boss", "Calvin Klein",
      "Tommy Hilfiger", "Ralph Lauren", "Gap", "Carhartt"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Manteaux", "manteaux",
     ["Manteau long", "Manteau court", "Manteau en laine", "Manteau oversize",
      "Doudoune longue", "Parka", "Trench-coat", "Caban", "Peacoat"],
     ["Zara", "Mango", "The North Face", "Columbia", "Patagonia",
      "Tommy Hilfiger", "Max Mara", "Camaïeu", "H&M", "Uniqlo"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Pulls", "pulls",
     ["Pull col rond", "Pull col V", "Pull col roulé", "Sweat-shirt",
      "Hoodie", "Sweat zippé", "Pull oversize", "Cardigan",
      "Pull maille", "Pull à torsades"],
     ["Uniqlo", "H&M", "Zara", "Gap", "Ralph Lauren", "Lacoste",
      "Tommy Hilfiger", "Carhartt", "Nike", "Adidas"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("T-shirts", "t-shirts",
     ["T-shirt basique", "T-shirt graphique", "T-shirt oversize",
      "T-shirt slim", "T-shirt manches longues", "T-shirt col V",
      "Polo", "T-shirt tie-dye", "T-shirt boxy", "Débardeur"],
     ["Uniqlo", "H&M", "Zara", "Gap", "Fruit of the Loom",
      "Lacoste", "Tommy Hilfiger", "Nike", "Adidas", "Carhartt"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Chemises", "chemises",
     ["Chemise oxford", "Chemise à carreaux", "Chemise en lin",
      "Chemise en denim", "Chemise slim", "Chemise oversize",
      "Chemise chambray", "Chemise flanelle", "Chemise hawaïenne"],
     ["Zara", "H&M", "Uniqlo", "Ralph Lauren", "Hugo Boss",
      "Tommy Hilfiger", "Diesel", "Gap", "Mango", "Jules"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    # ── Mode bas ─────────────────────────────────────────────────────────
    ("Jeans", "jeans",
     ["Jean slim", "Jean skinny", "Jean straight", "Jean bootcut",
      "Jean wide leg", "Jean mom", "Jean baggy", "Jean boyfriend",
      "Jean taille haute", "Jean déchiré"],
     ["Levi's", "Wrangler", "Lee", "Diesel", "G-Star", "Replay",
      "Calvin Klein", "Guess", "Pepe Jeans", "Jack & Jones"],
     JEAN_SIZES, DENIM_COLORS, None, None),

    ("Pantalons", "pantalons",
     ["Pantalon chino", "Pantalon cargo", "Pantalon de costume",
      "Pantalon jogger", "Pantalon large", "Pantalon fuselé",
      "Pantalon velours", "Pantalon tailleur", "Pantalon palazzo",
      "Legging"],
     ["Zara", "H&M", "Uniqlo", "Mango", "Hugo Boss",
      "Carhartt", "Dickies", "Gap", "J.Crew", "Pull&Bear"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Shorts", "shorts",
     ["Short cargo", "Short en jean", "Short de sport", "Short bermuda",
      "Short cycliste", "Short running", "Short basket",
      "Short imprimé", "Short fluide"],
     ["Zara", "H&M", "Nike", "Adidas", "Carhartt", "Dickies",
      "Quiksilver", "Billabong", "O'Neill", "Gap"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Robes", "robes",
     ["Robe midi", "Robe maxi", "Robe mini", "Robe portefeuille",
      "Robe chemise", "Robe à fleurs", "Robe bustier", "Robe bodycon",
      "Robe babydoll", "Robe de soirée"],
     ["Zara", "H&M", "Mango", "Shein", "Asos", "Bershka",
      "Pull&Bear", "Stradivarius", "Camaïeu", "Minelli"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Jupes", "jupes",
     ["Jupe midi", "Jupe maxi", "Jupe mini", "Jupe crayon",
      "Jupe plissée", "Jupe portefeuille", "Jupe en jean",
      "Jupe asymétrique", "Jupe évasée", "Jupe en cuir"],
     ["Zara", "H&M", "Mango", "Asos", "Bershka",
      "Stradivarius", "Camaïeu", "Minelli", "Uniqlo", "Pull&Bear"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    # ── Accessoires mode ────────────────────────────────────────────────
    ("Accessoires", "accessoires",
     ["Ceinture", "Bretelles", "Nœud papillon", "Cravate",
      "Écharpe", "Gants en cuir", "Lunettes de soleil",
      "Chapeau fedora", "Bonnet tricoté", "Pochette"],
     ["Lacoste", "Hugo Boss", "Ralph Lauren", "Tommy Hilfiger",
      "Guess", "Fossil", "Oakley", "Ray-Ban", "Le Tanneur", "Longchamp"],
     None, FASHION_COLORS, None, None),

    ("Casquettes", "casquettes",
     ["Casquette snapback", "Casquette fitted", "Casquette dad hat",
      "Casquette trucker", "Bob", "Bucket hat",
      "Casquette baseball", "Casquette 5 panels", "Casquette camionneur"],
     ["Nike", "Adidas", "New Era", "Carhartt", "Vans",
      "Supreme", "Stüssy", "The North Face", "Puma", "Fila"],
     None, SPORT_COLORS, None, None),

    ("Sacs", "sacs",
     ["Sac à dos", "Sac de sport", "Tote bag", "Sac banane",
      "Sacoche", "Sac de voyage", "Sac à main", "Sac messenger",
      "Pochette", "Sac gym"],
     ["Nike", "Adidas", "The North Face", "Fjällräven", "Herschel",
      "Longchamp", "Eastpak", "Kipling", "Vans", "Le Coq Sportif"],
     None, FASHION_COLORS, None, None),

    ("Montres", "montres",
     ["Montre analogique", "Montre digitale", "Montre connectée",
      "Montre sport", "Montre chronographe", "Montre minimaliste",
      "Montre skeleton", "Montre automatique", "Montre à quartz"],
     ["Casio", "Seiko", "Fossil", "Timex", "Swatch",
      "Garmin", "Suunto", "Tissot", "Lacoste", "Michael Kors"],
     None, None,
     ["Acier inoxydable", "Bracelet cuir", "Bracelet silicone",
      "Bracelet tissu", "Bracelet métal doré", "Bracelet milanais"],
     "Bracelet"),

    ("Bijoux", "bijoux",
     ["Collier", "Bracelet", "Bague", "Boucles d'oreilles",
      "Chevalière", "Gourmette", "Pendentif", "Chaîne", "Manchette"],
     ["Pandora", "Swarovski", "Tous", "Agatha", "Fossil",
      "Maty", "Histoire d'Or", "Cleor", "Brice", "Marc Orian"],
     None, None,
     ["Or jaune", "Or blanc", "Argent", "Acier", "Or rosé",
      "Plaqué or", "Titanium"],
     "Métal"),

    ("Chaussettes", "chaussettes",
     ["Chaussettes basses", "Chaussettes hautes", "Chaussettes invisibles",
      "Chaussettes de sport", "Chaussettes thermiques",
      "Lot de 3 paires", "Lot de 5 paires", "Chaussettes antidérapantes",
      "Chaussettes de randonnée"],
     ["Nike", "Adidas", "Falke", "Burlington", "Stance",
      "Décathlon", "Uniqlo", "Happy Socks", "Puma", "Levi's"],
     ["35-38", "39-42", "43-46"], FASHION_COLORS, None, None),

    ("Sous-vêtements", "sous-vetements",
     ["Boxer", "Caleçon", "Slip", "Bralette", "Soutien-gorge sport",
      "Culotte", "Shorty", "String", "Combinaison", "Caraco"],
     ["Calvin Klein", "Hugo Boss", "Dim", "Triumph", "Sloggi",
      "Tommy Hilfiger", "Emporio Armani", "Uniqlo", "Hom", "Passionata"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Pyjamas", "pyjamas",
     ["Pyjama deux pièces", "Pyjama combinaison", "Pyjama satiné",
      "Pyjama flanelle", "Short de nuit", "Chemise de nuit",
      "Nuisette", "Pyjama imprimé", "Pyjama polaire"],
     ["Etam", "Undiz", "Calida", "Triumph", "H&M",
      "Zara", "Primark", "La Redoute", "Marks & Spencer", "Dim"],
     CLOTHING_SIZES, FASHION_COLORS, None, None),

    ("Maillots de bain", "maillots-de-bain",
     ["Maillot une pièce", "Bikini triangle", "Tankini",
      "Monokini", "Short de bain", "Slip de bain",
      "Maillot sport", "Burkini"],
     ["Speedo", "Arena", "Seafolly", "Billabong", "Rip Curl",
      "O'Neill", "Quiksilver", "H&M", "Zara", "Banana Moon"],
     CLOTHING_SIZES, SPORT_COLORS, None, None),

    # ── Sport & outdoor ─────────────────────────────────────────────────
    ("Vêtements de sport", "vetements-de-sport",
     ["Brassière de sport", "Legging de sport", "T-shirt de sport",
      "Veste de sport", "Short de sport", "Débardeur de sport",
      "Ensemble sport", "Survêtement", "Collant thermique"],
     ["Nike", "Adidas", "Puma", "Under Armour", "Reebok",
      "Gymshark", "Lululemon", "Fabletics", "Asics", "New Balance"],
     CLOTHING_SIZES, SPORT_COLORS, None, None),

    ("Yoga", "yoga",
     ["Tapis de yoga", "Legging yoga", "Brassière yoga", "Bloc de yoga",
      "Sangle de yoga", "Coussin de méditation", "Shorts de yoga",
      "T-shirt yoga", "Couverture de yoga"],
     ["Lululemon", "Manduka", "Gaiam", "Gymshark",
      "Nike", "Adidas", "Decathlon", "Fabletics", "Alo Yoga", "Jade"],
     CLOTHING_SIZES, SPORT_COLORS, None, None),

    ("Cyclisme", "cyclisme",
     ["Cuissard de vélo", "Maillot cyclisme", "Coupe-vent vélo",
      "Casque vélo", "Gants vélo", "Chaussures vélo",
      "Lunettes vélo", "Gilet cyclisme", "Veste vélo"],
     ["Castelli", "Assos", "Rapha", "Pearl Izumi",
      "Shimano", "Decathlon", "Santini", "Sportful", "Gore", "Mavic"],
     CLOTHING_SIZES, SPORT_COLORS, None, None),

    ("Randonnée", "randonnee",
     ["Chaussures de randonnée basses", "Chaussures de randonnée hautes",
      "Chaussettes rando", "Pantalon de randonnée", "Veste de randonnée",
      "T-shirt rando", "Sac à dos rando", "Guêtres", "Bâton de marche",
      "Poncho de pluie"],
     ["Salomon", "Merrell", "The North Face", "Columbia",
      "Mammut", "Fjällräven", "Lowa", "Scarpa", "Decathlon", "Keen"],
     SHOE_SIZES, SPORT_COLORS, None, None),

    ("Ski", "ski",
     ["Veste de ski", "Pantalon de ski", "Combinaison de ski",
      "Sous-couche thermique", "Chaussettes de ski", "Gants de ski",
      "Bonnet de ski", "Cagoule", "Masque de ski", "Protège-dos"],
     ["Rossignol", "Salomon", "Atomic", "Head",
      "The North Face", "Columbia", "Phenix", "Völkl", "Helly Hansen", "Bogner"],
     CLOTHING_SIZES, SPORT_COLORS, None, None),

    ("Natation", "natation",
     ["Maillot de natation", "Lunettes de natation", "Bonnet de bain",
      "Combinaison de natation", "Plaquettes de natation",
      "Pull-buoy", "Palmes", "Serviette microfibre", "Short de natation"],
     ["Speedo", "Arena", "TYR", "Nabaiji", "Zoggs",
      "Funky Trunks", "Decathlon", "MP Michael Phelps", "Finis", "Blueseventy"],
     CLOTHING_SIZES, SPORT_COLORS, None, None),

    ("Équipement fitness", "equipement-fitness",
     ["Haltères", "Kettlebell", "Bande élastique", "Corde à sauter",
      "Tapis de fitness", "Rouleau de massage", "Banc de musculation",
      "Gants de musculation", "Ceinture lombaire", "Poignées de push-up"],
     ["Decathlon", "Reebok", "Nike", "CAP Barbell",
      "Bowflex", "TRX", "Domyos", "ProForm", "NordicTrack", "Trigger Point"],
     None, SPORT_COLORS, None, None),

    ("Nutrition sportive", "nutrition-sportive",
     ["Protéines whey", "Créatine monohydrate", "BCAA", "Pré-workout",
      "Mass gainer", "Barre protéinée", "Shaker", "Vitamines sport",
      "Oméga-3", "Caséine"],
     ["Optimum Nutrition", "MyProtein", "Scitec", "Bulk",
      "PhD Nutrition", "Weider", "Dymatize", "BSN", "Mutant", "USN"],
     None, None,
     ["Chocolat", "Vanille", "Fraise", "Caramel", "Cookies & Cream",
      "Banane", "Noisette", "Mangue", "Nature", "Citron"],
     "Goût"),

    # ── Électronique ────────────────────────────────────────────────────
    ("Électronique", "electronique",
     ["Batterie externe", "Hub USB-C", "Câble USB-C tressé",
      "Chargeur sans fil", "Support téléphone voiture",
      "Multi-prise USB", "Prise connectée", "Disque dur externe",
      "Clé USB", "Adaptateur HDMI"],
     ["Anker", "Belkin", "Samsung", "Baseus",
      "Ugreen", "RAVPower", "Aukey", "Xiaomi", "Apple", "Sony"],
     None, None,
     ["Blanc", "Noir", "Gris", "Bleu", "Rouge"], "Coloris"),

    ("Smartphones", "smartphones",
     ["Coque transparente", "Coque silicone", "Étui portefeuille",
      "Verre trempé", "Chargeur rapide 65W", "Câble USB-C",
      "Support voiture magnétique", "Anneau support", "Pop socket",
      "Câble Lightning"],
     ["Spigen", "OtterBox", "UAG", "Belkin",
      "Anker", "Apple", "Samsung", "Caseology", "Ringke", "ESR"],
     None, None,
     ["iPhone 15", "iPhone 14", "Samsung S24", "Samsung S23",
      "Pixel 8", "OnePlus 12", "Xiaomi 14", "Universel"],
     "Compatible"),

    ("Ordinateurs", "ordinateurs",
     ["Souris sans fil", "Clavier mécanique", "Webcam HD 1080p",
      "Microphone USB cardioïde", "Tapis de souris XL",
      "Support laptop réglable", "Refroidisseur PC portable",
      "Hub USB 7 ports", "Lampe de bureau LED", "Repose-poignets"],
     ["Logitech", "Razer", "SteelSeries", "Corsair",
      "HyperX", "Microsoft", "Asus", "Dell", "HP", "Keychron"],
     None, None,
     ["Noir", "Blanc", "Argent", "Bleu", "Rose"], "Coloris"),

    ("Tablettes", "tablettes",
     ["Housse de protection", "Stylet de précision", "Clavier bluetooth",
      "Support tablette bureau", "Film protecteur mat",
      "Chargeur USB-C 20W", "Étui rotatif", "Stand tablette pliable"],
     ["Apple", "Samsung", "Logitech", "Spigen",
      "ESR", "Anker", "Baseus", "Tucano", "Targus", "Belkin"],
     None, None,
     ["iPad 10", "iPad Pro", "Galaxy Tab S9", "Galaxy Tab A9",
      "Surface Pro", "Universel 10 pouces", "Universel 11 pouces"],
     "Compatible"),

    ("Audio", "audio",
     ["Écouteurs sans fil", "Casque audio réduction de bruit",
      "Enceinte bluetooth portable", "Barre de son", "Platine vinyle",
      "Câble jack 3.5mm", "Amplificateur HiFi",
      "Écouteurs intra-auriculaires", "Micro-cravate USB"],
     ["Sony", "Bose", "Jabra", "JBL", "Sennheiser",
      "Apple", "Samsung", "Marshall", "Bang & Olufsen", "Anker Soundcore"],
     None, None,
     ["Noir", "Blanc", "Bleu", "Rose", "Argent", "Vert Forêt"], "Coloris"),

    ("Gaming", "gaming",
     ["Manette de jeu", "Casque gaming 7.1", "Souris gaming",
      "Clavier gaming mécanique", "Tapis gaming XL",
      "Siège gamer", "Support casque", "Lampe LED RGB",
      "Carte mémoire microSD", "Webcam streaming"],
     ["Razer", "SteelSeries", "Logitech", "Corsair",
      "HyperX", "Xbox", "PlayStation", "Thrustmaster", "Astro", "Scuf"],
     None, None,
     ["Noir", "Blanc", "Rouge", "Bleu", "Violet RGB"], "Coloris"),

    # ── Maison ──────────────────────────────────────────────────────────
    ("Maison", "maison",
     ["Bougie parfumée", "Diffuseur d'huiles essentielles", "Cadre photo",
      "Vase décoratif", "Miroir mural", "Horloge murale",
      "Porte-manteau design", "Panier de rangement", "Boîte de rangement"],
     ["IKEA", "Maisons du Monde", "Zara Home", "H&M Home",
      "Muji", "Habitat", "Alinéa", "But", "Conforama", "La Redoute"],
     None, HOME_COLORS, None, None),

    ("Cuisine", "cuisine",
     ["Couteau de chef", "Planche à découper", "Poêle antiadhésive",
      "Casserole inox", "Cafetière filtre", "Blender", "Robot de cuisine",
      "Fouet inox", "Spatule silicone", "Thermomètre de cuisine"],
     ["Tefal", "Le Creuset", "KitchenAid", "Moulinex",
      "Philips", "Bosch", "WMF", "Pyrex", "Joseph Joseph", "Cuisinart"],
     None, HOME_COLORS, None, None),

    ("Décoration", "decoration",
     ["Tableau décoratif", "Sculpture décorative", "Plante artificielle",
      "Pot de fleurs", "Lanterne", "Guirlande lumineuse",
      "Coussin décoratif", "Tapis de salon", "Rideau occultant"],
     ["IKEA", "Maisons du Monde", "Zara Home", "H&M Home",
      "Atmosphera", "Habitat", "Alinéa", "Muji", "Sklum", "La Redoute"],
     None, HOME_COLORS, None, None),

    ("Mobilier", "mobilier",
     ["Chaise de bureau ergonomique", "Bureau pliant",
      "Étagère murale flottante", "Table de chevet",
      "Meuble à chaussures", "Bibliothèque", "Pouf",
      "Tabouret de bar", "Banc d'entrée", "Console"],
     ["IKEA", "Habitat", "But", "Conforama", "La Redoute",
      "Maisons du Monde", "Alinéa", "Sklum", "Jarvis", "Flexa"],
     None, HOME_COLORS, None, None),

    ("Literie", "literie",
     ["Oreiller mémoire de forme", "Couette légère 200g",
      "Couette chaude 400g", "Drap housse", "Taie d'oreiller",
      "Surmatelas", "Protège-matelas", "Plaid polaire",
      "Couverture lestée", "Parure de lit"],
     ["Dodo", "Doulito", "Dunlopillo", "Emma", "Purple",
      "IKEA", "Molly Mutt", "Coton Bio", "La Redoute", "Essix"],
     None, HOME_COLORS, None, None),

    ("Jardinage", "jardinage",
     ["Arrosoir 10L", "Gants de jardinage", "Truelle inox",
      "Sécateur Bypass", "Pot de fleurs extérieur",
      "Terreau universel", "Engrais granulé",
      "Tuyau d'arrosage extensible", "Lance d'arrosage réglable",
      "Semences légumes"],
     ["Fiskars", "Wolf-Garten", "Hozelock", "Gardena",
      "Husqvarna", "Bosch", "Ronseal", "Green Thumb", "Déco & Nature", "Vilmorin"],
     None, HOME_COLORS, None, None),

    ("Bricolage", "bricolage",
     ["Perceuse visseuse sans fil", "Tournevis électrique",
      "Niveau à bulle laser", "Mètre ruban 5m",
      "Pince multiprises", "Marteau de charpentier",
      "Scie circulaire", "Boîte à outils complète",
      "Escabeau 3 marches", "Ponceuse orbitale"],
     ["Bosch", "Makita", "DeWalt", "Black+Decker",
      "Stanley", "Facom", "Milwaukee", "Metabo", "Hilti", "Ryobi"],
     None, None,
     ["Jaune/Noir", "Bleu/Noir", "Rouge/Noir", "Vert/Noir", "Orange/Noir"],
     "Coloris"),

    # ── Culture & enfants ────────────────────────────────────────────────
    ("Livres", "livres",
     ["Roman policier", "Science-fiction", "Développement personnel",
      "Biographie", "Livre de cuisine", "Guide de voyage",
      "Essai historique", "Livre de philosophie",
      "Bande dessinée", "Manga"],
     ["Gallimard", "Hachette", "Flammarion", "Albin Michel",
      "Le Seuil", "Pocket", "Le Livre de Poche", "Actes Sud",
      "Larousse", "Nathan"],
     None, None,
     ["Poche", "Broché", "Grand format", "Luxe", "Illustré"], "Format"),

    ("Jouets", "jouets",
     ["Puzzle 1000 pièces", "Jeu de construction", "Figurine articulée",
      "Jeu de société familial", "Peluche géante",
      "Circuit électrique", "Poupée mannequin",
      "Jeu de cartes", "Jeu de dés", "Construction magnétique"],
     ["Lego", "Playmobil", "Fisher-Price", "Mattel",
      "Hasbro", "Ravensburger", "Clementoni", "Djeco",
      "Orchard Toys", "Learning Resources"],
     None, None,
     ["3-5 ans", "5-8 ans", "8-12 ans", "12 ans et +", "Tout âge"],
     "Âge"),

    ("Enfants", "enfants",
     ["T-shirt enfant", "Jean enfant", "Veste enfant",
      "Chaussures enfant", "Pyjama enfant", "Pull enfant",
      "Robe enfant", "Manteau enfant", "Short enfant",
      "Salopette enfant"],
     ["Zara Kids", "H&M Kids", "Petit Bateau", "Absorba",
      "Okaïdi", "Vertbaudet", "Tape à l'Œil", "Du Pareil au Même",
      "Jacadi", "Bonpoint"],
     KID_SIZES, FASHION_COLORS, None, None),

    # ── Beauté & santé ───────────────────────────────────────────────────
    ("Beauté", "beaute",
     ["Crème hydratante visage", "Sérum anti-âge", "Huile corps nourrissante",
      "Masque purifiant", "Shampoing fortifiant",
      "Après-shampoing réparateur", "Gel douche surgras",
      "Déodorant 48h", "Crème solaire SPF50", "Baume à lèvres"],
     ["L'Oréal", "Nivea", "Vichy", "La Roche-Posay",
      "Nuxe", "Garnier", "Dove", "Neutrogena", "Caudalie", "Avène"],
     None, None,
     ["Peau sèche", "Peau grasse", "Peau mixte", "Peau sensible",
      "Peau normale", "Tous types de peau"],
     "Pour"),

    ("Santé", "sante",
     ["Tensiomètre automatique", "Thermomètre frontal",
      "Oxymètre de pouls", "Balance connectée",
      "Coussin chauffant électrique", "Semelles orthopédiques",
      "Attelle de poignet", "Bandage élastique",
      "Gel froid sportif", "Masseur électrique shiatsu"],
     ["Omron", "Withings", "Beurer", "Thermos",
      "Compeed", "Sigvaris", "Epitact", "Thuasne",
      "Polar", "Garmin"],
     None, None,
     ["Adulte", "Senior", "Sport", "Confort", "Médical"], "Usage"),
]

DESCRIPTIONS = [
    "Confort et performance au quotidien pour une utilisation intensive.",
    "Design moderne et matériaux de haute qualité pour un style affirmé.",
    "Technologie de pointe pour des performances optimales en toutes circonstances.",
    "Style intemporel et confort exceptionnel pour toutes les occasions.",
    "Fabriqué avec des matériaux éco-responsables et durables.",
    "Coupe ajustée et respirante, parfaite pour le sport et le casual.",
    "Résistant et léger, conçu pour affronter toutes les conditions météo.",
    "Finitions soignées et détails précis pour un look impeccable.",
    "Polyvalent et pratique, s'adapte facilement à toutes vos tenues.",
    "Haute performance avec un design élégant et contemporain.",
    "Idéal pour les amateurs de sport comme pour les fashionistas urbains.",
    "Collection exclusive alliant confort optimal et esthétique moderne.",
    "Matière premium, coupe parfaite pour une silhouette valorisée.",
    "Innovation et style pour accompagner vos aventures du quotidien.",
    "Qualité professionnelle accessible, pour performer à votre meilleur niveau.",
    "Tissu technique à séchage rapide, idéal pour les activités intenses.",
    "Ergonomie pensée pour maximiser votre liberté de mouvement.",
    "Certification OEKO-TEX, sans substances nocives, respect de la peau.",
    "Édition limitée, pièce incontournable de la saison.",
    "Rapport qualité-prix imbattable, idéal pour débuter ou progresser.",
]


class Command(BaseCommand):
    help = 'Peuple la base de données avec 50 catégories et 100 000 produits cohérents'

    def handle(self, *args, **options):
        self.stdout.write('Création des 50 catégories...')
        cat_map = {}
        for entry in CATEGORIES:
            name, slug = entry[0], entry[1]
            cat, created = Category.objects.get_or_create(
                slug=slug, defaults={'name': name}
            )
            cat_map[slug] = cat
            status = 'Créée' if created else 'Existe déjà'
            self.stdout.write(f'  {status} : {cat.name}')

        self.stdout.write(self.style.SUCCESS(f'{len(cat_map)} catégories prêtes.'))

        existing_count = Product.objects.count()
        if existing_count >= TOTAL:
            self.stdout.write(self.style.SUCCESS(
                f'{existing_count} produits déjà présents, seed ignoré.'
            ))
            return

        remaining = TOTAL - existing_count
        self.stdout.write(f'Génération de {remaining} produits manquants...')

        existing_slugs = set(Product.objects.values_list('slug', flat=True))
        existing_names = set(Product.objects.values_list('name', flat=True))
        products_to_create = []
        created_count = 0
        counter = existing_count

        while created_count < remaining:
            entry = random.choice(CATEGORIES)
            _, cat_slug, product_types, brands, sizes, colors, extras, extra_label = entry
            cat_obj = cat_map[cat_slug]

            product_type = random.choice(product_types)
            brand        = random.choice(brands)
            size         = random.choice(sizes)   if sizes   else None
            color        = random.choice(colors)  if colors  else None
            extra        = random.choice(extras)  if extras  else None

            # Construire le nom de façon cohérente
            parts = [brand, product_type]
            if color:
                parts.append(color)
            if size:
                parts.append(size)
            if extra and extra_label:
                parts.append(f"{extra_label} {extra}")
            base_name = " ".join(parts)

            # Garantir l'unicité du nom
            name = base_name
            name_suffix = 2
            while name in existing_names:
                name = f"{base_name} #{name_suffix}"
                name_suffix += 1
            existing_names.add(name)

            base_slug = slugify(f"{brand}-{product_type}-{counter}")
            while base_slug in existing_slugs:
                counter += 1
                base_slug = slugify(f"{brand}-{product_type}-{counter}")

            existing_slugs.add(base_slug)

            desc_base = random.choice(DESCRIPTIONS)
            if extra and extra_label:
                description = f"{desc_base} {extra_label} : {extra}."
            elif color:
                description = f"{desc_base} Coloris : {color}."
            else:
                description = desc_base

            products_to_create.append(Product(
                name=name,
                slug=base_slug,
                description=description,
                price=round(random.uniform(4.99, 499.99), 2),
                stock=random.randint(0, 200),
                category=cat_obj,
                is_active=random.random() > 0.05,
            ))
            created_count += 1
            counter += 1

            if len(products_to_create) >= BATCH_SIZE:
                Product.objects.bulk_create(products_to_create)
                self.stdout.write(
                    f'  {existing_count + created_count}/{TOTAL} produits insérés...'
                )
                products_to_create = []

        if products_to_create:
            Product.objects.bulk_create(products_to_create)

        self.stdout.write(self.style.SUCCESS('100 000 produits cohérents créés avec succès !'))
