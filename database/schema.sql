-- E-Commerce Customer Segmentation & Sales Intelligence System
-- Data Warehouse Star Schema Definition (MySQL / SQLite Compatible DDL)

-- Create Dimension Tables

CREATE TABLE IF NOT EXISTS DIM_CUSTOMER (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    age INT,
    customer_location VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS DIM_PRODUCT (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subcategory VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS DIM_DATE (
    date_id INT PRIMARY KEY, -- Format: YYYYMMDD (e.g. 20260115)
    full_date DATE NOT NULL,
    day INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    quarter INT NOT NULL,
    year INT NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_LOCATION (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50),
    state VARCHAR(50),
    region VARCHAR(50) NOT NULL,
    country VARCHAR(50) DEFAULT 'India'
);

-- Create Fact Table

CREATE TABLE IF NOT EXISTS FACT_SALES (
    sales_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    date_id INT NOT NULL,
    location_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES DIM_CUSTOMER(customer_id),
    FOREIGN KEY (product_id) REFERENCES DIM_PRODUCT(product_id),
    FOREIGN KEY (date_id) REFERENCES DIM_DATE(date_id),
    FOREIGN KEY (location_id) REFERENCES DIM_LOCATION(location_id)
);

-- Create Performance Indexes for DWDM Queries & OLAP Aggregations
CREATE INDEX idx_fact_date ON FACT_SALES(date_id);
CREATE INDEX idx_fact_customer ON FACT_SALES(customer_id);
CREATE INDEX idx_fact_product ON FACT_SALES(product_id);
CREATE INDEX idx_fact_location ON FACT_SALES(location_id);
CREATE INDEX idx_dim_date_year_month ON DIM_DATE(year, month);
CREATE INDEX idx_dim_location_region ON DIM_LOCATION(region);
