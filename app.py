import os
import io
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from config.db import db_manager
from etl.pipeline import etl_pipeline
from analysis.sales import get_sales_overview, get_filter_options
from analysis.olap import olap_engine
from mining.rfm import get_rfm_summary, calculate_rfm_metrics
from mining.clustering import perform_kmeans_clustering
from analysis.insights import generate_business_insights

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dwdm_ecommerce_secret_key_2026')

# Initialize DB Schema and automatically load sample dataset on startup if DB is empty!
@app.before_request
def ensure_database_populated():
    if not hasattr(app, '_db_initialized'):
        app._db_initialized = True
        try:
            db_manager.init_schema()
            # Check if FACT_SALES has records
            fact_check = db_manager.query_to_df("SELECT COUNT(*) AS count FROM FACT_SALES")
            if fact_check.empty or int(fact_check.iloc[0]['count']) == 0:
                print("[App Startup] Data warehouse empty. Automatically populating sample dataset...")
                sample_csv_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_ecommerce_data.csv')
                if os.path.exists(sample_csv_path):
                    etl_pipeline.process_csv(sample_csv_path)
                    print("[App Startup] Sample dataset loaded successfully into Data Warehouse.")
        except Exception as e:
            print(f"[App Startup Warning] Error auto-populating DB: {e}")

# --- HTML TEMPLATE ROUTES ---

@app.route('/')
def dashboard_page():
    return render_template('dashboard.html', active_page='dashboard')

@app.route('/data')
def data_page():
    return render_template('data.html', active_page='data')

@app.route('/sales')
def sales_page():
    return render_template('sales.html', active_page='sales')

@app.route('/customers')
def customers_page():
    return render_template('customers.html', active_page='customers')

@app.route('/segmentation')
def segmentation_page():
    return render_template('segmentation.html', active_page='segmentation')

@app.route('/olap')
def olap_page():
    return render_template('olap.html', active_page='olap')

@app.route('/reports')
def reports_page():
    return render_template('reports.html', active_page='reports')

@app.route('/about')
def about_page():
    return render_template('about.html', active_page='about')

# --- REST API ENDPOINTS ---

@app.route('/api/dashboard')
def api_dashboard():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        region = request.args.get('region')

        sales_data = get_sales_overview(start_date, end_date, category, region)
        segmentation_data = perform_kmeans_clustering(n_clusters=4)

        # Build dashboard chart payloads
        response = {
            'success': True,
            'kpis': sales_data['kpis'],
            'charts': {
                'monthly_trend': sales_data['trends']['monthly'],
                'category_sales': sales_data['category_sales'],
                'region_sales': sales_data['region_sales'],
                'top_products': sales_data['top_products_revenue'],
                'segment_distribution': [
                    {'segment': s['segment_name'], 'count': s['customer_count'], 'color': s['color']}
                    for s in segmentation_data.get('cluster_summary', [])
                ],
                'revenue_distribution': [
                    {'segment': s['segment_name'], 'revenue': round(s['customer_count'] * s['avg_monetary'], 2), 'color': s['color']}
                    for s in segmentation_data.get('cluster_summary', [])
                ]
            }
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/filters')
def api_filters():
    try:
        options = get_filter_options()
        return jsonify({'success': True, 'filters': options})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/etl/upload', methods=['POST'])
def api_etl_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected.'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'error': 'Invalid file format. Please upload a CSV file.'}), 400

        result = etl_pipeline.process_csv(file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/etl/run_sample', methods=['POST'])
def api_etl_sample():
    try:
        sample_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_ecommerce_data.csv')
        if not os.path.exists(sample_path):
            from data.generate_sample_data import generate_ecommerce_dataset
            generate_ecommerce_dataset()

        result = etl_pipeline.process_csv(sample_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sales')
def api_sales():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        region = request.args.get('region')
        product_id = request.args.get('product_id')

        data = get_sales_overview(start_date, end_date, category, region, product_id)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/olap', methods=['GET'])
def api_olap():
    try:
        operation = request.args.get('operation', 'rollup').lower()

        if operation == 'rollup':
            level = request.args.get('level', 'monthly')
            year = request.args.get('year')
            res = olap_engine.rollup(level, year)
        elif operation == 'drilldown':
            year = request.args.get('year', 2026)
            quarter = request.args.get('quarter')
            month = request.args.get('month')
            res = olap_engine.drilldown(year, quarter, month)
        elif operation == 'slice':
            dim = request.args.get('dimension', 'category')
            val = request.args.get('value', 'Electronics')
            res = olap_engine.slice(dim, val)
        elif operation == 'dice':
            categories = request.args.getlist('categories')
            regions = request.args.getlist('regions')
            years = request.args.getlist('years')
            res = olap_engine.dice(categories, regions, years)
        else:
            return jsonify({'success': False, 'error': 'Unknown OLAP operation'}), 400

        return jsonify({'success': True, 'result': res})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rfm')
def api_rfm():
    try:
        df_rfm = calculate_rfm_metrics()
        summary = get_rfm_summary()
        return jsonify({
            'success': True,
            'summary': summary,
            'customers': df_rfm.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/segmentation')
def api_segmentation():
    try:
        n_clusters = int(request.args.get('clusters', 4))
        n_clusters = max(2, min(8, n_clusters))

        res = perform_kmeans_clustering(n_clusters=n_clusters)
        return jsonify({'success': True, 'data': res})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/insights')
def api_insights():
    try:
        insights = generate_business_insights()
        return jsonify({'success': True, 'insights': insights})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports/export/<export_type>')
def api_export_report(export_type):
    try:
        if export_type == 'sales':
            df = db_manager.query_to_df("""
                SELECT f.order_id, c.customer_name, p.product_name, p.category, f.quantity, f.unit_price, f.total_amount, d.full_date, l.region
                FROM FACT_SALES f
                JOIN DIM_CUSTOMER c ON f.customer_id = c.customer_id
                JOIN DIM_PRODUCT p ON f.product_id = p.product_id
                JOIN DIM_DATE d ON f.date_id = d.date_id
                JOIN DIM_LOCATION l ON f.location_id = l.location_id
                ORDER BY d.full_date DESC
            """)
            filename = "sales_summary_report.csv"
        elif export_type == 'rfm':
            df = calculate_rfm_metrics()
            filename = "rfm_analysis_report.csv"
        elif export_type == 'segmentation':
            seg = perform_kmeans_clustering(n_clusters=4)
            df = pd.DataFrame(seg['customers'])
            filename = "customer_segmentation_report.csv"
        else:
            olap_res = olap_engine.rollup('monthly')
            df = pd.DataFrame(olap_res['records'])
            filename = "olap_summary_report.csv"

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("================================================================")
    print("  E-Commerce Customer Segmentation & Sales Intelligence System")
    print("  DWDM B.Tech CSE Mini-Project Server")
    print("================================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
