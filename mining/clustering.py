import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from mining.rfm import calculate_rfm_metrics

def generate_segment_label(recency_avg, frequency_avg, monetary_avg, overall_rec_med, overall_freq_med, overall_mon_med):
    """
    Intelligent dynamic segment label generator based on cluster centroid metrics.
    Compares cluster averages against overall dataset medians.
    """
    is_high_spend = monetary_avg >= overall_mon_med
    is_frequent = frequency_avg >= overall_freq_med
    is_recent = recency_avg <= overall_rec_med

    if is_high_spend and is_frequent and is_recent:
        return "High-Value Champions", "Highest monetary value, frequent orders, and active recent purchases."
    elif is_high_spend and not is_recent:
        return "At-Risk Customers", "High past spending but inactive recently. Requires re-engagement campaigns."
    elif is_frequent and is_recent:
        return "Loyal Customers", "Consistent order frequency and recent activity with steady spending."
    elif is_recent and not is_frequent:
        return "Potential / New Customers", "Recently placed orders with promising growth potential."
    else:
        return "Occasional / Dormant Customers", "Low order frequency, low spend, and long period since last purchase."

def perform_kmeans_clustering(n_clusters=4):
    """
    Executes K-Means Customer Segmentation on RFM features.
    Returns:
    - elbow_curve: WCSS values for k=1..10
    - cluster_summary: Metrics and dynamic labels for each cluster
    - scatter_data: Customer points formatted for Chart.js 2D scatter visualization
    - customers_df: Full DataFrame with cluster assignments
    """
    df_rfm = calculate_rfm_metrics()

    if len(df_rfm) < n_clusters:
        return {
            'error': f"Insufficient customer data ({len(df_rfm)} records) for {n_clusters} clusters.",
            'elbow_curve': [],
            'cluster_summary': [],
            'scatter_data': [],
            'customers': []
        }

    # Features for clustering
    features = ['recency', 'frequency', 'monetary']
    X = df_rfm[features].copy()

    # Log transform monetary & recency to handle skewness if needed, but standard scaling works great
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 1. Compute Elbow Curve Data (k=1 to 10)
    wcss = []
    max_k = min(10, len(df_rfm))
    for k in range(1, max_k + 1):
        kmeans_temp = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans_temp.fit(X_scaled)
        wcss.append({'k': k, 'wcss': round(float(kmeans_temp.inertia_), 2)})

    # 2. Fit Final K-Means Model
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df_rfm['cluster'] = kmeans.fit_predict(X_scaled)

    # 3. Overall Dataset Medians for Contextual Labeling
    rec_med = df_rfm['recency'].median()
    freq_med = df_rfm['frequency'].median()
    mon_med = df_rfm['monetary'].median()

    # 4. PCA for 2D visual projections
    pca = PCA(n_components=2)
    pca_coords = pca.fit_transform(X_scaled)
    df_rfm['pca_x'] = np.round(pca_coords[:, 0], 2)
    df_rfm['pca_y'] = np.round(pca_coords[:, 1], 2)

    # 5. Cluster Profiles & Human-Readable Labels
    cluster_summary = []
    scatter_data = []

    # Palette of colors for clusters
    colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899']

    for c in range(n_clusters):
        c_df = df_rfm[df_rfm['cluster'] == c]
        if c_df.empty:
            continue

        c_count = len(c_df)
        c_rec_avg = round(float(c_df['recency'].mean()), 1)
        c_freq_avg = round(float(c_df['frequency'].mean()), 1)
        c_mon_avg = round(float(c_df['monetary'].mean()), 2)

        label, desc = generate_segment_label(c_rec_avg, c_freq_avg, c_mon_avg, rec_med, freq_med, mon_med)

        cluster_summary.append({
            'cluster_id': c,
            'segment_name': label,
            'description': desc,
            'customer_count': c_count,
            'percentage': round((c_count / len(df_rfm)) * 100, 1),
            'avg_recency': c_rec_avg,
            'avg_frequency': c_freq_avg,
            'avg_monetary': c_mon_avg,
            'color': colors[c % len(colors)]
        })

        # Format points for scatter chart (Recency vs Monetary or PCA coordinates)
        points = []
        for _, row in c_df.iterrows():
            points.append({
                'x': float(row['recency']),
                'y': float(row['monetary']),
                'customer_id': str(row['customer_id']),
                'customer_name': str(row['customer_name']),
                'frequency': int(row['frequency'])
            })

        scatter_data.append({
            'cluster_id': c,
            'label': f"Cluster {c+1}: {label}",
            'color': colors[c % len(colors)],
            'points': points
        })

    # Sort cluster summary by monetary value descending
    cluster_summary = sorted(cluster_summary, key=lambda x: x['avg_monetary'], reverse=True)

    # Map segment_name back into customers list
    c_label_map = {item['cluster_id']: item['segment_name'] for item in cluster_summary}
    df_rfm['segment_name'] = df_rfm['cluster'].map(c_label_map)

    return {
        'n_clusters': n_clusters,
        'total_customers': len(df_rfm),
        'elbow_curve': wcss,
        'cluster_summary': cluster_summary,
        'scatter_data': scatter_data,
        'customers': df_rfm.to_dict(orient='records')
    }
