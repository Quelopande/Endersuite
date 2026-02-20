frappe.query_reports["Libro Diario"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("Desde Fecha"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("Hasta Fecha"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_end(),
            "reqd": 1
        },
        {
            "fieldname": "cuenta",
            "label": __("Filtrar por Cuenta"),
            "fieldtype": "Link",
            "options": "Cuenta Contable"
        }
    ]
};