# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FormatodeTicket(Document):
	def validate(self):
		"""Validar que solo haya un formato predeterminado"""
		if self.predeterminado:
			# Desmarcar otros formatos predeterminados
			otros = frappe.get_all(
				"Formato de Ticket",
				filters={"name": ["!=", self.name], "predeterminado": 1}
			)
			for otro in otros:
				frappe.db.set_value("Formato de Ticket", otro.name, "predeterminado", 0)
	
	def before_save(self):
		"""Establecer plantillas por defecto si están vacías"""
		if not self.header_html:
			self.header_html = self.get_default_header()
		
		if not self.items_html:
			self.items_html = self.get_default_items()
		
		if not self.footer_html:
			self.footer_html = self.get_default_footer()
		
		if not self.estilos_css:
			self.estilos_css = self.get_default_css()
	
	def get_default_header(self):
		return """<div class="header">
    {% if compania %}
    <h2>{{ compania.name }}</h2>
    {% if compania.razon_social %}
    <p>{{ compania.razon_social }}</p>
    {% endif %}
    {% else %}
    <h2>{{ perfil_pos or "Punto de Venta" }}</h2>
    {% endif %}
    
    <p>TICKET DE VENTA</p>
    <p>{{ doc.name }}</p>
    <p>{{ frappe.format_date(doc.fecha_y_hora_de_venta, 'dd/MM/yyyy HH:mm') }}</p>
    
    {% if doc.cliente %}
    <p>Cliente: {{ doc.cliente }}</p>
    {% endif %}
</div>"""
	
	def get_default_items(self):
		return """<table class="items-table">
    <thead>
        <tr>
            <th>Producto</th>
            <th>Cant</th>
            <th>Precio</th>
            <th>Total</th>
        </tr>
    </thead>
    <tbody>
        {% for item in doc.tabla_de_productos %}
        <tr>
            <td>{{ item.producto }}</td>
            <td>{{ item.cantidad }}</td>
            <td>{{ frappe.format_value(item.precio_unitario, {'fieldtype': 'Currency'}) }}</td>
            <td>{{ frappe.format_value(item.total_linea, {'fieldtype': 'Currency'}) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>"""
	
	def get_default_footer(self):
		return """<div class="totals">
    <div class="total-row">
        <span>Subtotal:</span>
        <span>{{ frappe.format_value(doc.subtotal, {'fieldtype': 'Currency'}) }}</span>
    </div>
    <div class="total-row">
        <span>Impuestos:</span>
        <span>{{ frappe.format_value(doc.total_impuestos, {'fieldtype': 'Currency'}) }}</span>
    </div>
    <div class="total-row total-final">
        <span>TOTAL:</span>
        <span>{{ frappe.format_value(doc.total_final, {'fieldtype': 'Currency'}) }}</span>
    </div>
</div>

<div class="payment-methods">
    <strong>Métodos de Pago:</strong><br>
    {% for mp in doc.metodos_pago_nota %}
    {{ mp.metodo }}: {{ frappe.format_value(mp.monto, {'fieldtype': 'Currency'}) }}<br>
    {% endfor %}
</div>

{% if doc.cambio and doc.cambio > 0 %}
<div class="cambio">
    <strong>Cambio: {{ frappe.format_value(doc.cambio, {'fieldtype': 'Currency'}) }}</strong>
</div>
{% endif %}

<div class="footer-message">
    <p>¡Gracias por su compra!</p>
    <p>{{ frappe.session.user }} | {{ doc.sesion_pos }}</p>
</div>"""
	
	def get_default_css(self):
		return """/* Estilos adicionales personalizados */
.header {
    border-bottom: 2px dashed #000;
    padding-bottom: 10px;
    margin-bottom: 10px;
}

.items-table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
}

.items-table th,
.items-table td {
    padding: 5px;
    text-align: left;
}

.items-table th {
    border-bottom: 1px solid #000;
}

.totals {
    border-top: 2px dashed #000;
    padding-top: 10px;
    margin-top: 10px;
}

.total-row {
    display: flex;
    justify-content: space-between;
    padding: 3px 0;
}

.total-final {
    font-size: 14px;
    font-weight: bold;
    border-top: 1px solid #000;
    padding-top: 8px;
    margin-top: 5px;
}

.payment-methods {
    margin: 10px 0;
    padding: 10px 0;
    border-top: 2px dashed #000;
}

.cambio {
    background: #f0f0f0;
    padding: 10px;
    margin: 10px 0;
    text-align: center;
}

.footer-message {
    text-align: center;
    margin-top: 15px;
    font-size: 9px;
}"""


@frappe.whitelist()
def get_formato_predeterminado():
	"""Obtener el formato de ticket predeterminado"""
	formato = frappe.get_value(
		"Formato de Ticket",
		{"predeterminado": 1},
		["name", "ancho_ticket", "fuente", "tamano_fuente"],
		as_dict=True
	)
	
	if not formato:
		# Si no hay predeterminado, usar el primero disponible
		formato = frappe.get_value(
			"Formato de Ticket",
			filters={},
			fieldname=["name", "ancho_ticket", "fuente", "tamano_fuente"],
			as_dict=True
		)
	
	return formato


@frappe.whitelist()
def generar_ticket_html(nota_venta_name, formato_name=None):
	"""
	Generar HTML del ticket usando un formato específico
	
	Args:
		nota_venta_name: Nombre de la nota de venta
		formato_name: Nombre del formato (opcional, usa predeterminado si no se especifica)
	"""
	from jinja2 import Template
	
	# Obtener nota de venta
	nota = frappe.get_doc("Nota de Venta", nota_venta_name)
	
	# Obtener formato
	if not formato_name:
		formato = frappe.get_doc("Formato de Ticket", {"predeterminado": 1})
		if not formato:
			formato = frappe.get_all("Formato de Ticket", limit=1)
			if formato:
				formato = frappe.get_doc("Formato de Ticket", formato[0].name)
			else:
				frappe.throw("No hay formatos de ticket configurados")
	else:
		formato = frappe.get_doc("Formato de Ticket", formato_name)
	
	# Obtener datos adicionales
	compania = None
	perfil_pos = None
	
	if nota.perfil_pos:
		perfil = frappe.get_doc("Perfil de POS", nota.perfil_pos)
		perfil_pos = perfil.name
		if perfil.compania:
			compania = frappe.get_doc("Compania", perfil.compania)
	
	# Contexto para renderizar
	context = {
		"doc": nota,
		"compania": compania,
		"perfil_pos": perfil_pos,
		"frappe": frappe
	}
	
	# Renderizar plantillas
	header_template = Template(formato.header_html or "")
	items_template = Template(formato.items_html or "")
	footer_template = Template(formato.footer_html or "")
	
	header_html = header_template.render(context)
	items_html = items_template.render(context)
	footer_html = footer_template.render(context)
	
	# Construir HTML completo
	ancho_map = {
		"58mm": "58mm",
		"80mm": "80mm",
		"Carta": "210mm"
	}
	
	ancho = ancho_map.get(formato.ancho_ticket, "80mm")
	
	html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @media print {{
            @page {{
                size: {ancho} auto;
                margin: 0;
            }}
            body {{
                width: {ancho};
                margin: 0;
                padding: 5mm;
            }}
        }}
        
        body {{
            font-family: '{formato.fuente or "Courier New"}', monospace;
            font-size: {formato.tamano_fuente or 10}px;
            line-height: 1.4;
            max-width: {ancho};
            margin: 0 auto;
            padding: 5mm;
        }}
        
        h2, h3 {{
            margin: 5px 0;
        }}
        
        p {{
            margin: 2px 0;
        }}
        
        .header {{
            text-align: {formato.alinear_header or "center"};
        }}
        
        {formato.estilos_css or ""}
    </style>
</head>
<body>
    {header_html}
    {items_html}
    {footer_html}
</body>
</html>"""
	
	return html
