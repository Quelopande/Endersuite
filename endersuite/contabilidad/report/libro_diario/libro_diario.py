import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_data(filters):
    sql = """
        SELECT
            mc.fecha_contable as fecha,
            mc.asiento_origen as numero,
            mc.cuenta as cuenta,
            mc.debe as debe,
            mc.haber as haber,
            mc.narracion as detalle
        FROM
            `tabMovimiento Contable` mc
        WHERE
            mc.fecha_contable BETWEEN %(from_date)s AND %(to_date)s
    """
    
    if filters.get("cuenta"):
        sql += " AND mc.cuenta = %(cuenta)s"

    sql += " ORDER BY mc.fecha_contable ASC, mc.creation ASC"
    
    data = frappe.db.sql(sql, filters, as_dict=True)
    
    result = []
    for row in data:
        descripcion_completa = f"{row.cuenta}"
        if row.detalle:
            descripcion_completa += f" - {row.detalle}"

        result.append({
            "fecha": row.fecha,
            "numero": row.numero,
            "cuenta_y_detalle": descripcion_completa,
            "debe": row.debe,
            "haber": row.haber
        })

    return result

def get_columns():
    return [
        {
            "fieldname": "fecha",
            "label": _("Fecha"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "numero",
            "label": _("Número"),
            "fieldtype": "Link",
            "options": "Asiento Contable",
            "width": 140
        },
        {
            "fieldname": "cuenta_y_detalle",
            "label": _("Cuenta y detalle"),
            "fieldtype": "Data",
            "width": 300
        },
        {
            "fieldname": "debe",
            "label": _("DEBE"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "haber",
            "label": _("HABER"),
            "fieldtype": "Currency",
            "width": 120
        }
    ]