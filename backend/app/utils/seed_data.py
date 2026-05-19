"""
Realistic seed data for MongoDB.
Creates 50 users, 90 products across 6 categories, and 2000 weighted interactions.
Skips seeding if data already exists.
"""
import random
from datetime import datetime, timedelta
from pymongo.database import Database
from app.utils.auth import hash_password
from app.utils.logger import get_logger

logger = get_logger(__name__)

CATEGORIES = {
    "Electronics": {
        "brands": ["Sony", "Samsung", "Apple", "LG", "Bose", "JBL", "Anker", "Logitech"],
        "products": [
            ("Wireless Noise-Cancelling Headphones", "Premium noise cancellation, 30hr battery, foldable design",
             ["wireless", "noise-cancelling", "bluetooth", "audio", "premium", "headphones"]),
            ("4K OLED Smart TV 55\"", "4K OLED display with smart OS, HDR10+, Dolby Vision, built-in streaming",
             ["4k", "oled", "smart-tv", "hdr", "streaming", "television"]),
            ("Gaming Mechanical Keyboard", "RGB backlit, tactile switches, anti-ghosting, USB-C",
             ["gaming", "mechanical", "keyboard", "rgb", "peripherals", "computer"]),
            ("Portable Bluetooth Speaker", "360 sound, waterproof IP67, 12hr battery",
             ["bluetooth", "speaker", "portable", "waterproof", "audio", "outdoor"]),
            ("Smartwatch with Health Tracking", "Heart rate, SpO2, GPS, sleep tracking, 7-day battery",
             ["smartwatch", "fitness", "health", "gps", "wearable", "tracker"]),
            ("USB-C Hub 10-in-1", "HDMI 4K, 3x USB-A, SD card, Ethernet, 100W PD",
             ["usb-c", "hub", "accessories", "docking", "laptop", "productivity"]),
            ("Wireless Charging Pad", "15W fast charging, compatible with Qi devices",
             ["wireless", "charging", "qi", "accessories", "smartphone"]),
            ("Noise-Cancelling Earbuds", "ANC, 8hr battery, IPX4, transparency mode",
             ["earbuds", "noise-cancelling", "wireless", "audio", "compact"]),
            ("Action Camera 4K", "4K 60fps, EIS stabilization, waterproof, wide angle",
             ["camera", "action", "4k", "waterproof", "outdoor", "photography"]),
            ("Laptop Stand Adjustable", "Ergonomic 6-angle adjustable, aluminum",
             ["laptop", "stand", "ergonomic", "accessories", "aluminum", "office"]),
            ("Mechanical Gaming Mouse", "16000 DPI optical, RGB, programmable buttons",
             ["gaming", "mouse", "rgb", "precision", "peripherals"]),
            ("Webcam 4K Ultra HD", "4K 30fps, auto-focus, built-in mic, HDR, privacy cover",
             ["webcam", "4k", "streaming", "video-call", "home-office"]),
            ("Portable SSD 1TB", "NVMe, 1050MB/s read, USB-C, shock-resistant",
             ["ssd", "storage", "portable", "fast", "backup", "usb-c"]),
            ("Smart LED Strip Lights", "16M colors, voice control, music sync, app control",
             ["smart-home", "led", "lighting", "rgb", "voice-control"]),
            ("Wireless Ergonomic Mouse", "Bluetooth, vertical grip, 3 device pairing, 4-month battery",
             ["wireless", "mouse", "ergonomic", "office", "productivity"]),
        ],
    },
    "Books": {
        "brands": ["Penguin", "O'Reilly", "HarperCollins", "Simon & Schuster", "Wiley", "Packt"],
        "products": [
            ("Deep Learning with Python", "Comprehensive guide to deep learning using Keras and TensorFlow",
             ["machine-learning", "deep-learning", "python", "ai", "neural-networks"]),
            ("The Pragmatic Programmer", "Essential software development practices",
             ["programming", "software-engineering", "career", "best-practices"]),
            ("Clean Code", "A handbook of agile software craftsmanship",
             ["programming", "clean-code", "refactoring", "software-engineering"]),
            ("Designing Data-Intensive Applications", "Architecture of modern data systems",
             ["data-engineering", "distributed-systems", "databases", "backend"]),
            ("Atomic Habits", "Practical strategies for building good habits",
             ["self-help", "habits", "productivity", "psychology"]),
            ("System Design Interview", "Insider guide to system design questions",
             ["system-design", "interview", "backend", "architecture", "career"]),
            ("Python Crash Course", "Beginner-friendly introduction to Python",
             ["python", "programming", "beginner", "tutorial", "coding"]),
            ("The Lean Startup", "How entrepreneurs use continuous innovation",
             ["startup", "entrepreneurship", "business", "innovation"]),
            ("Introduction to Algorithms", "Comprehensive textbook on algorithms",
             ["algorithms", "data-structures", "computer-science", "programming"]),
            ("Thinking, Fast and Slow", "How two systems of thought shape decisions",
             ["psychology", "decision-making", "cognitive-science"]),
            ("Zero to One", "Notes on startups, or how to build the future",
             ["startup", "entrepreneurship", "technology", "business"]),
            ("FastAPI for Beginners", "Build modern APIs with Python and FastAPI",
             ["fastapi", "python", "api", "web-development", "backend"]),
            ("Data Science Handbook", "Field guide to data analysis and ML",
             ["data-science", "analytics", "python", "statistics"]),
            ("The Innovator's Dilemma", "Why great companies fail with disruption",
             ["business", "innovation", "technology", "strategy"]),
            ("The Art of War", "Ancient military treatise with modern applications",
             ["strategy", "business", "philosophy", "classic"]),
        ],
    },
    "Clothing": {
        "brands": ["Nike", "Adidas", "Levi's", "H&M", "Zara", "Uniqlo", "Puma"],
        "products": [
            ("Running Shoes Pro", "Lightweight, breathable mesh, cushioned sole",
             ["running", "shoes", "sports", "athletic", "lightweight"]),
            ("Slim Fit Jeans", "Stretch denim, slim fit, 5-pocket design",
             ["jeans", "denim", "casual", "slim-fit", "pants", "fashion"]),
            ("Performance Hoodie", "Moisture-wicking, fleece lined, zip-up",
             ["hoodie", "gym", "athletic", "fleece", "activewear"]),
            ("Casual Polo Shirt", "100% cotton pique, classic fit, ribbed collar",
             ["polo", "shirt", "casual", "cotton", "classic"]),
            ("Yoga Leggings High Waist", "4-way stretch, squat-proof, moisture-wicking",
             ["leggings", "yoga", "fitness", "womens", "activewear"]),
            ("Waterproof Hiking Jacket", "Gore-Tex membrane, 3-layer, packable",
             ["jacket", "hiking", "waterproof", "outdoor", "gore-tex"]),
            ("Classic White Sneakers", "Leather upper, rubber sole, minimalist design",
             ["sneakers", "shoes", "casual", "leather", "white"]),
            ("Compression Running Socks", "Graduated compression, moisture-wicking",
             ["socks", "running", "compression", "sports", "athletic"]),
            ("Formal Business Shirt", "100% cotton, non-iron, slim fit",
             ["shirt", "formal", "business", "office", "cotton"]),
            ("Lightweight Puffer Vest", "Recycled fill, packable, side pockets",
             ["vest", "puffer", "lightweight", "outdoor", "packable"]),
            ("Sports Shorts 2-in-1", "Inner compression layer, outer mesh",
             ["shorts", "sports", "running", "compression", "athletic"]),
            ("Knit Beanie Hat", "100% merino wool, ribbed texture",
             ["beanie", "hat", "wool", "winter", "accessories"]),
            ("Denim Jacket Classic", "100% cotton, button-front, vintage wash",
             ["jacket", "denim", "casual", "classic", "fashion"]),
            ("Anti-Odor Sports T-Shirt", "Silver ion technology, moisture-wicking",
             ["t-shirt", "sports", "anti-odor", "athletic", "performance"]),
            ("Thermal Base Layer", "Merino wool blend, moisture-wicking, lightweight",
             ["thermal", "base-layer", "wool", "hiking", "winter"]),
        ],
    },
    "Home & Kitchen": {
        "brands": ["Instant Pot", "KitchenAid", "Cuisinart", "Dyson", "Ninja", "Breville"],
        "products": [
            ("Air Fryer 5.8QT", "Digital display, 8 presets, non-stick basket, 1700W",
             ["air-fryer", "kitchen", "cooking", "healthy", "appliance"]),
            ("Instant Pot Duo 7-in-1", "Pressure cooker, slow cooker, rice cooker, 6qt",
             ["instant-pot", "pressure-cooker", "kitchen", "cooking", "multi-cooker"]),
            ("Robot Vacuum Cleaner", "2500Pa suction, laser navigation, app control",
             ["vacuum", "robot", "smart-home", "cleaning", "autonomous"]),
            ("Stand Mixer 5QT", "575W motor, 10 speeds, tilt-head",
             ["mixer", "baking", "kitchen", "stand-mixer", "appliance"]),
            ("Coffee Maker with Grinder", "Built-in burr grinder, 12-cup, programmable",
             ["coffee", "kitchen", "grinder", "programmable", "brewing"]),
            ("Non-Stick Cookware Set 10-Piece", "Hard-anodized aluminum, ceramic coating",
             ["cookware", "non-stick", "kitchen", "pots", "pans"]),
            ("Smart Air Purifier", "True HEPA, 4-stage filtration, auto mode, 500 sqft",
             ["air-purifier", "hepa", "smart-home", "health", "filter"]),
            ("Sous Vide Precision Cooker", "1200W, accurate to 0.1°C, Wi-Fi enabled",
             ["sous-vide", "cooking", "precision", "kitchen", "gourmet"]),
            ("Cast Iron Skillet 12\"", "Pre-seasoned, even heat, oven-safe",
             ["cast-iron", "skillet", "cooking", "kitchen", "durable"]),
            ("Electric Kettle 1.7L", "Variable temperature control, 60-min keep warm",
             ["kettle", "electric", "kitchen", "tea", "coffee"]),
            ("Knife Set with Block", "German stainless steel, 15-piece, hardwood block",
             ["knives", "kitchen", "cooking", "professional", "stainless-steel"]),
            ("Blender High-Performance", "1800W, 64oz container, self-cleaning",
             ["blender", "kitchen", "smoothies", "high-performance", "appliance"]),
            ("Digital Kitchen Scale", "0.1g precision, tare function, LCD display",
             ["scale", "kitchen", "baking", "precision", "digital"]),
            ("Bamboo Cutting Board Set", "3-piece set, juice grooves, non-slip feet",
             ["cutting-board", "bamboo", "kitchen", "eco-friendly"]),
            ("Toaster Oven with Air Fry", "6-in-1 function, 26L capacity, convection",
             ["toaster-oven", "air-fry", "kitchen", "multi-function", "baking"]),
        ],
    },
    "Sports & Outdoors": {
        "brands": ["Coleman", "Garmin", "TRX", "Bowflex", "CamelBak", "Black Diamond"],
        "products": [
            ("Adjustable Dumbbell Set", "Replaces 15 weights, 5-52.5 lbs, quick-change dial",
             ["dumbbells", "weights", "gym", "fitness", "strength-training", "home-gym"]),
            ("Yoga Mat Premium", "6mm thick, non-slip, alignment lines, eco-friendly TPE",
             ["yoga", "mat", "fitness", "non-slip", "eco-friendly", "exercise"]),
            ("Resistance Bands Set", "5 resistance levels, door anchor, handles, ankle straps",
             ["resistance-bands", "fitness", "workout", "portable", "strength"]),
            ("Camping Tent 4-Person", "Waterproof 3000mm, quick setup, 2-door",
             ["tent", "camping", "outdoor", "waterproof", "family"]),
            ("GPS Running Watch", "GPS, heart rate, VO2 max, 14-day battery",
             ["watch", "gps", "running", "fitness", "sports", "heart-rate"]),
            ("Foam Roller Deep Tissue", "High-density EVA, textured surface, 13-inch",
             ["foam-roller", "recovery", "fitness", "massage", "flexibility"]),
            ("Hiking Backpack 50L", "Rain cover, hip belt pockets, hydration compatible",
             ["backpack", "hiking", "outdoor", "50l", "travel", "camping"]),
            ("Jump Rope Speed Cable", "Adjustable length, ball-bearing handles",
             ["jump-rope", "cardio", "fitness", "speed", "boxing"]),
            ("Kettlebell Set Adjustable", "Replaces 6 kettlebells, 8-40 lbs",
             ["kettlebell", "weights", "gym", "strength-training", "fitness"]),
            ("Trekking Poles Carbon Fiber", "Carbon fiber, shock absorbing, foldable",
             ["trekking-poles", "hiking", "outdoor", "carbon-fiber"]),
            ("Hydration Pack 2L", "2L reservoir, insulated tube, multiple pockets",
             ["hydration", "backpack", "running", "cycling", "outdoor"]),
            ("Pull-Up Bar Doorframe", "No screws, 300lb capacity, multiple grip positions",
             ["pull-up-bar", "gym", "strength", "home-gym", "fitness"]),
            ("Sleeping Bag -10C", "Down fill, mummy shape, compression sack",
             ["sleeping-bag", "camping", "outdoor", "down", "cold-weather"]),
            ("Exercise Bike Stationary", "Magnetic resistance, 22 levels, LCD display",
             ["exercise-bike", "cardio", "indoor", "cycling", "fitness"]),
            ("Climbing Harness", "UIAA certified, padded waist, 4 gear loops",
             ["climbing", "harness", "outdoor", "safety", "adventure"]),
        ],
    },
    "Beauty & Personal Care": {
        "brands": ["Dyson", "Philips", "Neutrogena", "Olay", "L'Oreal", "Foreo", "Tatcha"],
        "products": [
            ("Hair Dryer Ionic 1875W", "Ionic technology, 3 heat settings, concentrator nozzle",
             ["hair-dryer", "ionic", "beauty", "hair-care", "styling"]),
            ("Electric Face Cleanser", "Sonic vibration, silicone head, 3 modes, waterproof",
             ["face-cleanser", "beauty", "skincare", "sonic", "electric"]),
            ("Vitamin C Serum 20%", "20% L-ascorbic acid, hyaluronic acid, anti-aging",
             ["serum", "vitamin-c", "skincare", "anti-aging", "brightening"]),
            ("Electric Shaver Men", "Flex head, wet/dry use, 60min runtime, fast charge",
             ["shaver", "electric", "men", "grooming", "beard"]),
            ("Retinol Night Cream", "0.3% retinol, niacinamide, peptides",
             ["night-cream", "retinol", "skincare", "anti-aging", "moisturizer"]),
            ("Hair Straightener Titanium", "Titanium plates, 450F max, digital display",
             ["straightener", "hair", "beauty", "titanium", "styling"]),
            ("Sunscreen SPF 50+ Mineral", "Zinc oxide 20%, reef-safe, water-resistant",
             ["sunscreen", "spf", "skincare", "sun-protection", "mineral"]),
            ("Electric Toothbrush Sonic", "40000 strokes/min, 5 modes, pressure sensor",
             ["toothbrush", "electric", "sonic", "dental", "oral-care"]),
            ("Hyaluronic Acid Moisturizer", "3-weight HA, ceramides, niacinamide, oil-free",
             ["moisturizer", "hyaluronic-acid", "skincare", "hydration"]),
            ("Perfume Floral Eau de Parfum", "Bergamot, jasmine, sandalwood, 50ml",
             ["perfume", "fragrance", "beauty", "floral", "feminine"]),
            ("Jade Roller & Gua Sha Set", "100% natural jade, double-ended roller",
             ["jade-roller", "gua-sha", "skincare", "beauty", "facial-massage"]),
            ("Hair Growth Serum", "Biotin, caffeine, peptides, scalp treatment",
             ["hair-growth", "serum", "beauty", "hair-care", "scalp"]),
            ("Nail Polish Set 24 Colors", "Long-lasting, chip-resistant, quick-dry, vegan",
             ["nail-polish", "beauty", "nails", "colors", "set"]),
            ("Face Mask Sheet Set 20pk", "Hyaluronic acid, collagen, vitamin E, 20 varieties",
             ["face-mask", "skincare", "sheet-mask", "beauty", "hydrating"]),
            ("Lip Balm SPF 30 Set", "SPF 30, beeswax, vitamin E, shea butter, 6-pack",
             ["lip-balm", "spf", "beauty", "lip-care", "moisture"]),
        ],
    },
}

LOCATIONS = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX",
             "Phoenix, AZ", "San Francisco, CA", "Seattle, WA", "Denver, CO",
             "Nashville, TN", "Austin, TX", "Dallas, TX", "Boston, MA"]

FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
               "Isabella", "Jack", "Katherine", "Liam", "Mia", "Noah", "Olivia", "Peter",
               "Quinn", "Rachel", "Samuel", "Tara", "Uma", "Victor", "Wendy", "Xander",
               "Yara", "Zoe", "Aaron", "Beth", "Carlos", "Dena", "Ethan", "Fiona",
               "George", "Hannah", "Ivan", "Julia", "Kevin", "Laura", "Mike", "Nancy",
               "Oscar", "Paula", "Robert", "Sara", "Thomas", "Ursula", "Vincent", "Wanda",
               "Xavier", "Yvonne"]

PRICE_RANGES = {
    "Electronics": (29.99, 899.99), "Books": (9.99, 59.99),
    "Clothing": (14.99, 249.99), "Home & Kitchen": (19.99, 399.99),
    "Sports & Outdoors": (14.99, 499.99), "Beauty & Personal Care": (8.99, 199.99),
}


def seed_database(db) -> None:
    """Seed MongoDB with realistic test data. Skips if data already exists."""
    if db.products.count_documents({}) > 0:
        logger.info("Database products already seeded, skipping.")
        return

    logger.info("Seeding MongoDB with realistic data...")
    random.seed(42)
    hashed_pw = hash_password("password123")

    # ── Users ─────────────────────────────────────────────────────────────────
    seed_users = list(db.users.find({"is_seed": True}))
    if len(seed_users) == 0:
        user_docs = []
        for i, name in enumerate(FIRST_NAMES[:50]):
            domain = random.choice(["gmail.com", "yahoo.com", "outlook.com"])
            user_docs.append({
                "name": name,
                "email": f"{name.lower()}.{i+1}@{domain}",
                "password_hash": hashed_pw,
                "age": random.randint(18, 65),
                "location": random.choice(LOCATIONS),
                "created_at": datetime.utcnow() - timedelta(days=random.randint(30, 365)),
                "is_seed": True
            })
        result = db.users.insert_many(user_docs)
        user_ids = [str(uid) for uid in result.inserted_ids]
        logger.info(f"Created {len(user_ids)} seed users")
    else:
        user_ids = [str(doc["_id"]) for doc in seed_users]
        logger.info(f"Found {len(user_ids)} existing seed users")

    # ── Products ───────────────────────────────────────────────────────────────
    product_docs = []
    for category, data in CATEGORIES.items():
        low, high = PRICE_RANGES[category]
        for name, description, features in data["products"]:
            brand = random.choice(data["brands"])
            product_docs.append({
                "name": f"{brand} {name}",
                "category": category,
                "price": round(random.uniform(low, high), 2),
                "description": description,
                "features": features,
                "brand": brand,
                "rating": round(random.uniform(3.2, 5.0), 1),
                "num_reviews": random.randint(50, 5000),
                "image_url": None,
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 300)),
            })
    result = db.products.insert_many(product_docs)
    product_ids = [str(pid) for pid in result.inserted_ids]
    logger.info(f"Created {len(product_ids)} products")

    # ── Interactions ────────────────────────────────────────────────────────────
    interaction_types = ["view", "add_to_cart", "purchase"]
    weights = [0.6, 0.25, 0.15]

    # User category affinities
    all_cats = list(CATEGORIES.keys())
    user_affinities = {uid: random.sample(all_cats, random.randint(1, 3)) for uid in user_ids}

    # Group products by category
    cat_product_map: dict[str, list[str]] = {}
    for cat in CATEGORIES:
        # Get product IDs for this category from the inserted products
        cat_product_map[cat] = []

    for doc in db.products.find({}, {"_id": 1, "category": 1}):
        cat_product_map.setdefault(doc["category"], []).append(str(doc["_id"]))

    interactions = []
    for _ in range(2000):
        uid = random.choice(user_ids)
        affinity_cats = user_affinities[uid]
        if random.random() < 0.7:
            category = random.choice(affinity_cats)
            pids = cat_product_map.get(category, product_ids)
        else:
            pids = product_ids
        pid = random.choice(pids)
        itype = random.choices(interaction_types, weights=weights, k=1)[0]
        rating = None
        if itype in ("add_to_cart", "purchase") and random.random() < 0.5:
            rating = round(random.uniform(2.5, 5.0), 1)
        interactions.append({
            "user_id": uid,
            "product_id": pid,
            "interaction_type": itype,
            "rating": rating,
            "timestamp": datetime.utcnow() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
            ),
        })
    db.interactions.insert_many(interactions)
    logger.info(f"Created {len(interactions)} interactions — seeding complete!")
