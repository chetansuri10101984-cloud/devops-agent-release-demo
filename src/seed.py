"""Seed sample data for demo purposes."""

import uuid
from datetime import datetime, timedelta
import random


def seed_sample_data(orders_db):
    """Populate the in-memory store with realistic sample orders."""
    customers = [
        ("Alice Johnson", "alice.johnson@email.com"),
        ("Bob Smith", "bob.smith@company.co"),
        ("Carol Williams", "carol.w@example.org"),
        ("David Brown", "david.brown@mail.com"),
        ("Emma Davis", "emma.d@techcorp.io"),
        ("Frank Miller", "frank.miller@startup.com"),
        ("Grace Lee", "grace.lee@enterprise.net"),
        ("Henry Wilson", "henry.w@agency.co"),
    ]

    products = [
        ("Wireless Keyboard", 79.99),
        ("USB-C Hub", 45.00),
        ("Monitor Stand", 129.95),
        ("Mechanical Keyboard", 149.99),
        ("Webcam HD", 89.00),
        ("Desk Lamp", 34.99),
        ("Mouse Pad XL", 24.95),
        ("Laptop Stand", 59.99),
        ("Cable Management Kit", 19.99),
        ("Noise Cancelling Headphones", 249.99),
    ]

    statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    status_weights = [3, 2, 2, 3, 5, 1]

    for i in range(15):
        customer = random.choice(customers)
        num_items = random.randint(1, 4)
        items = []
        for _ in range(num_items):
            product = random.choice(products)
            items.append({
                "product": product[0],
                "quantity": random.randint(1, 3),
                "price": product[1],
            })

        total = sum(item["price"] * item["quantity"] for item in items)
        created = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        status = random.choices(statuses, weights=status_weights, k=1)[0]

        order_id = str(uuid.uuid4())
        orders_db[order_id] = {
            "order_id": order_id,
            "customer_name": customer[0],
            "customer_email": customer[1],
            "items": items,
            "shipping_address": f"{random.randint(100, 9999)} Main St, City, ST {random.randint(10000, 99999)}",
            "total_amount": round(total, 2),
            "status": status,
            "created_at": created.isoformat(),
            "updated_at": (created + timedelta(hours=random.randint(1, 48))).isoformat(),
        }

    print(f"  Seeded {len(orders_db)} sample orders")
