# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class NotadeVenta(Document):
	def validate(self):
		"""Validaciones generales"""
		self.ensure_cliente()
		self.validate_sesion_pos()
		self.calculate_taxes()
		self.calculate_totals()
		self.validate_payment_methods()
		self.validar_metodos_de_pago_duplicados()
		self.validate_stock_availability()

	def before_insert(self):
		"""Validaciones antes de insertar"""
		# Asegurar que el naming_series esté presente
		if not self.naming_series:
			self.naming_series = "NV-.YYYY.-.MM.-.#####"

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

	def validate_sesion_pos(self):
		"""Validar que la sesión POS está abierta si se especifica"""
		if self.sesion_pos:
			sesion = frappe.get_value("Sesion POS", self.sesion_pos, ["estado", "usuario"], as_dict=True)
			if not sesion:
				frappe.throw(_("La sesión POS {0} no existe").format(self.sesion_pos))
			if sesion.estado != "Abierta":
				frappe.throw(_("La sesión POS {0} no está abierta").format(self.sesion_pos))

	def calculate_taxes(self):
		"""Calcular impuestos línea por línea desde producto.tipo_de_impuesto"""
		from frappe.utils import flt
		
		for item in self.tabla_de_productos:
			# Convertir a float para evitar errores de tipo
			cantidad = flt(item.cantidad)
			precio_unitario = flt(item.precio_unitario)
			descuento_porcentaje = flt(item.descuento_porcentaje)
			
			# Calcular subtotal sin impuesto
			item.subtotal_sin_impuesto = cantidad * precio_unitario

			# Calcular descuento
			if descuento_porcentaje:
				item.descuento_monto = item.subtotal_sin_impuesto * (descuento_porcentaje / 100)
			else:
				item.descuento_monto = 0

			# Base imponible = subtotal - descuento
			item.base_imponible = item.subtotal_sin_impuesto - item.descuento_monto

			# Obtener porcentaje de impuesto
			if item.impuesto:
				porcentaje = flt(frappe.get_value("Impuestos", item.impuesto, "porciento_impuesto") or 0)
				item.porcentaje_impuesto = porcentaje
				item.impuesto_monto = item.base_imponible * (porcentaje / 100)
			else:
				item.porcentaje_impuesto = 0
				item.impuesto_monto = 0

			# Total línea = base imponible + impuesto
			item.total_linea = item.base_imponible + item.impuesto_monto

	def calculate_totals(self):
		"""Calcular subtotal, descuentos, base imponible, total"""
		from frappe.utils import flt
		
		# Sumar todos los items
		self.subtotal = sum([flt(item.subtotal_sin_impuesto) for item in self.tabla_de_productos])

		# Calcular descuento global
		descuento_global_porcentaje = flt(self.descuento_global_porcentaje)
		if descuento_global_porcentaje:
			self.descuento_global_monto = self.subtotal * (descuento_global_porcentaje / 100)
		else:
			self.descuento_global_monto = 0

		# Base imponible total
		subtotal_con_descuento = sum([flt(item.base_imponible) for item in self.tabla_de_productos])
		self.base_imponible_total = subtotal_con_descuento - self.descuento_global_monto

		# Total impuestos
		self.total_impuestos = sum([flt(item.impuesto_monto) for item in self.tabla_de_productos])

		# Ajustar impuestos si hay descuento global
		if self.descuento_global_monto > 0 and subtotal_con_descuento > 0:
			factor = self.base_imponible_total / subtotal_con_descuento
			self.total_impuestos = self.total_impuestos * factor

		# Total final
		self.total_final = self.base_imponible_total + self.total_impuestos

		# Calcular total pagado y cambio
		self.total_pagado = sum([flt(metodo.monto) for metodo in self.metodos_pago_nota])
		self.cambio = max(0, self.total_pagado - self.total_final)

	def validate_payment_methods(self):
		"""Validar que suma de métodos de pago >= total"""
		if not self.metodos_pago_nota:
			frappe.throw(_("Debe especificar al menos un método de pago"))

		total_pagado = sum([m.monto or 0 for m in self.metodos_pago_nota])

		if total_pagado < self.total_final:
			frappe.throw(_("El total pagado ({0}) es menor que el total final ({1})").format(
				frappe.format_value(total_pagado, {'fieldtype': 'Currency'}),
				frappe.format_value(self.total_final, {'fieldtype': 'Currency'})
			))

	def validate_stock_availability(self):
		"""Validar que hay stock disponible para productos que lo requieren"""
		for item in self.tabla_de_productos:
			producto = frappe.get_doc("Producto", item.producto)
			if producto.mantener_stock:
				# Obtener stock actual del almacén
				if not self.almacen:
					frappe.throw(_("Debe especificar un almacén para productos con control de stock"))

				stock_actual = frappe.db.get_value(
					"Producto",
					item.producto,
					"cantidad_disponible"
				) or 0

				if stock_actual < item.cantidad:
					frappe.throw(_("Stock insuficiente para {0}. Disponible: {1}, Requerido: {2}").format(
						item.producto,
						stock_actual,
						item.cantidad
					))

	def on_cancel(self):
		"""Remover de la sesión POS cuando se cancela la nota"""
		if self.sesion_pos:
			self.remover_de_sesion_pos()

			# Emitir evento realtime para actualizar otros dispositivos
			frappe.publish_realtime(
				event='venta_cancelada',
				message={
					'sesion_pos': self.sesion_pos,
					'nota_venta': self.name
				},
				doctype='Sesion POS',
				docname=self.sesion_pos
			)
	
	def validar_metodos_de_pago_duplicados(self):
		"""Valida que no haya métodos de pago duplicados"""
		metodos = []
		for row in self.metodos_pago_nota:
			if row.metodo in metodos:
				frappe.throw(_("El método de pago {0} ya ha sido agregado").format(row.metodo))
			metodos.append(row.metodo)
	
	def get_dashboard_data(self):
		"""Datos para el dashboard de la nota de venta"""
		return {
			'fieldname': 'nota_de_venta',
			'transactions': [
				{
					'label': _('Relacionado'),
					'items': ['Sesion POS']
				}
			]
		}
	
	@frappe.whitelist()
	def marcar_como_impreso(self):
		"""Marca la nota de venta como impresa"""
		self.estado_impresion = "Impreso"
		self.save()
		frappe.msgprint(_("Nota de venta marcada como impresa"))
	
	def get_items_summary(self):
		"""Resumen de items para reportes"""
		items_summary = []
		for item in self.tabla_de_productos:
			items_summary.append({
				'producto': item.producto,
				'cantidad': item.cantidad,
				'precio_unitario': item.precio_unitario,
				'total': item.total_linea
			})
		return items_summary

	def remover_de_sesion_pos(self):
		"""Remover esta nota de venta de la sesión POS"""
		try:
			sesion = frappe.get_doc("Sesion POS", self.sesion_pos)

			# Filtrar las ventas para remover esta nota
			ventas_validas = []
			for venta in sesion.ventas:
				if venta.nota_de_venta != self.name:
					ventas_validas.append(venta)

			# Limpiar y reagregar solo las ventas válidas
			sesion.ventas = []
			for venta in ventas_validas:
				sesion.append('ventas', {
					'nota_de_venta': venta.nota_de_venta,
					'total': venta.total,
					'metodo_pago': venta.metodo_pago
				})

			# Guardar sin disparar validaciones
			sesion.flags.ignore_validate = True
			sesion.save(ignore_permissions=True)

			frappe.msgprint(_("La nota de venta ha sido removida de la sesión POS"))
		except Exception as e:
			frappe.log_error(f"Error removiendo nota de venta de sesión: {str(e)}", "Cancelación Nota de Venta")
