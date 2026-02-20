# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AsientoContable(Document):
	def validate(self):
		# Esta función corre AUTOMÁTICAMENTE al intentar guardar
		self.validar_que_cuadre()

	def validar_que_cuadre(self):
		total_debe = 0.0
		total_haber = 0.0
		
		# Recorremos la tabla 'detalle' para sumar
		for row in self.detalle:
			total_debe += flt(row.debito)
			total_haber += flt(row.credito)
			
		diferencia = total_debe - total_haber
		
		# Validamos con una pequeña tolerancia para decimales
		if abs(diferencia) > 0.009:
			frappe.throw(_(
				"<b>¡Error de Ecuación Contable!</b><br>"
				"El asiento no cuadra (Debe ≠ Haber).<br><br>"
				"Total Debe: {0:,.2f}<br>"
				"Total Haber: {1:,.2f}<br>"
				"<b>Diferencia: {2:,.2f}</b>"
			).format(total_debe, total_haber, diferencia))
