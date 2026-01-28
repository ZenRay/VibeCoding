#!/usr/bin/env python3
"""
Generate sample data for small test database
"""

import random
from datetime import datetime, timedelta


# Generate 50 customers
def generate_customers():
    first_names = [
        "John",
        "Jane",
        "Bob",
        "Alice",
        "Charlie",
        "Diana",
        "Edward",
        "Fiona",
        "George",
        "Hannah",
    ]
    last_names = [
        "Doe",
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Davis",
        "Miller",
        "Wilson",
        "Moore",
        "Taylor",
    ]
    cities = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
    ]

    with open("02_data_customers.sql", "w") as f:
        f.write("-- Customer data\n")
        f.write(
            "INSERT INTO customers (email, first_name, last_name, phone, city, country, created_at, is_active) VALUES\n"
        )

        values = []
        for i in range(50):
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            email = f"{fname.lower()}.{lname.lower()}{i}@email.com"
            phone = f"555-{random.randint(1000,9999)}"
            city = random.choice(cities)
            created = datetime(2024, random.randint(1, 12), random.randint(1, 28))
            is_active = random.choice([True, True, True, False])  # 75% active

            values.append(
                f"('{email}', '{fname}', '{lname}', '{phone}', '{city}', 'USA', '{created}', {is_active})"
            )

        f.write(",\n".join(values) + ";\n")


# Generate 100 products
def generate_products():
    categories = {
        "Electronics": [
            "Headphones",
            "Smart Watch",
            "Charger",
            "Mouse",
            "Keyboard",
            "Webcam",
            "USB Hub",
            "Laptop Stand",
        ],
        "Home": [
            "Water Bottle",
            "Pan Set",
            "Kettle",
            "Knife Set",
            "Coffee Maker",
            "Blender",
            "Vacuum",
            "Air Fryer",
        ],
        "Clothing": [
            "T-Shirt",
            "Yoga Pants",
            "Jeans",
            "Hoodie",
            "Shoes",
            "Jacket",
            "Belt",
            "Sneakers",
        ],
        "Books": [
            "Programming Guide",
            "Cookbook",
            "Novel",
            "Biography",
            "Self-Help",
            "Picture Book",
        ],
        "Sports": [
            "Yoga Mat",
            "Dumbbells",
            "Resistance Bands",
            "Jump Rope",
            "Basketball",
            "Soccer Ball",
        ],
    }

    with open("03_data_products.sql", "w") as f:
        f.write("-- Product data\n")
        f.write(
            "INSERT INTO products (sku, name, description, price, stock_quantity, category, is_available) VALUES\n"
        )

        values = []
        for cat, items in categories.items():
            for i, item in enumerate(items):
                sku = f"{cat[:4].upper()}-{i+1:03d}"
                price = round(random.uniform(9.99, 299.99), 2)
                stock = random.randint(10, 300)
                values.append(
                    f"('{sku}', '{item}', 'Quality {item.lower()}', {price}, {stock}, '{cat}', true)"
                )

        f.write(",\n".join(values) + ";\n")


# Generate orders and items
def generate_orders():
    with open("04_data_orders.sql", "w") as f:
        f.write("-- Orders and order items\n")
        f.write(
            "INSERT INTO orders (customer_id, order_date, status, total_amount, payment_method) VALUES\n"
        )

        order_values = []
        statuses = ["delivered", "delivered", "shipped", "processing", "pending", "cancelled"]
        payments = ["credit_card", "paypal", "debit_card", "stripe"]

        for i in range(150):
            cust_id = random.randint(1, 50)
            order_date = datetime(2025, 12, 1) + timedelta(days=random.randint(0, 58))
            status = random.choice(statuses)
            total = round(random.uniform(50, 500), 2)
            payment = random.choice(payments)

            order_values.append(f"({cust_id}, '{order_date}', '{status}', {total}, '{payment}')")

        f.write(",\n".join(order_values) + ";\n\n")

        # Order items
        f.write("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES\n")
        item_values = []

        for order_id in range(1, 151):
            num_items = random.randint(1, 5)
            for _ in range(num_items):
                prod_id = random.randint(1, 48)  # Total products
                quantity = random.randint(1, 3)
                price = round(random.uniform(9.99, 199.99), 2)
                item_values.append(f"({order_id}, {prod_id}, {quantity}, {price})")

        f.write(",\n".join(item_values) + ";\n")


# Generate reviews
def generate_reviews():
    titles = [
        "Great product!",
        "Love it",
        "Not bad",
        "Excellent quality",
        "Would buy again",
        "Disappointed",
        "Amazing!",
    ]
    comments = [
        "Really happy with this purchase",
        "Quality is good",
        "Works as expected",
        "Perfect for my needs",
    ]

    with open("05_data_reviews.sql", "w") as f:
        f.write("-- Reviews\n")
        f.write(
            "INSERT INTO reviews (product_id, customer_id, rating, title, comment, created_at) VALUES\n"
        )

        values = []
        used_pairs = set()

        for _ in range(200):
            prod_id = random.randint(1, 48)
            cust_id = random.randint(1, 50)

            if (prod_id, cust_id) in used_pairs:
                continue
            used_pairs.add((prod_id, cust_id))

            rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 30, 40])[
                0
            ]  # Skew positive
            title = random.choice(titles)
            comment = random.choice(comments)
            created = datetime(2026, 1, random.randint(1, 28))

            values.append(f"({prod_id}, {cust_id}, {rating}, '{title}', '{comment}', '{created}')")

        f.write(",\n".join(values) + ";\n")


if __name__ == "__main__":
    print("Generating small database data files...")
    generate_customers()
    print("✓ Customers generated")
    generate_products()
    print("✓ Products generated")
    generate_orders()
    print("✓ Orders generated")
    generate_reviews()
    print("✓ Reviews generated")
    print("\nDone! Run these files in order after 01_schema.sql")
