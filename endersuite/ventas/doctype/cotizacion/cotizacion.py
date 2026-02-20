# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import add_days, getdate


class Cotizacion(Document):
	def validate(self):
		"""Validaciones generales"""
		self.ensure_cliente()
		self.ensure_fecha_vencimiento()
		self.validar_productos()
		self.calculate_taxes()
		self.calculate_totals()

	def before_insert(self):
		"""Validaciones antes de insertar"""
		if not self.naming_series:
			self.naming_series = "COT-.YYYY.-.#####"

	def ensure_cliente(self):
		"""Asegurar que hay un cliente, sino usar Cliente Genérico"""
		if not self.cliente:
			# Buscar o crear Cliente Genérico
			if not frappe.db.exists("Cliente", "Cliente Genérico"):
				cliente = frappe.new_doc("Cliente")
				cliente.nombre_del_cliente = "Cliente Genérico"
				cliente.flags.ignore_mandatory = True
				cliente.insert(ignore_permissions=True)
			self.cliente = "Cliente Genérico"

	def ensure_fecha_vencimiento(self):
		"""Establecer fecha de vencimiento por defecto (30 días)"""
		if not self.fecha_vencimiento and self.fecha:
			self.fecha_vencimiento = add_days(self.fecha, 30)

	def validar_productos(self):
		"""Valida que se hayan agregado productos"""
		if not self.productos or len(self.productos) == 0:
			frappe.throw(_("Debe agregar al menos un producto a la cotización"))

		# Validar cantidades y precios positivos
		for idx, row in enumerate(self.productos, start=1):
			if row.cantidad <= 0:
				frappe.throw(_("La cantidad debe ser mayor a cero en la línea #{0}").format(idx))
			if row.precio_unitario < 0:
				frappe.throw(_("El precio unitario no puede ser negativo en la línea #{0}").format(idx))

	def calculate_taxes(self):
		"""Calcular impuestos línea por línea desde producto.tipo_de_impuesto"""
		for item in self.productos:
			# Calcular subtotal sin impuesto
			item.subtotal_sin_impuesto = item.cantidad * item.precio_unitario

			# Calcular descuento
			if item.descuento_porcentaje:
				item.descuento_monto = item.subtotal_sin_impuesto * (item.descuento_porcentaje / 100)
			else:
				item.descuento_monto = 0

			# Base imponible = subtotal - descuento
			item.base_imponible = item.subtotal_sin_impuesto - item.descuento_monto

			# Obtener porcentaje de impuesto
			if item.impuesto:
				porcentaje = frappe.get_value("Impuestos", item.impuesto, "porciento_impuesto") or 0
				item.porcentaje_impuesto = porcentaje
				item.impuesto_monto = item.base_imponible * (porcentaje / 100)
			else:
				item.porcentaje_impuesto = 0
				item.impuesto_monto = 0

			# Total línea = base imponible + impuesto
			item.total_linea = item.base_imponible + item.impuesto_monto

	def calculate_totals(self):
		"""Calcular subtotal, descuentos, base imponible, total"""
		# Sumar todos los items
		self.subtotal = sum([item.subtotal_sin_impuesto or 0 for item in self.productos])

		# Calcular descuento global
		if self.descuento_global_porcentaje:
			self.descuento_global_monto = self.subtotal * (self.descuento_global_porcentaje / 100)
		else:
			self.descuento_global_monto = 0

		# Base imponible total
		subtotal_con_descuento = sum([item.base_imponible or 0 for item in self.productos])
		self.base_imponible_total = subtotal_con_descuento - self.descuento_global_monto

		# Total impuestos
		self.total_impuestos = sum([item.impuesto_monto or 0 for item in self.productos])

		# Ajustar impuestos si hay descuento global
		if self.descuento_global_monto > 0 and subtotal_con_descuento > 0:
			factor = self.base_imponible_total / subtotal_con_descuento
			self.total_impuestos = self.total_impuestos * factor

		# Total final
		self.total_final = self.base_imponible_total + self.total_impuestos

	@frappe.whitelist()
	def convertir_a_orden_venta(self):
		"""Convertir cotización a orden de venta"""
		if self.workflow_state != "Aceptada":
			frappe.throw(_("Solo se pueden convertir cotizaciones aceptadas"))

		# Crear Orden de Venta
		orden = frappe.new_doc("Orden de Venta")
		orden.cliente = self.cliente
		orden.vendedor = self.vendedor
		orden.fecha = getdate()
		orden.lista_de_precios = self.lista_de_precios
		orden.referencia_cotizacion = self.name

		# Copiar productos
		for item in self.productos:
			orden.append("productos", {
				"producto": item.producto,
				"cantidad": item.cantidad,
				"precio_unitario": item.precio_unitario,
				"descuento_porcentaje": item.descuento_porcentaje
			})

		# Copiar descuento global
		orden.descuento_global_porcentaje = self.descuento_global_porcentaje

		orden.insert()

		# Marcar cotización como convertida
		self.workflow_state = "Convertida"
		self.save()

		frappe.msgprint(_("Orden de Venta {0} creada exitosamente").format(orden.name))
		return orden.name

	def get_dashboard_data(self):
		"""Datos para el dashboard"""
		return {
			'fieldname': 'referencia_cotizacion',
			'transactions': [
				{
					'label': _('Relacionado'),
					'items': ['Orden de Venta']
				}
			]
		}
