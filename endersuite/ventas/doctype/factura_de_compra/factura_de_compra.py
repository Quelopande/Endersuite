# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FacturadeCompra(Document):
	def validate(self):
		self.calcular_totales()

	def calcular_totales(self):
		suma_subtotal = 0.0
		suma_impuestos_trasladados = 0.0
		suma_impuestos_retenidos = 0.0

		# Recorremos la tabla de productos
		for item in self.tabla_productos_compra:
			# 1. Obtener valores seguros
			cantidad = item.cantidad or 0
			precio = item.valor or 0
			dcto_percent = item.descuento or 0
			
			# 2. Calcular importe bruto
			importe_bruto = cantidad * precio
			
			# 3. Calcular neto con descuento
			monto_descuento = importe_bruto * (dcto_percent / 100)
			importe_neto = importe_bruto - monto_descuento
			
			# Guardar en la linea
			item.total_linea = importe_neto

			# 4. Calcular Impuestos
			tasa_iva = item.porcentaje_iva or 0
			tasa_ret = item.porcentaje_retencion or 0

			impuesto_linea = importe_neto * (tasa_iva / 100)
			retencion_linea = importe_neto * (tasa_ret / 100)

			# 5. Sumar a acumuladores
			suma_subtotal += importe_neto
			suma_impuestos_trasladados += impuesto_linea
			suma_impuestos_retenidos += retencion_linea

		# Asignar totales al padre
		self.subtotal = suma_subtotal
		self.total_impuestos_trasladados = suma_impuestos_trasladados
		self.total_impuestos_retenidos = suma_impuestos_retenidos

		descuento_global = self.descuento_total or 0.0

		# Calculo final
		self.total = (self.subtotal + self.total_impuestos_trasladados) - self.total_impuestos_retenidos - descuento_global
