import pandas as pd
from config.db import db_manager

class OLAPEngine:
    def __init__(self):
        pass

    def rollup(self, hierarchy_level='monthly', year=None):
        """
        ROLL-UP Operation: Aggregate sales data up a dimension hierarchy.
        Levels: 'daily' -> 'monthly' -> 'quarterly' -> 'yearly'
        """
        where_clause = ""
        params = []
        if year and year != 'All':
            where_clause = "WHERE d.year = %s"
            params.append(int(year))

        if hierarchy_level == 'yearly':
            group_by = "d.year"
            select_cols = "d.year AS time_dimension"
            viva_desc = "ROLL-UP Operation: Aggregating transaction metrics from granular levels up to Yearly total summary."
        elif hierarchy_level == 'quarterly':
            group_by = "d.year, d.quarter"
            select_cols = "CONCAT('Q', d.quarter, ' ', d.year) AS time_dimension" if db_manager.db_type == 'mysql' else "('Q' || d.quarter || ' ' || d.year) AS time_dimension"
            viva_desc = "ROLL-UP Operation: Aggregating transaction metrics from Monthly/Daily level up to Quarterly summary."
        elif hierarchy_level == 'daily':
            group_by = "d.full_date"
            select_cols = "d.full_date AS time_dimension"
            viva_desc = "ROLL-UP Base Level: Viewing granular Daily transactions across the data warehouse."
        else: # monthly (default)
            group_by = "d.year, d.month, d.month_name"
            select_cols = "CONCAT(d.month_name, ' ', d.year) AS time_dimension" if db_manager.db_type == 'mysql' else "(d.month_name || ' ' || d.year) AS time_dimension"
            viva_desc = "ROLL-UP Operation: Aggregating daily transactions into Monthly summaries."

        sql = f"""
        SELECT
            {select_cols},
            COUNT(DISTINCT f.order_id) AS total_orders,
            SUM(f.quantity) AS total_units_sold,
            ROUND(SUM(f.total_amount), 2) AS total_revenue,
            ROUND(AVG(f.total_amount), 2) AS avg_transaction_value
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_id = d.date_id
        {where_clause}
        GROUP BY {group_by}
        ORDER BY MIN(d.date_id)
        """

        df = db_manager.query_to_df(sql, tuple(params))
        return {
            'operation': 'ROLL-UP',
            'hierarchy_level': hierarchy_level,
            'viva_description': viva_desc,
            'sql_executed': sql.strip(),
            'records': df.to_dict(orient='records') if not df.empty else []
        }

    def drilldown(self, target_year=2026, target_quarter=None, target_month=None):
        """
        DRILL-DOWN Operation: De-aggregating summary data into higher detail.
        Yearly Summary -> Quarterly Breakdown -> Monthly Breakdown -> Daily Details
        """
        params = [int(target_year)]
        viva_desc = f"DRILL-DOWN Operation: Zooming into details for Year {target_year}."

        if target_month:
            where_clause = "WHERE d.year = %s AND d.month = %s"
            params.append(int(target_month))
            group_by = "d.full_date"
            select_cols = "d.full_date AS time_breakdown, 'Daily Detail' AS level"
            viva_desc += f" -> Month {target_month} (Daily Transactions)"
        elif target_quarter:
            where_clause = "WHERE d.year = %s AND d.quarter = %s"
            params.append(int(target_quarter))
            group_by = "d.year, d.month, d.month_name"
            select_cols = "CONCAT(d.month_name, ' ', d.year) AS time_breakdown, 'Monthly Detail' AS level" if db_manager.db_type == 'mysql' else "(d.month_name || ' ' || d.year) AS time_breakdown, 'Monthly Detail' AS level"
            viva_desc += f" -> Quarter {target_quarter} (Monthly Breakdown)"
        else:
            where_clause = "WHERE d.year = %s"
            group_by = "d.year, d.quarter"
            select_cols = "CONCAT('Q', d.quarter, ' ', d.year) AS time_breakdown, 'Quarterly Detail' AS level" if db_manager.db_type == 'mysql' else "('Q' || d.quarter || ' ' || d.year) AS time_breakdown, 'Quarterly Detail' AS level"
            viva_desc += " (Quarterly Breakdown)"

        sql = f"""
        SELECT
            {select_cols},
            COUNT(DISTINCT f.order_id) AS total_orders,
            SUM(f.quantity) AS total_units_sold,
            ROUND(SUM(f.total_amount), 2) AS total_revenue
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_id = d.date_id
        {where_clause}
        GROUP BY {group_by}
        ORDER BY MIN(d.date_id)
        """

        df = db_manager.query_to_df(sql, tuple(params))
        return {
            'operation': 'DRILL-DOWN',
            'target_year': target_year,
            'target_quarter': target_quarter,
            'target_month': target_month,
            'viva_description': viva_desc,
            'sql_executed': sql.strip(),
            'records': df.to_dict(orient='records') if not df.empty else []
        }

    def slice(self, dimension='category', slice_value='Electronics'):
        """
        SLICE Operation: Selects a single 2D slice from the data cube by fixing 1 dimension value.
        """
        viva_desc = f"SLICE Operation: Fixing 1 dimension attribute ({dimension.upper()} = '{slice_value}') to extract a 2D slice of sales metrics."

        where_col = f"p.{dimension}" if dimension in ['category', 'subcategory', 'product_name'] else f"l.{dimension}"
        if dimension == 'year':
            where_col = "d.year"

        sql = f"""
        SELECT
            d.year,
            d.month_name,
            p.category,
            l.region,
            COUNT(DISTINCT f.order_id) AS total_orders,
            SUM(f.quantity) AS total_units_sold,
            ROUND(SUM(f.total_amount), 2) AS total_revenue
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_id = d.date_id
        JOIN DIM_PRODUCT p ON f.product_id = p.product_id
        JOIN DIM_LOCATION l ON f.location_id = l.location_id
        WHERE {where_col} = %s
        GROUP BY d.year, d.month_name, p.category, l.region
        ORDER BY d.year, MIN(d.month)
        """

        df = db_manager.query_to_df(sql, (slice_value,))
        return {
            'operation': 'SLICE',
            'dimension': dimension,
            'slice_value': slice_value,
            'viva_description': viva_desc,
            'sql_executed': sql.strip(),
            'records': df.to_dict(orient='records') if not df.empty else []
        }

    def dice(self, categories=None, regions=None, years=None):
        """
        DICE Operation: Selects a sub-cube by specifying criteria across 2 or more dimensions.
        Example: Category IN ('Electronics', 'Apparel') AND Region = 'South' AND Year = 2026
        """
        where_clauses = []
        params = []

        if categories and categories != ['All']:
            placeholders = ", ".join(["%s"] * len(categories))
            where_clauses.append(f"p.category IN ({placeholders})")
            params.extend(categories)

        if regions and regions != ['All']:
            placeholders = ", ".join(["%s"] * len(regions))
            where_clauses.append(f"l.region IN ({placeholders})")
            params.extend(regions)

        if years and years != ['All']:
            years_int = [int(y) for y in years if str(y).isdigit()]
            if years_int:
                placeholders = ", ".join(["%s"] * len(years_int))
                where_clauses.append(f"d.year IN ({placeholders})")
                params.extend(years_int)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        cat_str = ", ".join(categories) if categories else "All"
        reg_str = ", ".join(regions) if regions else "All"
        yr_str = ", ".join([str(y) for y in years]) if years else "All"

        viva_desc = f"DICE Operation: Filtering sub-cube across multiple dimensions (Categories: [{cat_str}], Regions: [{reg_str}], Years: [{yr_str}])."

        sql = f"""
        SELECT
            p.category,
            l.region,
            d.year,
            COUNT(DISTINCT f.order_id) AS total_orders,
            SUM(f.quantity) AS total_units_sold,
            ROUND(SUM(f.total_amount), 2) AS total_revenue
        FROM FACT_SALES f
        JOIN DIM_DATE d ON f.date_id = d.date_id
        JOIN DIM_PRODUCT p ON f.product_id = p.product_id
        JOIN DIM_LOCATION l ON f.location_id = l.location_id
        {where_sql}
        GROUP BY p.category, l.region, d.year
        ORDER BY total_revenue DESC
        """

        df = db_manager.query_to_df(sql, tuple(params))
        return {
            'operation': 'DICE',
            'filters': {'categories': categories, 'regions': regions, 'years': years},
            'viva_description': viva_desc,
            'sql_executed': sql.strip(),
            'records': df.to_dict(orient='records') if not df.empty else []
        }

olap_engine = OLAPEngine()
