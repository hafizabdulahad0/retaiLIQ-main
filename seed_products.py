# seed_ten_products.py

from app import app
from models import db, Store, Product

products = [
    {
        "name": "Eco-Friendly Bamboo Toothbrush",
        "price": 4.99,
        "max_discount": 0.50,
        "description": "Biodegradable bamboo handle, soft nylon bristles.",
        "justification": "Sustainable choice for daily dental care.",
        "other_discounts": "5% off bundle of 3+"
    },
    {
        "name": "Smartphone Adjustable Stand",
        "price": 19.99,
        "max_discount": 2.00,
        "description": "360° rotation, holds phone/tablet at any angle.",
        "justification": "Perfect for video calls and recipes.",
        "other_discounts": "Holiday coupon: 10%"
    },
    {
        "name": "Wireless Charging Pad",
        "price": 29.99,
        "max_discount": 3.00,
        "description": "Qi-certified, fast charge up to 10W.",
        "justification": "Eliminate tangled cables.",
        "other_discounts": "Free shipping"
    },
    {
        "name": "Portable Mini Bluetooth Speaker",
        "price": 24.99,
        "max_discount": 2.50,
        "description": "Compact, 6-hour battery life, built-in mic.",
        "justification": "Bring music anywhere.",
        "other_discounts": ""
    },
    {
        "name": "Insulated Stainless Steel Tumbler",
        "price": 14.99,
        "max_discount": 1.50,
        "description": "Keeps drinks hot/cold for 8h, leak-proof lid.",
        "justification": "Double-wall vacuum insulation.",
        "other_discounts": "10% off orders $50+"
    },
    {
        "name": "LED Clip-On Book Light",
        "price": 12.99,
        "max_discount": 1.00,
        "description": "Adjustable arm, 3 brightness levels.",
        "justification": "Perfect for reading at night.",
        "other_discounts": ""
    },
    {
        "name": "Reusable Canvas Tote Bag",
        "price": 9.99,
        "max_discount": 1.00,
        "description": "Heavy-duty cotton, eco-friendly printing.",
        "justification": "Durable and washable.",
        "other_discounts": ""
    },
    {
        "name": "Bamboo Charcoal Air Purifying Bag",
        "price": 7.99,
        "max_discount": 0.80,
        "description": "Natural odor absorber, lasts 2 years.",
        "justification": "Chemical-free home freshener.",
        "other_discounts": ""
    },
    {
        "name": "Silicone Baking Mats (Set of 2)",
        "price": 11.99,
        "max_discount": 1.20,
        "description": "Non-stick, easy-clean, oven-safe to 480°F.",
        "justification": "Reusable replacement for parchment.",
        "other_discounts": ""
    },
    {
        "name": "Foldable Laptop Stand",
        "price": 34.99,
        "max_discount": 3.50,
        "description": "Aluminum alloy, portable, ergonomic height.",
        "justification": "Prevents neck strain.",
        "other_discounts": "Bundle discount: 5%"
    },
]

with app.app_context():
    store = Store.query.first()
    if not store:
        print("❌ No store found! Create a store first.")
        exit(1)

    for data in products:
        p = Product(
            name=data["name"],
            price=data["price"],
            max_discount=data["max_discount"],
            description=data["description"],
            justification=data["justification"],
            other_discounts=data["other_discounts"],
            store_id=store.id
        )
        db.session.add(p)
    db.session.commit()
    print(f"✅ Seeded {len(products)} products into store '{store.name}'.")
