from analysis.sales import get_sales_overview
from mining.clustering import perform_kmeans_clustering
from mining.rfm import get_rfm_summary

def generate_business_insights():
    sales_data = get_sales_overview()
    rfm_summary = get_rfm_summary()
    segmentation_data = perform_kmeans_clustering(n_clusters=4)

    analytical_findings = []
    strategic_recommendations = []

    # 1. Sales & Category Insights
    best_cats = sales_data.get('best_categories', [])
    if best_cats:
        top_cat = best_cats[0]
        analytical_findings.append({
            'title': 'Highest Revenue Product Category',
            'detail': f"Category '{top_cat['category']}' generated the highest revenue of ₹{top_cat['revenue']:,.2f} across {top_cat['orders']} orders.",
            'category': 'Sales Analytics',
            'badge': 'Primary Revenue Driver',
            'icon': 'bi-tags-fill'
        })
        strategic_recommendations.append({
            'target': f"Category: {top_cat['category']}",
            'action': f"Expand product inventory and run targeted promo campaigns in '{top_cat['category']}' as it drives maximum sales volume.",
            'priority': 'High'
        })

    # 2. Regional Insights
    best_regs = sales_data.get('best_regions', [])
    if best_regs:
        top_reg = best_regs[0]
        analytical_findings.append({
            'title': 'Top Performing Sales Region',
            'detail': f"The '{top_reg['region']}' region generated ₹{top_reg['revenue']:,.2f} in total sales ({top_reg['quantity']} units sold).",
            'category': 'Regional Intelligence',
            'badge': 'Regional Leader',
            'icon': 'bi-geo-alt-fill'
        })

    # 3. Product Insights
    top_prods = sales_data.get('top_products_revenue', [])
    if top_prods:
        top_prod = top_prods[0]
        analytical_findings.append({
            'title': 'Top Performing Individual Product',
            'detail': f"'{top_prod['product_name']}' ({top_prod['category']}) achieved highest total revenue of ₹{top_prod['revenue']:,.2f}.",
            'category': 'Product Intelligence',
            'badge': 'Best Seller',
            'icon': 'bi-box-seam-fill'
        })

    # 4. Customer Segmentation Insights
    cluster_summary = segmentation_data.get('cluster_summary', [])
    if cluster_summary:
        # Highest monetary segment
        highest_val_seg = max(cluster_summary, key=lambda x: x['avg_monetary'])
        analytical_findings.append({
            'title': 'Highest Value Customer Segment',
            'detail': f"'{highest_val_seg['segment_name']}' accounts for {highest_val_seg['customer_count']} customers ({highest_val_seg['percentage']}%) with an impressive average spend of ₹{highest_val_seg['avg_monetary']:,.2f} per customer.",
            'category': 'Customer Intelligence',
            'badge': 'VIP Segment',
            'icon': 'bi-star-fill'
        })
        strategic_recommendations.append({
            'target': f"Segment: {highest_val_seg['segment_name']}",
            'action': "Enroll these customers in an exclusive VIP loyalty program with dedicated support and early product releases.",
            'priority': 'High'
        })

        # At-Risk / Dormant Segment
        at_risk_seg = next((s for s in cluster_summary if 'Risk' in s['segment_name'] or 'Dormant' in s['segment_name']), None)
        if at_risk_seg:
            analytical_findings.append({
                'title': 'At-Risk / Inactive Customer Warning',
                'detail': f"'{at_risk_seg['segment_name']}' consists of {at_risk_seg['customer_count']} customers ({at_risk_seg['percentage']}%) with a high average recency of {at_risk_seg['avg_recency']} days since last order.",
                'category': 'Retention Alert',
                'badge': 'Churn Warning',
                'icon': 'bi-exclamation-triangle-fill'
            })
            strategic_recommendations.append({
                'target': f"Segment: {at_risk_seg['segment_name']}",
                'action': "Trigger automated win-back email sequences with personalized discount coupons (e.g. 15% off) to reactivate past buyers.",
                'priority': 'Urgent'
            })

    # 5. Growth & Trend Insights
    monthly_trends = sales_data.get('trends', {}).get('monthly', [])
    if len(monthly_trends) >= 2:
        prev_m = monthly_trends[-2]['revenue']
        curr_m = monthly_trends[-1]['revenue']
        growth = round(((curr_m - prev_m) / prev_m) * 100, 1) if prev_m > 0 else 0
        trend_status = "growth" if growth >= 0 else "decline"

        analytical_findings.append({
            'title': 'Recent Monthly Sales Growth',
            'detail': f"Sales transitioned from ₹{prev_m:,.2f} ({monthly_trends[-2]['label']}) to ₹{curr_m:,.2f} ({monthly_trends[-1]['label']}), representing a {abs(growth)}% {trend_status}.",
            'category': 'Sales Growth',
            'badge': f"{growth}% {trend_status.capitalize()}",
            'icon': 'bi-graph-up-arrow' if growth >= 0 else 'bi-graph-down-arrow'
        })

    return {
        'findings': analytical_findings,
        'recommendations': strategic_recommendations,
        'kpis': sales_data.get('kpis', {}),
        'rfm_summary': rfm_summary
    }
