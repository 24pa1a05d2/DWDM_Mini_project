import os
import sqlite3
import pymysql
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'ecommerce_dwdm')

# Database connection manager with automatic fallback
class DatabaseManager:
    def __init__(self):
        self.db_type = 'mysql'
        self.sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'ecommerce_dwdm.db')
        self.sqlite_path = os.path.abspath(self.sqlite_path)
        self._check_connection()

    def _check_connection(self):
        try:
            # Try connecting to MySQL
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=2
            )
            # Create DB if it doesn't exist
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
            conn.close()
            self.db_type = 'mysql'
            print(f"[DB Manager] Connected successfully to MySQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
        except Exception as e:
            self.db_type = 'sqlite'
            print(f"[DB Manager] MySQL connection unavailable ({e}). Falling back to SQLite database at {self.sqlite_path}")

    def get_connection(self):
        if self.db_type == 'mysql':
            return pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn

    def init_schema(self):
        conn = self.get_connection()
        if self.db_type == 'mysql':
            cursor = conn.cursor()
            schema_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
            with open(schema_file, 'r') as f:
                sql_script = f.read()
            # Split commands
            commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip()]
            for cmd in commands:
                try:
                    cursor.execute(cmd)
                except Exception as ex:
                    print(f"[DB Init Warning] {ex}")
            cursor.close()
        else:
            # SQLite DDL adaptation
            sqlite_ddl = """
            CREATE TABLE IF NOT EXISTS DIM_CUSTOMER (
                customer_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                gender TEXT,
                age INTEGER,
                customer_location TEXT
            );

            CREATE TABLE IF NOT EXISTS DIM_PRODUCT (
                product_id TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT
            );

            CREATE TABLE IF NOT EXISTS DIM_DATE (
                date_id INTEGER PRIMARY KEY,
                full_date TEXT NOT NULL,
                day INTEGER NOT NULL,
                month INTEGER NOT NULL,
                month_name TEXT NOT NULL,
                quarter INTEGER NOT NULL,
                year INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS DIM_LOCATION (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT,
                state TEXT,
                region TEXT NOT NULL,
                country TEXT DEFAULT 'India'
            );

            CREATE TABLE IF NOT EXISTS FACT_SALES (
                sales_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                date_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES DIM_CUSTOMER(customer_id),
                FOREIGN KEY (product_id) REFERENCES DIM_PRODUCT(product_id),
                FOREIGN KEY (date_id) REFERENCES DIM_DATE(date_id),
                FOREIGN KEY (location_id) REFERENCES DIM_LOCATION(location_id)
            );
            """
            cursor = conn.cursor()
            cursor.executescript(sqlite_ddl)
            conn.commit()
        conn.close()

    def query_to_df(self, query, params=None):
        conn = self.get_connection()
        try:
            if self.db_type == 'sqlite':
                sqlite_query = query.replace('%s', '?')
                df = pd.read_sql_query(sqlite_query, conn, params=params if params else ())
            else:
                # Mysql
                df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()

    def execute(self, query, params=None):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if self.db_type == 'sqlite':
                # Convert %s placeholders to ? if sqlite
                sqlite_query = query.replace('%s', '?')
                cursor.execute(sqlite_query, params if params else ())
            else:
                cursor.execute(query, params if params else ())
            conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        finally:
            conn.close()

    def execute_many(self, query, params_list):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if self.db_type == 'sqlite':
                sqlite_query = query.replace('%s', '?')
                cursor.executemany(sqlite_query, params_list)
            else:
                cursor.executemany(query, params_list)
            conn.commit()
            cursor.close()
        finally:
            conn.close()

db_manager = DatabaseManager()
