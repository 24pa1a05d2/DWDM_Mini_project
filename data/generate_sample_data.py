import os
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_ecommerce_dataset(filename="sample_ecommerce_data.csv", num_records=1500):
    random.seed(42)
    np.random.seed(42)

    categories_subcategories = {
        'Electronics': ['Audio', 'Mobile Accessories', 'Laptops & PCs', 'Wearables', 'Cameras'],
        'Apparel': ["Men's Wear", "Women's Wear", 'Footwear', 'Watches', 'Bags'],
        'Home & Kitchen': ['Kitchenware', 'Furniture', 'Home Decor', 'Bedding', 'Lighting'],
        'Books & Stationery': ['Fiction', 'Academic', 'Self-Help', 'Office Supplies', 'Comics'],
        'Beauty & Personal Care': ['Skincare', 'Haircare', 'Fragrances', 'Grooming', 'Makeup'],
        'Sports & Fitness': ['Fitness Equipment', 'Outdoor Gear', 'Sports Wear', 'Yoga Accessories', 'Cycling']
    }

    products_by_category = {
        'Electronics': [
            ('Wireless Noise-Cancelling Headphones', 'Audio', 4999.00),
            ('Bluetooth Smart Speaker', 'Audio', 2999.00),
            ('Fast Charging Power Bank 20000mAh', 'Mobile Accessories', 1499.00),
            ('Ergonomic Wireless Mouse', 'Laptops & PCs', 899.00),
            ('Smart Fitness Watch Pro', 'Wearables', 3499.00),
            ('Mechanical Gaming Keyboard', 'Laptops & PCs', 3999.00),
            ('HD Action Camera 4K', 'Cameras', 8999.00),
            ('USB-C Multi-port Hub', 'Mobile Accessories', 1299.00)
        ],
        'Apparel': [
            ('Classic Cotton Denim Jacket', "Men's Wear", 2499.00),
            ('Floral Print Summer Dress', "Women's Wear", 1899.00),
            ('Running Sports Sneakers', 'Footwear', 3299.00),
            ('Analog Leather Strap Watch', 'Watches', 2799.00),
            ('Canvas Travel Backpack', 'Bags', 1599.00),
            ('Slim Fit Formal Trousers', "Men's Wear", 1499.00),
            ('Winter Hooded Sweatshirt', "Men's Wear", 1999.00)
        ],
        'Home & Kitchen': [
            ('Stainless Steel Cookware Set', 'Kitchenware', 3999.00),
            ('Orthopedic Memory Foam Pillow', 'Bedding', 1299.00),
            ('Smart LED Desk Lamp', 'Lighting', 999.00),
            ('Automatic Espresso Coffee Maker', 'Kitchenware', 12999.00),
            ('Decorative Ceramic Vase', 'Home Decor', 799.00),
            ('Wooden Minimalist Side Table', 'Furniture', 4499.00)
        ],
        'Books & Stationery': [
            ('Data Science & Mining Handbook', 'Academic', 850.00),
            ('The Psychology of Money', 'Self-Help', 450.00),
            ('Bestseller Mystery Novel', 'Fiction', 399.00),
            ('Executive Hardbound Notebook Set', 'Office Supplies', 599.00),
            ('Graphic Novel Collection', 'Comics', 1200.00)
        ],
        'Beauty & Personal Care': [
            ('Vitamin C Face Serum 30ml', 'Skincare', 699.00),
            ('Argan Oil Hair Treatment', 'Haircare', 899.00),
            ('Luxury Eau De Parfum 100ml', 'Fragrances', 2499.00),
            ('Electric Beard Trimmer Kit', 'Grooming', 1799.00)
        ],
        'Sports & Fitness': [
            ('Non-Slip Eco Yoga Mat', 'Yoga Accessories', 999.00),
            ('Adjustable Dumbbell Pair (20kg)', 'Fitness Equipment', 5499.00),
            ('Thermal Insulated Water Bottle', 'Outdoor Gear', 699.00),
            ('Cycling Helmet with Safety Light', 'Cycling', 1899.00),
            ('Resistance Band Set', 'Fitness Equipment', 499.00)
        ]
    }

    cities_regions = [
        ('Mumbai', 'West', 'Maharashtra'),
        ('Delhi', 'North', 'Delhi'),
        ('Bangalore', 'South', 'Karnataka'),
        ('Hyderabad', 'South', 'Telangana'),
        ('Chennai', 'South', 'Tamil Nadu'),
        ('Kolkata', 'East', 'West Bengal'),
        ('Pune', 'West', 'Maharashtra'),
        ('Ahmedabad', 'West', 'Gujarat'),
        ('Jaipur', 'North', 'Rajasthan'),
        ('Lucknow', 'Central', 'Uttar Pradesh'),
        ('Bhopal', 'Central', 'Madhya Pradesh'),
        ('Chandigarh', 'North', 'Punjab')
    ]

    first_names = ['Aarav', 'Ananya', 'Rohan', 'Priya', 'Vikram', 'Neha', 'Rahul', 'Sneha', 'Amit', 'Pooja', 'Karan', 'Divya', 'Siddharth', 'Meera', 'Arjun', 'Tanvi', 'Aditya', 'Riya', 'Sanjay', 'Kavita']
    last_names = ['Sharma', 'Verma', 'Patel', 'Rao', 'Gupta', 'Singh', 'Nair', 'Deshmukh', 'Joshi', 'Mehta', 'Reddy', 'Kumar', 'Chopra', 'Banerjee', 'Bhat']

    # Generate customer pool (approx 200 customers)
    num_customers = 180
    customers = []
    for i in range(1, num_customers + 1):
        cust_id = f"CUST-{1000 + i}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        gender = random.choice(['Male', 'Female'])
        age = random.randint(18, 65)
        city, region, state = random.choice(cities_regions)
        # Assign customer tier / spending tendency
        tier = np.random.choice(['VIP', 'Loyal', 'Regular', 'Occasional'], p=[0.15, 0.25, 0.40, 0.20])
        customers.append({
            'customer_id': cust_id,
            'customer_name': name,
            'gender': gender,
            'age': age,
            'city': city,
            'region': region,
            'tier': tier
        })

    # Prepare order generation
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 9, 30)
    total_days = (end_date - start_date).days

    rows = []

    # Map products into flat list
    flat_products = []
    prod_idx = 100
    for cat, prods in products_by_category.items():
        for item in prods:
            prod_idx += 1
            flat_products.append({
                'product_id': f"PROD-{prod_idx}",
                'product_name': item[0],
                'category': cat,
                'subcategory': item[1],
                'unit_price': item[2]
            })

    order_counter = 10000

    for r in range(num_records):
        # Pick customer based on tier probabilities
        cust = random.choice(customers)
        tier = cust['tier']

        # Determine purchase date biased by customer tier to create clear RFM / K-Means clusters!
        if tier == 'VIP':
            days_offset = random.randint(total_days - 120, total_days) # Recent purchase
            qty_range = (2, 8)
        elif tier == 'Loyal':
            days_offset = random.randint(total_days - 250, total_days)
            qty_range = (1, 5)
        elif tier == 'At-Risk' or tier == 'Occasional':
            days_offset = random.randint(0, total_days - 180) # Older purchase
            qty_range = (1, 2)
        else:
            days_offset = random.randint(0, total_days)
            qty_range = (1, 3)

        order_date = start_date + timedelta(days=days_offset)
        order_counter += random.choice([0, 0, 1]) # Multiple items per order occasionally
        order_id = f"ORD-{order_counter}"

        prod = random.choice(flat_products)
        quantity = random.randint(*qty_range)
        unit_price = prod['unit_price']

        rows.append({
            'Invoice/Order ID': order_id,
            'Customer ID': cust['customer_id'],
            'Customer Name': cust['customer_name'],
            'Gender': cust['gender'],
            'Age': cust['age'],
            'Product ID': prod['product_id'],
            'Product Name': prod['product_name'],
            'Category': prod['category'],
            'Subcategory': prod['subcategory'],
            'Quantity': quantity,
            'Unit Price': unit_price,
            'Order Date': order_date.strftime('%Y-%m-%d'),
            'Customer Location': cust['city'],
            'Region': cust['region']
        })

    df = pd.DataFrame(rows)

    # Save to CSV
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, filename)
    df.to_csv(output_path, index=False)
    print(f"Sample dataset successfully generated with {len(df)} records at: {output_path}")
    return output_path

if __name__ == '__main__':
    generate_ecommerce_dataset()
