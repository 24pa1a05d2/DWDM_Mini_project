import pandas as pd
from config.db import db_manager

def get_filtered_sales_data(start_date=None, end_date=None, category=None, region=None, product_id=None):
    """
    Builds SQL query dynamically based on user filter selections.
    """
    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("d.full_date >= %s")
        params.append(start_date)
    if end_date:
        where_clauses.append("d.full_date <= %s")
        params.append(end_date)
    if category and category != 'All':
        where_clauses.append("p.category = %s")
        params.append(category)
    if region and region != 'All':
        where_clauses.append("l.region = %s")
        params.append(region)
    if product_id and product_id != 'All':
        where_clauses.append("p.product_id = %s")
        params.append(product_id)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
    SELECT
        f.sales_id,
        f.order_id,
        f.customer_id,
        f.product_id,
        f.quantity,
        f.unit_price,
        f.total_amount,
        d.full_date,
        d.day,
        d.month,
        d.month_name,
        d.quarter,
        d.year,
        p.product_name,
        p.category,
        p.subcategory,
        l.city,
        l.region
    FROM FACT_SALES f
    JOIN DIM_DATE d ON f.date_id = d.date_id
    JOIN DIM_PRODUCT p ON f.product_id = p.product_id
    JOIN DIM_LOCATION l ON f.location_id = l.location_id
    {where_sql}
    """

    return db_manager.query_to_df(query, tuple(params))

def get_sales_overview(start_date=None, end_date=None, category=None, region=None, product_id=None):
    df = get_filtered_sales_data(start_date, end_date, category, region, product_id)

    if df.empty:
        return {
            'kpis': {'total_revenue': 0, 'total_orders': 0, 'total_quantity': 0, 'avg_order_value': 0, 'total_customers': 0, 'total_products': 0},
            'trends': {'daily': [], 'monthly': [], 'quarterly': [], 'yearly': []},
            'category_sales': [],
            'region_sales': [],
            'top_products_revenue': [],
            'top_products_quantity': [],
            'best_categories': [],
            'best_regions': []
        }

    # KPIs
    total_revenue = round(float(df['total_amount'].sum()), 2)
    total_orders = int(df['order_id'].nunique())
    total_quantity = int(df['quantity'].sum())
    total_customers = int(df['customer_id'].nunique())
    total_products = int(df['product_id'].nunique())
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0

    kpis = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_quantity': total_quantity,
        'avg_order_value': avg_order_value,
        'total_customers': total_customers,
        'total_products': total_products
    }

    # Daily trend
    daily_df = df.groupby('full_date').agg({'total_amount': 'sum', 'order_id': 'nunique'}).reset_index()
    daily_df.columns = ['date', 'revenue', 'orders']
    daily_df['revenue'] = daily_df['revenue'].round(2)
    daily = daily_df.to_dict(orient='records')

    # Monthly trend
    monthly_df = df.groupby(['year', 'month', 'month_name']).agg({'total_amount': 'sum', 'order_id': 'nunique'}).reset_index()
    monthly_df = monthly_df.sort_values(by=['year', 'month'])
    monthly_df['label'] = monthly_df['month_name'].astype(str) + " " + monthly_df['year'].astype(str)
    monthly_df['revenue'] = monthly_df['total_amount'].round(2)
    monthly = monthly_df[['label', 'revenue', 'order_id']].rename(columns={'order_id': 'orders'}).to_dict(orient='records')

    # Quarterly trend
    quarterly_df = df.groupby(['year', 'quarter']).agg({'total_amount': 'sum', 'order_id': 'nunique'}).reset_index()
    quarterly_df = quarterly_df.sort_values(by=['year', 'quarter'])
    quarterly_df['label'] = "Q" + quarterly_df['quarter'].astype(str) + " " + quarterly_df['year'].astype(str)
    quarterly_df['revenue'] = quarterly_df['total_amount'].round(2)
    quarterly = quarterly_df[['label', 'revenue', 'order_id']].rename(columns={'order_id': 'orders'}).to_dict(orient='records')

    # Yearly trend
    yearly_df = df.groupby('year').agg({'total_amount': 'sum', 'order_id': 'nunique'}).reset_index()
    yearly_df['revenue'] = yearly_df['total_amount'].round(2)
    yearly = yearly_df[['year', 'revenue', 'order_id']].rename(columns={'order_id': 'orders'}).to_dict(orient='records')

    # Category Sales
    cat_df = df.groupby('category').agg({'total_amount': 'sum', 'quantity': 'sum', 'order_id': 'nunique'}).reset_index()
    cat_df.columns = ['category', 'revenue', 'quantity', 'orders']
    cat_df['revenue'] = cat_df['revenue'].round(2)
    cat_df = cat_df.sort_values(by='revenue', ascending=False)
    category_sales = cat_df.to_dict(orient='records')

    # Region Sales
    reg_df = df.groupby('region').agg({'total_amount': 'sum', 'quantity': 'sum', 'order_id': 'nunique'}).reset_index()
    reg_df.columns = ['region', 'revenue', 'quantity', 'orders']
    reg_df['revenue'] = reg_df['revenue'].round(2)
    reg_df = reg_df.sort_values(by='revenue', ascending=False)
    region_sales = reg_df.to_dict(orient='records')

    # Top 10 Products by Revenue
    prod_rev_df = df.groupby(['product_id', 'product_name', 'category']).agg({'total_amount': 'sum', 'quantity': 'sum'}).reset_index()
    prod_rev_df['revenue'] = prod_rev_df['total_amount'].round(2)
    top_products_revenue = prod_rev_df.sort_values(by='revenue', ascending=False).head(10).to_dict(orient='records')

    # Top 10 Products by Quantity
    top_products_quantity = prod_rev_df.sort_values(by='quantity', ascending=False).head(10).to_dict(orient='records')

    return {
        'kpis': kpis,
        'trends': {
            'daily': daily,
            'monthly': monthly,
            'quarterly': quarterly,
            'yearly': yearly
        },
        'category_sales': category_sales,
        'region_sales': region_sales,
        'top_products_revenue': top_products_revenue,
        'top_products_quantity': top_products_quantity,
        'best_categories': category_sales[:5],
        'best_regions': region_sales[:5]
    }

def get_filter_options():
    """
    Returns available filter dropdown lists (categories, regions, products).
    """
    categories_df = db_manager.query_to_df("SELECT DISTINCT category FROM DIM_PRODUCT ORDER BY category")
    regions_df = db_manager.query_to_df("SELECT DISTINCT region FROM DIM_LOCATION ORDER BY region")
    products_df = db_manager.query_to_df("SELECT product_id, product_name FROM DIM_PRODUCT ORDER BY product_name")

    return {
        'categories': categories_df['category'].tolist() if not categories_df.empty else [],
        'regions': regions_df['region'].tolist() if not regions_df.empty else [],
        'products': products_df.to_dict(orient='records') if not products_df.empty else []
    }
