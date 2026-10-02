import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
from config.db import db_manager

STANDARD_COLUMNS = {
    'order_id': ['Invoice/Order ID', 'Order ID', 'Invoice ID', 'InvoiceNo', 'order_id', 'Invoice'],
    'customer_id': ['Customer ID', 'CustomerID', 'customer_id', 'User ID', 'Customer_ID'],
    'customer_name': ['Customer Name', 'CustomerName', 'customer_name', 'Name'],
    'gender': ['Gender', 'gender'],
    'age': ['Age', 'age'],
    'product_id': ['Product ID', 'ProductID', 'StockCode', 'product_id', 'Product_ID'],
    'product_name': ['Product Name', 'ProductName', 'Description', 'product_name', 'Item Name'],
    'category': ['Category', 'category', 'Product Category'],
    'subcategory': ['Subcategory', 'subcategory', 'Sub Category'],
    'quantity': ['Quantity', 'quantity', 'Qty'],
    'unit_price': ['Unit Price', 'UnitPrice', 'unit_price', 'Price'],
    'order_date': ['Order Date', 'OrderDate', 'InvoiceDate', 'order_date', 'Date'],
    'customer_location': ['Customer Location', 'Location', 'City', 'customer_location', 'city'],
    'region': ['Region', 'region', 'State/Region', 'Zone']
}

def auto_map_columns(df_columns):
    mapping = {}
    df_cols_lower = {str(col).strip().lower(): col for col in df_columns}

    for std_key, alt_names in STANDARD_COLUMNS.items():
        matched = False
        for alt in alt_names:
            alt_lower = alt.strip().lower()
            if alt_lower in df_cols_lower:
                mapping[std_key] = df_cols_lower[alt_lower]
                matched = True
                break
        if not matched:
            mapping[std_key] = None
    return mapping

class ETLPipeline:
    def __init__(self):
        self.stats = {
            'original_rows': 0,
            'removed_duplicates': 0,
            'missing_values_count': 0,
            'invalid_records_count': 0,
            'valid_rows': 0,
            'extracted_count': 0,
            'transformed_count': 0,
            'loaded_count': 0,
            'processing_time_ms': 0,
            'status': 'Not Started',
            'error_message': None
        }

    def process_csv(self, file_path_or_buffer, user_column_mapping=None):
        start_time = time.time()
        self.stats['status'] = 'Processing'

        try:
            # 1. EXTRACT
            if isinstance(file_path_or_buffer, str):
                df_raw = pd.read_csv(file_path_or_buffer)
            else:
                df_raw = pd.read_csv(file_path_or_buffer)

            self.stats['original_rows'] = len(df_raw)
            self.stats['extracted_count'] = len(df_raw)

            if len(df_raw) == 0:
                raise ValueError("Uploaded dataset is empty.")

            # Column mapping
            if not user_column_mapping:
                user_column_mapping = auto_map_columns(df_raw.columns)

            df = pd.DataFrame()
            # Rename columns based on mapping
            for std_col, csv_col in user_column_mapping.items():
                if csv_col and csv_col in df_raw.columns:
                    df[std_col] = df_raw[csv_col]
                else:
                    df[std_col] = None

            # 2. TRANSFORM & CLEANING
            # Remove exact duplicates
            initial_count = len(df)
            df = df.drop_duplicates()
            dup_count = initial_count - len(df)
            self.stats['removed_duplicates'] = dup_count

            # Required columns validation
            required_cols = ['order_id', 'customer_id', 'product_id', 'order_date', 'quantity', 'unit_price']
            missing_req = [c for c in required_cols if df[c].isnull().all()]
            if missing_req:
                raise ValueError(f"Missing required columns in dataset: {', '.join(missing_req)}")

            # Handle missing essential values
            before_missing = len(df)
            df = df.dropna(subset=['order_id', 'customer_id', 'product_id', 'order_date', 'quantity', 'unit_price'])
            self.stats['missing_values_count'] = before_missing - len(df)

            # Clean and parse types
            # Quantities and Prices
            before_invalid = len(df)
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
            df = df[(df['quantity'] > 0) & (df['unit_price'] > 0)]

            # Clean Order Date
            df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
            df = df.dropna(subset=['order_date'])

            invalid_records = before_invalid - len(df)
            self.stats['invalid_records_count'] = invalid_records

            # Calculate derived Total Amount
            df['quantity'] = df['quantity'].astype(int)
            df['unit_price'] = df['unit_price'].astype(float)
            df['total_amount'] = (df['quantity'] * df['unit_price']).round(2)

            # Fill default values for optional dimension attributes
            df['customer_name'] = df['customer_name'].fillna(df['customer_id'])
            df['gender'] = df['gender'].fillna('Unknown')
            df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(30).astype(int)
            df['product_name'] = df['product_name'].fillna(df['product_id'])
            df['category'] = df['category'].fillna('General')
            df['subcategory'] = df['subcategory'].fillna('General')
            df['customer_location'] = df['customer_location'].fillna('Unknown City')
            df['region'] = df['region'].fillna('Central')

            # Ensure proper string formats
            for str_col in ['order_id', 'customer_id', 'product_id', 'customer_name', 'gender', 'product_name', 'category', 'subcategory', 'customer_location', 'region']:
                df[str_col] = df[str_col].astype(str).str.strip()

            self.stats['valid_rows'] = len(df)
            self.stats['transformed_count'] = len(df)

            if len(df) == 0:
                raise ValueError("No valid records remaining after dataset cleaning.")

            # 3. LOAD INTO STAR SCHEMA
            db_manager.init_schema()

            # Load DIM_CUSTOMER
            customers_df = df[['customer_id', 'customer_name', 'gender', 'age', 'customer_location']].drop_duplicates('customer_id')
            self._load_dim_customer(customers_df)

            # Load DIM_PRODUCT
            products_df = df[['product_id', 'product_name', 'category', 'subcategory']].drop_duplicates('product_id')
            self._load_dim_product(products_df)

            # Load DIM_DATE
            df['date_id'] = df['order_date'].dt.strftime('%Y%m%d').astype(int)
            df['full_date'] = df['order_date'].dt.strftime('%Y-%m-%d')
            df['day'] = df['order_date'].dt.day
            df['month'] = df['order_date'].dt.month
            df['month_name'] = df['order_date'].dt.strftime('%B')
            df['quarter'] = df['order_date'].dt.quarter
            df['year'] = df['order_date'].dt.year

            dates_df = df[['date_id', 'full_date', 'day', 'month', 'month_name', 'quarter', 'year']].drop_duplicates('date_id')
            self._load_dim_date(dates_df)

            # Load DIM_LOCATION
            locations_df = df[['customer_location', 'region']].drop_duplicates()
            location_map = self._load_dim_location(locations_df)

            # Map location_id back to fact DataFrame
            df['location_id'] = df.apply(lambda r: location_map.get((r['customer_location'], r['region']), 1), axis=1)

            # Load FACT_SALES
            fact_df = df[['order_id', 'customer_id', 'product_id', 'date_id', 'location_id', 'quantity', 'unit_price', 'total_amount']]
            self._load_fact_sales(fact_df)

            self.stats['loaded_count'] = len(fact_df)
            self.stats['status'] = 'Success'
            self.stats['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)

            preview_records = df.head(10).to_dict(orient='records')
            for rec in preview_records:
                rec['order_date'] = rec['full_date']

            return {
                'success': True,
                'stats': self.stats,
                'preview': preview_records
            }

        except Exception as e:
            self.stats['status'] = 'Failed'
            self.stats['error_message'] = str(e)
            self.stats['processing_time_ms'] = round((time.time() - start_time) * 1000, 2)
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }

    def _load_dim_customer(self, df):
        rows = df.values.tolist()
        if db_manager.db_type == 'mysql':
            sql = "INSERT INTO DIM_CUSTOMER (customer_id, customer_name, gender, age, customer_location) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE customer_name=VALUES(customer_name), customer_location=VALUES(customer_location)"
        else:
            sql = "INSERT OR REPLACE INTO DIM_CUSTOMER (customer_id, customer_name, gender, age, customer_location) VALUES (%s, %s, %s, %s, %s)"
        db_manager.execute_many(sql, rows)

    def _load_dim_product(self, df):
        rows = df.values.tolist()
        if db_manager.db_type == 'mysql':
            sql = "INSERT INTO DIM_PRODUCT (product_id, product_name, category, subcategory) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE product_name=VALUES(product_name), category=VALUES(category)"
        else:
            sql = "INSERT OR REPLACE INTO DIM_PRODUCT (product_id, product_name, category, subcategory) VALUES (%s, %s, %s, %s)"
        db_manager.execute_many(sql, rows)

    def _load_dim_date(self, df):
        rows = df.values.tolist()
        if db_manager.db_type == 'mysql':
            sql = "INSERT INTO DIM_DATE (date_id, full_date, day, month, month_name, quarter, year) VALUES (%s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE full_date=VALUES(full_date)"
        else:
            sql = "INSERT OR REPLACE INTO DIM_DATE (date_id, full_date, day, month, month_name, quarter, year) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        db_manager.execute_many(sql, rows)

    def _load_dim_location(self, df):
        location_map = {}
        for _, row in df.iterrows():
            city = str(row['customer_location'])
            region = str(row['region'])
            # Check if location exists
            existing = db_manager.query_to_df("SELECT location_id FROM DIM_LOCATION WHERE city = %s AND region = %s", (city, region))
            if not existing.empty:
                loc_id = int(existing.iloc[0]['location_id'])
            else:
                loc_id = db_manager.execute("INSERT INTO DIM_LOCATION (city, state, region, country) VALUES (%s, %s, %s, %s)", (city, city, region, 'India'))
            location_map[(city, region)] = loc_id
        return location_map

    def _load_fact_sales(self, df):
        # Clear previous fact data when loading new dataset to avoid duplicate keys during re-runs
        db_manager.execute("DELETE FROM FACT_SALES")
        rows = df.values.tolist()
        sql = "INSERT INTO FACT_SALES (order_id, customer_id, product_id, date_id, location_id, quantity, unit_price, total_amount) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        db_manager.execute_many(sql, rows)

etl_pipeline = ETLPipeline()
