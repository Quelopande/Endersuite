# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SesionPOS(Document):
	def before_save(self):
		"""Calcular totales del sistema antes de guardar"""
		self.calcular_totales_sistema()
	
	def validate(self):
		"""Validaciones antes de guardar"""
		# Validar que no haya otra sesión abierta para este usuario
		if self.estado == "Abierta" and not self.is_new():
			otras_abiertas = frappe.db.count(
				"Sesion POS",
				filters={
					"usuario": self.usuario,
					"estado": "Abierta",
					"name": ["!=", self.name]
				}
			)
			if otras_abiertas > 0:
				frappe.throw(_("Ya existe una sesión abierta para este usuario. Debe cerrarla antes de abrir una nueva."))
		
		# Si está cerrada, validar campos requeridos
		if self.estado == "Cerrada":
			if not self.fecha_hora_cierre:
				frappe.throw(_("Debe especificar la fecha y hora de cierre"))
			if self.efectivo_contado is None:
				frappe.throw(_("Debe especificar el efectivo contado para el arqueo"))
	
	def before_submit(self):
		"""Validar que esté cerrada antes de submit"""
		if self.estado != "Cerrada":
			frappe.throw(_("Solo puede enviar sesiones cerradas"))
		
		# Calcular diferencia de arqueo
		self.diferencia = (self.efectivo_contado or 0) - ((self.total_efectivo_sistema or 0) + (self.monto_apertura or 0))
	
	def calcular_totales_sistema(self):
		"""Calcular totales por método de pago desde las ventas válidas (no canceladas)"""
		if not self.ventas:
			# Resetear totales si no hay ventas
			self.total_efectivo_sistema = 0
			self.total_tarjeta_sistema = 0
			self.total_transferencia_sistema = 0
			self.total_cheque_sistema = 0
			self.total_general_sistema = 0
			return

		# Obtener todas las notas de venta válidas (solo enviadas, no canceladas)
		notas_venta = []
		for v in self.ventas:
			if v.nota_de_venta:
				# Verificar que la nota existe y no está cancelada
				docstatus = frappe.db.get_value("Nota de Venta", v.nota_de_venta, "docstatus")
				if docstatus == 1:  # Solo notas enviadas (no borradores ni canceladas)
					notas_venta.append(v.nota_de_venta)

		if not notas_venta:
			# Si no hay ventas válidas, resetear totales
			self.total_efectivo_sistema = 0
			self.total_tarjeta_sistema = 0
			self.total_transferencia_sistema = 0
			self.total_cheque_sistema = 0
			self.total_general_sistema = 0
			return

		# Calcular totales reales desde las notas de venta
		totales_por_metodo = {}
		total_general = 0

		for nota_name in notas_venta:
			# Obtener métodos de pago de cada nota
			metodos = frappe.get_all(
				"Metodos de Pago Nota",
				filters={"parent": nota_name, "parenttype": "Nota de Venta"},
				fields=["metodo", "monto"]
			)

			for metodo_pago in metodos:
				metodo = metodo_pago.metodo
				monto = metodo_pago.monto or 0

				if metodo not in totales_por_metodo:
					totales_por_metodo[metodo] = 0
				totales_por_metodo[metodo] += monto
				total_general += monto

		# Asignar totales a los campos correspondientes
		# Mapear métodos de pago conocidos a los campos del doctype
		self.total_efectivo_sistema = totales_por_metodo.get("Efectivo", 0)
		self.total_tarjeta_sistema = totales_por_metodo.get("Tarjeta", 0) + totales_por_metodo.get("Tarjeta de Crédito", 0) + totales_por_metodo.get("Tarjeta de Débito", 0)
		self.total_transferencia_sistema = totales_por_metodo.get("Transferencia", 0) + totales_por_metodo.get("Transferencia Bancaria", 0)
		self.total_cheque_sistema = totales_por_metodo.get("Cheque", 0)
		self.total_general_sistema = total_general
