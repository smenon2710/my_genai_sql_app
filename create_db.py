import sqlite3
from datetime import datetime
import random

# Make sure you're saving the DB in the right folder
conn = sqlite3.connect("schema/sample_data.db")
cursor = conn.cursor()

# Drop existing tables if re-running
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS orders")

# Create tables
cursor.execute("""
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT,
    category TEXT
)
""")

cursor.execute("""
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    product_id INTEGER,
    quantity INTEGER,
    revenue REAL,
    region TEXT,
    order_date TEXT,
    FOREIGN KEY(product_id) REFERENCES products(product_id)
)
""")

# Sample products
products = [
    (1, 'Laptop', 'Electronics'),
    (2, 'Smartphone', 'Electronics'),
    (3, 'Headphones', 'Accessories'),
    (4, 'Desk Chair', 'Furniture'),
    (5, 'Monitor', 'Electronics'),
]

cursor.executemany("INSERT INTO products VALUES (?, ?, ?)", products)

# Random orders
regions = ['North', 'South', 'East', 'West']
orders = []

for i in range(1, 101):
    product = random.choice(products)
    quantity = random.randint(1, 5)
    revenue = round(quantity * random.uniform(100, 1500), 2)
    region = random.choice(regions)
    date = datetime(2024, random.randint(1, 12), random.randint(1, 28)).strftime('%Y-%m-%d')
    orders.append((i, product[0], quantity, revenue, region, date))

cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", orders)

conn.commit()
conn.close()

print("✅ Database created at schema/sample_data.db with test data!")
