import os
import sys
import random
from datetime import datetime, timedelta

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.database import connect_to_mongo, close_mongo
from app.utils.logger import get_logger

logger = get_logger(__name__)

NEW_CATEGORIES = {
    "Mobiles": {
        "brands": ["Apple", "Samsung", "Google", "OnePlus", "Xiaomi"],
        "products": [
            ("Pro Max Ultra", "6.7-inch OLED, 1TB storage, 100x zoom camera", ["smartphone", "mobile", "flagship", "camera", "oled"]),
            ("Galaxy Fold", "Foldable 7.6-inch screen, 12GB RAM, stylus support", ["smartphone", "foldable", "mobile", "stylus"]),
            ("Pixel Pro", "Computational photography, pure Android, 50MP camera", ["smartphone", "camera", "android", "mobile"]),
            ("Nord Lite", "Affordable mid-range, 90Hz display, 5G ready", ["smartphone", "affordable", "5g", "mobile"]),
            ("Gaming Phone Black", "144Hz screen, built-in triggers, cooling fan, 16GB RAM", ["smartphone", "gaming", "mobile", "144hz"]),
            ("Mini Series", "Compact 5.4-inch display, flagship chip", ["smartphone", "compact", "mobile", "flagship"]),
            ("Note Series", "Large display, embedded stylus, productivity focused", ["smartphone", "stylus", "productivity", "mobile"]),
            ("Budget 5G", "Cheap 5G phone, 5000mAh battery", ["smartphone", "budget", "5g", "battery"]),
            ("Camera Phone Pro", "1-inch sensor, Leica lenses, professional photography", ["smartphone", "camera", "pro", "photography"]),
            ("Rugged Phone", "Drop-proof, waterproof, massive battery, thermal camera", ["smartphone", "rugged", "outdoor", "waterproof"]),
            ("Flip Phone", "Clamshell foldable design, pocket-sized", ["smartphone", "foldable", "flip", "compact"]),
            ("Lite Edition", "Lightweight, sleek design, dual camera", ["smartphone", "lightweight", "sleek", "budget"]),
            ("Creator Phone", "Vlog-centric, gimbal stabilization, dual front cameras", ["smartphone", "vlog", "video", "creator"]),
            ("Enterprise Phone", "Hardware encryption, secure boot, enterprise software", ["smartphone", "security", "enterprise", "business"]),
            ("Entry Level", "Basic smartphone functionality, large battery, affordable", ["smartphone", "basic", "affordable", "budget"])
        ]
    },
    "Laptops": {
        "brands": ["Dell", "Apple", "Lenovo", "HP", "ASUS"],
        "products": [
            ("XPS 15", "15-inch 4K OLED, 32GB RAM, 1TB SSD", ["laptop", "productivity", "4k", "oled", "premium"]),
            ("MacBook Pro 16", "M3 Max chip, 64GB RAM, Liquid Retina XDR", ["laptop", "creative", "premium", "mac", "professional"]),
            ("ThinkPad X1", "Carbon fiber, legendary keyboard, business class", ["laptop", "business", "thinkpad", "lightweight"]),
            ("Spectre x360", "Convertible 2-in-1, stylus included, OLED", ["laptop", "convertible", "touchscreen", "2-in-1"]),
            ("ROG Zephyrus", "Gaming laptop, RTX 4080, 240Hz display", ["laptop", "gaming", "rtx", "high-refresh", "asus"]),
            ("Chromebook Flip", "Lightweight ChromeOS, long battery life, 2-in-1", ["laptop", "chromebook", "education", "budget"]),
            ("ZenBook Duo", "Dual-screen laptop, creator focused", ["laptop", "dual-screen", "creator", "innovation"]),
            ("Legion Pro 5", "Mid-range gaming, Ryzen 7, RTX 4060", ["laptop", "gaming", "ryzen", "mid-range"]),
            ("MacBook Air", "Fanless design, M3 chip, incredibly thin", ["laptop", "thin", "lightweight", "fanless", "mac"]),
            ("Pavilion Aero", "Under 1kg, magnesium chassis, affordable", ["laptop", "lightweight", "budget", "portable"]),
            ("TUF Gaming", "Durable gaming laptop, military-grade standards", ["laptop", "gaming", "durable", "budget"]),
            ("Surface Laptop", "PixelSense touchscreen, Alcantara keyboard", ["laptop", "touchscreen", "premium", "windows"]),
            ("Latitude 7000", "Enterprise security, smart card reader, vPro", ["laptop", "enterprise", "security", "business"]),
            ("Swift 3", "Evo platform, Intel Core i5, long battery", ["laptop", "productivity", "evo", "budget"]),
            ("Creator Studio", "OLED calibrated display, NVIDIA Studio drivers", ["laptop", "creator", "nvidia-studio", "color-accurate"])
        ]
    },
    "Clothes": {
        "brands": ["Nike", "Levi's", "Zara", "H&M", "Uniqlo", "Patagonia"],
        "products": [
            ("Graphic T-Shirt", "100% cotton, relaxed fit, original graphic", ["clothing", "t-shirt", "casual", "cotton"]),
            ("Slim Fit Jeans", "Stretch denim, 5-pocket styling", ["clothing", "jeans", "denim", "slim-fit"]),
            ("Winter Parka", "Water-resistant, faux fur trim, heavily insulated", ["clothing", "jacket", "winter", "parka", "warm"]),
            ("Summer Shorts", "Lightweight linen blend, drawstring waist", ["clothing", "shorts", "summer", "linen", "casual"]),
            ("Fleece Pullover", "Quarter-zip, soft fleece, outdoor ready", ["clothing", "fleece", "pullover", "outdoor", "warm"]),
            ("Button-Down Shirt", "Oxford cotton, tailored fit, versatile", ["clothing", "shirt", "button-down", "formal", "office"]),
            ("Yoga Leggings", "High-waisted, moisture-wicking, 4-way stretch", ["clothing", "leggings", "yoga", "activewear"]),
            ("Denim Jacket", "Classic trucker style, vintage wash", ["clothing", "jacket", "denim", "classic", "casual"]),
            ("Cashmere Sweater", "100% pure cashmere, crew neck, ultra-soft", ["clothing", "sweater", "cashmere", "premium", "winter"]),
            ("Athletic Joggers", "Tapered fit, zip pockets, breathable fabric", ["clothing", "joggers", "athletic", "sports", "comfortable"])
        ]
    },
    "Shoes": {
        "brands": ["Nike", "Adidas", "Puma", "Reebok", "New Balance"],
        "products": [
            ("Air Running Shoes", "Air cushioning, breathable mesh, lightweight", ["shoes", "running", "athletic", "sneakers"]),
            ("Classic Leather Sneakers", "Retro design, full leather upper, casual", ["shoes", "sneakers", "leather", "casual", "retro"]),
            ("Trail Running Shoes", "Aggressive grip, waterproof Gore-Tex, durable", ["shoes", "trail", "running", "outdoor", "waterproof"]),
            ("Basketball Shoes", "High-top, ankle support, impact cushioning", ["shoes", "basketball", "sports", "high-top"]),
            ("Slip-On Loafers", "Suede, memory foam insole, smart-casual", ["shoes", "loafers", "casual", "slip-on", "suede"]),
            ("Weightlifting Shoes", "Flat solid sole, elevated heel, secure strap", ["shoes", "weightlifting", "gym", "fitness"]),
            ("Winter Boots", "Insulated, waterproof, faux-fur lining", ["shoes", "boots", "winter", "waterproof", "warm"]),
            ("Skate Shoes", "Vulcanized sole, canvas upper, durable", ["shoes", "skate", "casual", "canvas", "sneakers"])
        ]
    },
    "Watches": {
        "brands": ["Apple", "Garmin", "Casio", "Seiko", "Fossil"],
        "products": [
            ("Ultra Smartwatch", "Titanium case, cellular, precision dual-frequency GPS", ["watch", "smartwatch", "fitness", "gps", "premium"]),
            ("G-Shock Digital", "Shock-resistant, 200M water resistance, solar powered", ["watch", "digital", "rugged", "water-resistant", "casio"]),
            ("Automatic Diver Watch", "Stainless steel, automatic movement, luminous hands", ["watch", "analog", "diver", "automatic", "seiko"]),
            ("Fitness Tracker Band", "Slim design, heart rate monitor, sleep tracking", ["watch", "fitness-tracker", "wearable", "health"]),
            ("Chronograph Leather Watch", "Three sub-dials, genuine leather strap, quartz", ["watch", "analog", "chronograph", "leather", "formal"]),
            ("Hybrid Smartwatch", "Analog hands with hidden e-ink display, notifications", ["watch", "hybrid", "smartwatch", "e-ink"]),
            ("Running GPS Watch", "Advanced running metrics, VO2 max, music storage", ["watch", "gps", "running", "sports"])
        ]
    },
    "Bags": {
        "brands": ["Samsonite", "Herschel", "North Face", "Jansport", "Osprey"],
        "products": [
            ("Classic Backpack", "Laptop sleeve, front pocket, padded straps", ["bag", "backpack", "school", "casual"]),
            ("Hiking Daypack", "Hydration compatible, waist belt, breathable mesh", ["bag", "backpack", "hiking", "outdoor"]),
            ("Hard-shell Suitcase", "Carry-on size, spinner wheels, TSA lock", ["bag", "luggage", "travel", "suitcase"]),
            ("Canvas Messenger Bag", "Vintage style, multiple compartments, cross-body", ["bag", "messenger", "canvas", "work", "vintage"]),
            ("Duffel Bag", "Water-resistant, shoe compartment, gym ready", ["bag", "duffel", "gym", "travel", "sports"]),
            ("Leather Tote", "Premium leather, large capacity, elegant", ["bag", "tote", "leather", "women", "fashion"])
        ]
    },
    "Toys": {
        "brands": ["Lego", "Hasbro", "Mattel", "Fisher-Price", "Nerf"],
        "products": [
            ("Creator Space Shuttle", "1200 piece building set, realistic details", ["toy", "building-blocks", "lego", "space", "kids"]),
            ("Motorized Blaster", "Fully automatic, 50-dart drum, high speed", ["toy", "blaster", "nerf", "action", "outdoor"]),
            ("Classic Board Game", "Property trading game, family fun, new tokens", ["toy", "board-game", "family", "multiplayer"]),
            ("RC Off-Road Truck", "4WD, 2.4GHz remote, suspension, fast speed", ["toy", "rc-car", "remote-control", "outdoor"]),
            ("Educational Toddler Set", "Shape sorting, colors, sounds, safe materials", ["toy", "toddler", "educational", "learning"]),
            ("Action Figure Collector's Edition", "Highly articulated, premium paint, accessories", ["toy", "action-figure", "collectible", "comic"])
        ]
    }
}

PRICE_RANGES = {
    "Mobiles": (199.99, 1299.99),
    "Laptops": (399.99, 2999.99),
    "Clothes": (19.99, 199.99),
    "Shoes": (49.99, 249.99),
    "Watches": (49.99, 899.99),
    "Bags": (29.99, 299.99),
    "Toys": (9.99, 149.99),
}

def append_seed_data():
    db = connect_to_mongo()
    logger.info("Appending new seed data for expanded categories...")
    random.seed(123)

    users = list(db.users.find({}, {"_id": 1}))
    if not users:
        logger.error("No users found! Please run the original seed_data.py first.")
        close_mongo()
        return

    user_ids = [str(u["_id"]) for u in users]

    # Generate and Upsert Products
    new_product_ids = []
    product_docs = []
    
    for category, data in NEW_CATEGORIES.items():
        low, high = PRICE_RANGES[category]
        for name, description, features in data["products"]:
            # Generate one product for each brand in the category to multiply data
            for brand in data["brands"]:
                # Introduce slight variation in price
                price = round(random.uniform(low, high), 2)
                product_name = f"{brand} {name}"
                
                doc = {
                    "name": product_name,
                    "category": category,
                    "price": price,
                    "description": description,
                    "features": features,
                    "brand": brand,
                    "rating": round(random.uniform(3.5, 5.0), 1),
                    "num_reviews": random.randint(10, 2000),
                    "image_url": None,
                    "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 100)),
                }
                
                # Upsert into MongoDB
                result = db.products.update_one(
                    {"name": product_name},
                    {"$set": doc},
                    upsert=True
                )
                
                # Fetch it to get the ID
                inserted_doc = db.products.find_one({"name": product_name})
                new_product_ids.append(str(inserted_doc["_id"]))

    logger.info(f"Upserted and retrieved {len(new_product_ids)} new products.")

    # Generate interactions for the NEW products so ML models pick them up
    interactions = []
    interaction_types = ["view", "add_to_cart", "purchase"]
    weights = [0.6, 0.25, 0.15]

    for _ in range(5000): # 5000 new interactions
        uid = random.choice(user_ids)
        pid = random.choice(new_product_ids)
        itype = random.choices(interaction_types, weights=weights, k=1)[0]
        
        rating = None
        if itype in ("add_to_cart", "purchase") and random.random() < 0.5:
            rating = round(random.uniform(3.0, 5.0), 1)
            
        interactions.append({
            "user_id": uid,
            "product_id": pid,
            "interaction_type": itype,
            "rating": rating,
            "timestamp": datetime.utcnow() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
            ),
        })

    # Insert interactions (no upsert needed here, just bulk insert new history)
    db.interactions.insert_many(interactions)
    logger.info(f"Appended {len(interactions)} new interactions.")

    close_mongo()
    logger.info("Append seed data script complete!")

if __name__ == "__main__":
    append_seed_data()
