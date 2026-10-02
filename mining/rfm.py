import pandas as pd
import numpy as np
from config.db import db_manager

def calculate_rfm_metrics():
    """
    Calculates Recency, Frequency, Monetary (RFM) metrics and quantile scores for each customer.
    Query aggregates FACT_SALES, DIM_CUSTOMER, and DIM_DATE tables in the Data Warehouse.
    """
    query = """
    SELECT
        c.customer_id,
        c.customer_name,
        c.customer_location,
        c.gender,
        c.age,
        MAX(d.full_date) AS last_purchase_date,
        COUNT(DISTINCT f.order_id) AS frequency,
        SUM(f.total_amount) AS monetary
    FROM FACT_SALES f
    JOIN DIM_CUSTOMER c ON f.customer_id = c.customer_id
    JOIN DIM_DATE d ON f.date_id = d.date_id
    GROUP BY c.customer_id, c.customer_name, c.customer_location, c.gender, c.age
    """

    df = db_manager.query_to_df(query)

    if df.empty:
        return pd.DataFrame(columns=[
            'customer_id', 'customer_name', 'last_purchase_date',
            'recency', 'frequency', 'monetary',
            'r_score', 'f_score', 'm_score', 'rfm_score_str', 'rfm_total_score'
        ])

    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    max_date = df['last_purchase_date'].max()

    # Calculate Recency in days
    df['recency'] = (max_date - df['last_purchase_date']).dt.days

    # Ensure numeric types
    df['frequency'] = df['frequency'].astype(int)
    df['monetary'] = df['monetary'].astype(float).round(2)

    # Calculate RFM Quantile Scores (1-5 scale)
    num_customers = len(df)
    bins = min(5, max(2, num_customers))

    # Recency: lower is better -> labels 5 to 1
    try:
        df['r_score'] = pd.qcut(df['recency'], q=bins, labels=range(bins, 0, -1), duplicates='drop').astype(int)
    except Exception:
        df['r_score'] = pd.cut(df['recency'], bins=bins, labels=range(bins, 0, -1)).astype(int)

    # Frequency: higher is better -> labels 1 to 5
    try:
        df['f_score'] = pd.qcut(df['frequency'].rank(method='first'), q=bins, labels=range(1, bins + 1)).astype(int)
    except Exception:
        df['f_score'] = pd.cut(df['frequency'], bins=bins, labels=range(1, bins + 1)).astype(int)

    # Monetary: higher is better -> labels 1 to 5
    try:
        df['m_score'] = pd.qcut(df['monetary'], q=bins, labels=range(1, bins + 1), duplicates='drop').astype(int)
    except Exception:
        df['m_score'] = pd.cut(df['monetary'], bins=bins, labels=range(1, bins + 1)).astype(int)

    # Composite RFM Score String (e.g. "555") and Total Score Sum
    df['rfm_score_str'] = df['r_score'].astype(str) + df['f_score'].astype(str) + df['m_score'].astype(str)
    df['rfm_total_score'] = df['r_score'] + df['f_score'] + df['m_score']

    # Format date back to string
    df['last_purchase_date'] = df['last_purchase_date'].dt.strftime('%Y-%m-%d')

    return df

def get_rfm_summary():
    df = calculate_rfm_metrics()
    if df.empty:
        return {
            'total_customers': 0,
            'avg_recency': 0,
            'avg_frequency': 0,
            'avg_monetary': 0,
            'top_rfm_customers': []
        }

    summary = {
        'total_customers': len(df),
        'avg_recency': round(float(df['recency'].mean()), 1),
        'avg_frequency': round(float(df['frequency'].mean()), 1),
        'avg_monetary': round(float(df['monetary'].mean()), 2),
        'top_rfm_customers': df.sort_values(by='rfm_total_score', ascending=False).head(10).to_dict(orient='records')
    }
    return summary
