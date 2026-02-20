# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class CuentaContable(NestedSet):
	def onload(self):
		# Este evento se dispara cada vez que abres el formulario de la cuenta
		self.generar_html_t()

	def generar_html_t(self):
		# Consulta SQL Corregida:
		# 1. Busca en la tabla hija 'tabDetalle Asiento' (alias child)
		# 2. Une con el padre 'tabAsiento Contable' (alias parent)
		# 3. Importante: Filtra solo asientos validados (docstatus=1)
		
		sql = """
			SELECT 
				child.debito, 
				child.credito, 
				parent.posting_date, 
				parent.name as asiento_id
			FROM `tabDetalle Asiento` child
			INNER JOIN `tabAsiento Contable` parent ON child.parent = parent.name
			WHERE 
				child.cuenta = %s 
				AND parent.docstatus = 1
			ORDER BY parent.posting_date DESC, parent.creation DESC
			LIMIT 50
		"""
		
		# Ejecutamos la consulta
		movimientos = frappe.db.sql(sql, (self.name), as_dict=True)

		# Calculamos los totales matemáticos
		suma_debe = sum(flt(m.debito) for m in movimientos)
		suma_haber = sum(flt(m.credito) for m in movimientos)
		saldo = suma_debe - suma_haber

		# Generamos el HTML visual
		self.construir_visualizacion(movimientos, suma_debe, suma_haber, saldo)

	def construir_visualizacion(self, movimientos, debe, haber, saldo):
		filas_html = ""
		estilo_borde = "border-right: 2px solid #333;"
		
		for m in movimientos:
			# Formato de moneda con comas
			val_debe = f"{m.debito:,.2f}" if m.debito > 0 else ""
			val_haber = f"{m.credito:,.2f}" if m.credito > 0 else ""
			
			# Crear enlace para ir al asiento al hacer clic
			link = frappe.utils.get_url_to_form('Asiento Contable', m.asiento_id)
			
			filas_html += f"""
			<tr style="border-bottom: 1px solid #eee;">
				<td style="{estilo_borde} text-align: right; padding: 4px; font-family: monospace;">
					<a href="{link}" style="text-decoration: none; color: inherit;">{val_debe}</a>
				</td>
				<td style="text-align: right; padding: 4px; font-family: monospace;">
					<a href="{link}" style="text-decoration: none; color: inherit;">{val_haber}</a>
				</td>
			</tr>
			"""

		# HTML Final que se inyectará en el campo 'visualizacion_t'
		html_final = f"""
		<div style="font-family: sans-serif; width: 100%; border: 1px solid #ddd; padding: 15px; border-radius: 4px; background-color: #fff;">
			<h3 style="text-align: center; border-bottom: 2px solid #333; margin: 0 0 10px 0; padding-bottom: 5px;">{self.nombre_cuenta}</h3>
			
			<div style="display: flex; border-bottom: 2px solid #333; font-weight: bold; background-color: #f9f9f9;">
				<div style="flex: 1; text-align: center; {estilo_borde} padding: 5px;">DEBE</div>
				<div style="flex: 1; text-align: center; padding: 5px;">HABER</div>
			</div>
			
			<table style="width: 100%; border-collapse: collapse;">
				{filas_html}
				
				<tr style="border-top: 2px solid #333; font-weight: bold; background-color: #f0f0f0;">
					<td style="{estilo_borde} text-align: right; padding: 8px;">{debe:,.2f}</td>
					<td style="text-align: right; padding: 8px;">{haber:,.2f}</td>
				</tr>
			</table>
			
			<div style="text-align: center; margin-top: 15px; font-size: 1.1em; font-weight: bold; color: {'#28a745' if saldo >= 0 else '#dc3545'};">
				Saldo Actual: {saldo:,.2f}
			</div>
		</div>
		"""
		
		# Enviamos el HTML al frontend a través de la propiedad __onload
		self.set_onload('html_cuenta_t', html_final)
