# E-Commerce Customer Segmentation & Sales Intelligence System
> **B.Tech CSE Data Warehousing and Data Mining (DWDM) Mini-Project**

A complete, full-stack Data Warehousing & Data Mining web application that transforms raw e-commerce transaction data into strategic business intelligence using an automated **ETL Pipeline**, **Star Schema Data Warehouse**, **Multidimensional OLAP Engine**, **RFM Analysis**, and **K-Means Machine Learning Customer Segmentation**.

---

## 🌟 Key Features & Application Modules

1. **Executive Dashboard (`/`)**
   - 5 Real-Time KPI Cards: Total Revenue, Total Orders, Total Customers, Total Products, Average Order Value (AOV).
   - 6 Dynamic Interactive Chart.js Visualizations (Monthly Trend, Category Sales, Region Sales, Top 10 Products, Segment Distribution, Revenue Distribution).
   - Dynamic Date, Category, and Region Filters.

2. **Data Management & ETL Pipeline (`/data`)**
   - CSV Dataset Drag & Drop Upload with custom field mapping.
   - Cleaning & Preprocessing: Deduplication, null value handling, date standardization (ISO format), invalid record filtering ($Qty \le 0, Price \le 0$).
   - Automated Star Schema Insertion & ETL Execution Statistics (Extracted, Transformed, Loaded, Duration ms).

3. **Data Warehouse Star Schema (`database/schema.sql`)**
   - Central `FACT_SALES` table storing numeric metrics and foreign keys.
   - 4 Normalized Dimension Tables: `DIM_CUSTOMER`, `DIM_PRODUCT`, `DIM_DATE`, `DIM_LOCATION`.

4. **Sales Analysis Module (`/sales`)**
   - Time-series granularity toggle (Daily, Monthly, Quarterly, Yearly trend lines).
   - Top 10 products tables by Revenue and by Volume.
   - Category and Regional sales performance tables with interactive filters.

5. **Customer Analysis & RFM Engine (`/customers`)**
   - Recency (days since last purchase), Frequency (total orders), Monetary (total spend) metric calculation.
   - Quantile-based 1-5 scoring and composite RFM string generation (e.g., `555`, `452`).
   - Interactive datatable with live search and sorting by R, F, M, or RFM score.

6. **K-Means Customer Segmentation (`/segmentation`)**
   - Feature scaling via `StandardScaler`.
   - Dynamic Elbow Method WCSS curve calculation across $K \in [1, 10]$.
   - 2D Customer Cluster Scatter Plot (Recency vs Monetary).
   - Dynamic Human-Readable Segment Profiles (*High-Value Champions*, *Loyal Customers*, *At-Risk Customers*, *Potential / New Customers*, *Occasional Customers*).
   - Segment Customer Explorer Modal.

7. **Multidimensional OLAP Engine (`/olap`)**
   - **ROLL-UP**: Aggregate granular daily transactions up to Monthly, Quarterly, or Yearly levels.
   - **DRILL-DOWN**: De-aggregate yearly summary metrics down to Quarterly, Monthly, or Daily details.
   - **SLICE**: Extract 2D slice by fixing 1 dimension (e.g. Category = Electronics).
   - **DICE**: Extract sub-cube across multiple dimensions (e.g. Category IN (...) AND Region IN (...) AND Year IN (...)).
   - Generated SQL queries & DWDM Viva concept explanations.

8. **Business Insights & Reports (`/reports`)**
   - Dynamic Analytical Findings & Strategic Marketing Recommendations generated from data facts.
   - Summary datatables, CSV Report exporter, and Printable Report View.

9. **About Project & Viva Defense Guide (`/about`)**
   - End-to-end architecture flow, DWDM concepts breakdown, technology stack, and viva presentation notes.

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js
- **Backend Framework**: Python 3.13 / Flask REST APIs
- **Database**: MySQL Data Warehouse (with automatic SQLite fallback for instant out-of-the-box execution)
- **Data Processing & Analytics**: Pandas, NumPy
- **Data Mining & ML**: Scikit-Learn (`KMeans`, `StandardScaler`, `PCA`)

---

## 📁 Project Structure

```text
ecommerce-dwdm/
│
├── app.py                      # Flask Application Server & REST API Routes
├── requirements.txt            # Python Dependencies
├── .env.example                # Environment Variable Template
├── .env                        # Local Environment Configuration
├── README.md                   # Project Documentation
│
├── config/
│   └── db.py                   # DB Connection Manager (MySQL with SQLite Fallback)
│
├── database/
│   └── schema.sql              # Star Schema Data Warehouse DDL
│
├── data/
│   ├── sample_ecommerce_data.csv  # 1,500 Record Sample Dataset
│   └── generate_sample_data.py # Synthetic Dataset Generator Script
│
├── etl/
│   └── pipeline.py             # ETL Engine: Extract, Clean/Transform, Load
│
├── mining/
│   ├── rfm.py                  # RFM Quantile Analysis Engine
│   └── clustering.py           # K-Means Machine Learning Clustering Engine
│
├── analysis/
│   ├── sales.py                # Sales Metrics & Multi-Dimensional Aggregations
│   ├── olap.py                 # OLAP Engine (Roll-Up, Drill-Down, Slice, Dice)
│   └── insights.py             # Dynamic Business Findings & Strategy Generator
│
├── templates/                  # Jinja2 HTML Page Templates
│   ├── base.html
│   ├── dashboard.html
│   ├── data.html
│   ├── sales.html
│   ├── customers.html
│   ├── segmentation.html
│   ├── olap.html
│   ├── reports.html
│   └── about.html
│
└── static/                     # CSS & JavaScript Assets
    ├── css/
    │   └── style.css
    └── js/
        ├── main.js
        ├── dashboard.js
        ├── data_management.js
        ├── sales.js
        ├── customers.js
        ├── segmentation.js
        ├── olap.js
        └── reports.js
```

---

## 🚀 Installation & Setup Instructions

### 1. Clone or Open Project Directory
```bash
cd c:\Users\navya\OneDrive\Documents\dwdm_mini_project
```

### 2. Install Python Dependencies
```bash
py -3 -m pip install -r requirements.txt
```

### 3. Database Configuration (MySQL / SQLite)
- **Option A (MySQL)**: Start your local MySQL Server (XAMPP / MySQL Workbench). Create database `ecommerce_dwdm` and update `.env` with your credentials:
  ```ini
  DB_HOST=localhost
  DB_PORT=3306
  DB_USER=root
  DB_PASSWORD=your_mysql_password
  DB_NAME=ecommerce_dwdm
  ```
- **Option B (SQLite Fallback)**: If MySQL is not running locally, the system **automatically falls back to an embedded SQLite database** (`database/ecommerce_dwdm.db`) so the application works seamlessly out-of-the-box!

### 4. Run Flask Application
```bash
py -3 app.py
```

### 5. Access Web Dashboard
Open your browser and navigate to:
```text
http://localhost:5000
```
*Note: On first startup, the application automatically loads the 1,500 record sample dataset into the Data Warehouse.*

---

## 🎓 DWDM Viva Questions Quick Reference

1. **What is a Star Schema and why use it?**
   - *Answer*: A Star Schema consists of a single central Fact Table (`FACT_SALES`) connected to un-normalized Dimension Tables (`DIM_CUSTOMER`, `DIM_PRODUCT`, `DIM_DATE`, `DIM_LOCATION`). It minimizes query joins and accelerates OLAP aggregation performance.

2. **Explain the difference between Roll-Up and Drill-Down.**
   - *Answer*: Roll-Up moves up a dimension hierarchy (e.g. Daily $\rightarrow$ Monthly $\rightarrow$ Yearly) to summarize data. Drill-Down moves down a dimension hierarchy (e.g. Yearly $\rightarrow$ Monthly $\rightarrow$ Daily) to inspect granular detail.

3. **How does K-Means handle feature scaling in RFM analysis?**
   - *Answer*: Since Monetary spend (e.g. ₹50,000) has a much larger numeric scale than Frequency (e.g. 5 orders) or Recency (e.g. 30 days), we use `StandardScaler` to transform features to mean=0 and variance=1. This ensures Euclidean distance calculations treat all 3 RFM features equally.
