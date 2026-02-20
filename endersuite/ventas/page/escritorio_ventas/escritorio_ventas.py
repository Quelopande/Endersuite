import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate, formatdate, get_first_day, get_last_day

@frappe.whitelist()
def get_dashboard_data():
    data = {}
    
    # Date ranges
    today = nowdate()
    first_day_month = get_first_day(today)
    last_day_month = get_last_day(today)
    
    # Metrics: Today
    data['sales_today'] = frappe.db.sql("""
        SELECT SUM(total_final) FROM `tabNota de Venta`
        WHERE DATE(fecha_y_hora_de_venta) = %s AND docstatus = 1
    """, (today,))[0][0] or 0
    
    data['orders_today'] = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabNota de Venta`
        WHERE DATE(fecha_y_hora_de_venta) = %s AND docstatus = 1
    """, (today,))[0][0] or 0

    # Metrics: This Month
    data['sales_month'] = frappe.db.sql("""
        SELECT SUM(total_final) FROM `tabNota de Venta`
        WHERE DATE(fecha_y_hora_de_venta) BETWEEN %s AND %s AND docstatus = 1
    """, (first_day_month, last_day_month))[0][0] or 0
    
    data['orders_month'] = frappe.db.sql("""
        SELECT COUNT(*) FROM `tabNota de Venta`
        WHERE DATE(fecha_y_hora_de_venta) BETWEEN %s AND %s AND docstatus = 1
    """, (first_day_month, last_day_month))[0][0] or 0
    
    # Top Selling Products (This Month)
    top_products_raw = frappe.db.sql("""
        SELECT t.producto, SUM(t.cantidad) as qty, SUM(t.total_linea) as amount
        FROM `tabTabla de Productos` t
        JOIN `tabNota de Venta` n ON t.parent = n.name
        WHERE DATE(n.fecha_y_hora_de_venta) BETWEEN %s AND %s
        AND n.docstatus = 1
        GROUP BY t.producto
        ORDER BY amount DESC
        LIMIT 5
    """, (first_day_month, last_day_month), as_dict=True)
    
    # Enrich with product images
    data['top_products'] = []
    for product in top_products_raw:
        product_doc = frappe.get_doc("Producto", product.producto)
        data['top_products'].append({
            'producto': product.producto,
            'qty': product.qty,
            'amount': product.amount,
            'imagen': product_doc.imagen if hasattr(product_doc, 'imagen') else None
        })
    
    
    # Sales Trend (Last 30 Days)
    thirty_days_ago = add_days(today, -30)
    sales_trend = frappe.db.sql("""
        SELECT DATE(fecha_y_hora_de_venta) as date, SUM(total_final) as total
        FROM `tabNota de Venta`
        WHERE DATE(fecha_y_hora_de_venta) >= %s AND docstatus = 1
        GROUP BY DATE(fecha_y_hora_de_venta)
        ORDER BY DATE(fecha_y_hora_de_venta) ASC
    """, (thirty_days_ago,), as_dict=True)
    
    data['sales_trend'] = {
        'labels': [formatdate(d.date) for d in sales_trend],
        'values': [d.total for d in sales_trend]
    }

    return data
