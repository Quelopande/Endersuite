# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import add_days, getdate


class Ordendeventa(Document):
	def validate(self):
		"""Validaciones generales"""
		self.ensure_cliente()
		self.ensure_fecha_entrega()
		self.validar_productos()
		self.validar_fechas()
		self.calculate_taxes()
		self.calculate_totals()

	def before_insert(self):
		"""Validaciones antes de insertar"""
		if not self.naming_series:
			self.naming_series = "OV-.YYYY.-.#####"

	def on_submit(self):
		"""Actualizar estado al confirmar"""
		if self.estado == "Borrador":
			self.estado = "Confirmada"
			self.db_set('estado', 'Confirmada', update_modified=False)

	def ensure_cliente(self):
		"""Asegurar que hay un cliente, sino usar Cliente Genérico"""
		if not self.cliente:
			if not frappe.db.exists("Cliente", "Cliente Genérico"):
				cliente = frappe.new_doc("Cliente")
				cliente.nombre_del_cliente = "Cliente Genérico"
				cliente.flags.ignore_mandatory = True
				cliente.insert(ignore_permissions=True)
			self.cliente = "Cliente Genérico"

	def ensure_fecha_entrega(self):
		"""Establecer fecha de entrega estimada por defecto (7 días)"""
		if not self.fecha_entrega_estimada and self.fecha:
			self.fecha_entrega_estimada = add_days(self.fecha, 7)

	def validar_productos(self):
		"""Valida que se hayan agregado productos"""
		if not self.productos or len(self.productos) == 0:
			frappe.throw(_("Debe agregar al menos un producto a la orden de venta"))

		# Validar cantidades y precios positivos
		for idx, row in enumerate(self.productos, start=1):
			if row.cantidad <= 0:
				frappe.throw(_("La cantidad debe ser mayor a cero en la línea #{0}").format(idx))
			if row.precio_unitario < 0:
				frappe.throw(_("El precio unitario no puede ser negativo en la línea #{0}").format(idx))

	def validar_fechas(self):
		"""Valida que las fechas sean consistentes"""
		if self.fecha_entrega_estimada and self.fecha:
			if self.fecha_entrega_estimada < self.fecha:
				frappe.throw(_("La fecha de entrega estimada no puede ser anterior a la fecha de la orden"))

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
	def cambiar_estado(self, nuevo_estado):
		"""Cambia el estado de la orden"""
		estados_validos = ["Borrador", "Confirmada", "En Entrega", "Cerrada", "Cancelada"]

		if nuevo_estado not in estados_validos:
			frappe.throw(_("Estado inválido"))

		self.estado = nuevo_estado
		self.save()
		frappe.msgprint(_("Estado actualizado a {0}").format(nuevo_estado))
		return self.estado

	@frappe.whitelist()
	def crear_nota_de_venta(self):
		"""Crear Nota de Venta desde esta orden"""
		if self.estado != "Confirmada":
			frappe.throw(_("Solo se pueden crear notas de venta desde órdenes confirmadas"))

		# Validar almacén
		if not self.almacen:
			frappe.throw(_("Debe especificar un almacén para crear la nota de venta"))

		# Crear Nota de Venta
		nota = frappe.new_doc("Nota de Venta")
		nota.cliente = self.cliente
		nota.vendedor = self.vendedor
		nota.almacen = self.almacen
		nota.lista_de_precios = self.lista_de_precios

		# Copiar productos
		for item in self.productos:
			nota.append("tabla_de_productos", {
				"producto": item.producto,
				"cantidad": item.cantidad,
				"precio_unitario": item.precio_unitario,
				"descuento_porcentaje": item.descuento_porcentaje
			})

		# Copiar descuento global
		nota.descuento_global_porcentaje = self.descuento_global_porcentaje

		nota.insert()

		# Actualizar estado a "En Entrega"
		self.estado = "En Entrega"
		self.save()

		frappe.msgprint(_("Nota de Venta {0} creada exitosamente").format(nota.name))
		return nota.name

	def get_dashboard_data(self):
		"""Datos para el dashboard"""
		return {
			'fieldname': 'orden_de_venta',
			'transactions': [
				{
					'label': _('Relacionado'),
					'items': ['Nota de Venta', 'Factura de Venta']
				}
			]
		}
