# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Producto(Document):
	def validate(self):
		"""Calcular automáticamente los precios e impuestos para cada lista de precios"""
		self.calcular_precios()
	
	def calcular_precios(self):
		"""Calcular impuestos y ganancia para cada fila de precios"""
		if not self.table_rzld:
			return
		
		# Obtener información del impuesto
		tasa_impuesto = 0
		incluido_en_precio = False
		
		if self.tipo_de_impuesto:
			impuesto = frappe.get_doc("Impuestos", self.tipo_de_impuesto)
			tasa_impuesto = impuesto.porciento_impuesto or 0
			incluido_en_precio = impuesto.incluido_en_el_precio or False
		
		costo = self.costo or 0
		
		for row in self.table_rzld:
			precio_unitario = row.precio_unitario or 0
			
			if incluido_en_precio:
				# IVA INCLUIDO - El precio ya incluye impuestos (RETENIDO)
				# La empresa absorbe/paga el impuesto
				precio_sin_impuestos = precio_unitario / (1 + (tasa_impuesto / 100))
				row.impuestos_retenidos = precio_unitario - precio_sin_impuestos
				row.impuestos_trasladados = 0
				row.precio_total = precio_unitario
				# Ganancia = Precio - Costo - Impuesto que paga la empresa
				row.ganancia_bruta = precio_unitario - costo - row.impuestos_retenidos
			else:
				# IVA NO INCLUIDO - Los impuestos se suman al precio (TRASLADADO)
				# El cliente paga el impuesto
				impuesto_calculado = precio_unitario * (tasa_impuesto / 100)
				row.impuestos_retenidos = 0
				row.impuestos_trasladados = impuesto_calculado
				row.precio_total = precio_unitario + impuesto_calculado
				# Ganancia = Precio - Costo (el impuesto lo paga el cliente, no afecta ganancia)
				row.ganancia_bruta = precio_unitario - costo
