# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class Reembolso(Document):
	def validate(self):
		"""Validaciones generales del reembolso"""
		self.validar_productos_reembolso()
		self.calcular_total_reembolso()

	def before_submit(self):
		"""Validaciones antes de aprobar el reembolso"""
		self.validar_nota_venta_valida()
		self.validar_cantidades_disponibles()

	def on_submit(self):
		"""Procesar reembolso: revertir stock y registrar devolución"""
		self.estado = "Aprobado"
		self.revertir_stock()
		self.registrar_devolucion_dinero()
		self.actualizar_sesion_pos()

		# Emitir evento realtime para actualizar otros dispositivos
		frappe.publish_realtime(
			event='reembolso_creado',
			message={
				'reembolso': self.name,
				'nota_venta_original': self.nota_de_venta_original,
				'sesion_pos': self.sesion_pos,
				'total_reembolso': self.total_reembolso,
				'cliente': self.cliente
			},
			doctype='Reembolso',
			docname=self.name
		)

		frappe.msgprint(_("Reembolso {0} aprobado exitosamente. Total reembolsado: {1}").format(
			self.name, frappe.format_value(self.total_reembolso, {'fieldtype': 'Currency'})
		))

	def on_cancel(self):
		"""Cancelar reembolso"""
		self.estado = "Cancelado"
		frappe.msgprint(_("Reembolso {0} cancelado").format(self.name))

	def validar_nota_venta_valida(self):
		"""Valida que la nota de venta original exista y esté aprobada"""
		if not self.nota_de_venta_original:
			frappe.throw(_("Debe especificar la Nota de Venta Original"))

		# Verificar que la nota de venta existe y está enviada (docstatus = 1)
		nota = frappe.get_doc("Nota de Venta", self.nota_de_venta_original)
		if nota.docstatus != 1:
			frappe.throw(_("La Nota de Venta {0} debe estar aprobada para poder hacer un reembolso").format(
				self.nota_de_venta_original
			))

	def validar_productos_reembolso(self):
		"""Valida que se hayan agregado productos al reembolso"""
		if not self.productos_reembolso or len(self.productos_reembolso) == 0:
			frappe.throw(_("Debe agregar al menos un producto para reembolsar"))

		# Validar que las cantidades sean positivas
		for idx, row in enumerate(self.productos_reembolso, start=1):
			if row.cantidad_reembolso <= 0:
				frappe.throw(_("La cantidad a reembolsar debe ser mayor a cero en la línea #{0}").format(idx))

	def validar_cantidades_disponibles(self):
		"""Valida que las cantidades a reembolsar no excedan las vendidas"""
		# Obtener los productos de la nota de venta original
		nota_productos = frappe.get_all(
			"Productos Nota de Venta",
			filters={"parent": self.nota_de_venta_original},
			fields=["producto", "cantidad"]
		)

		# Crear un diccionario de productos vendidos
		productos_vendidos = {p.producto: p.cantidad for p in nota_productos}

		# Obtener reembolsos previos para esta nota de venta
		reembolsos_previos = frappe.get_all(
			"Reembolso",
			filters={
				"nota_de_venta_original": self.nota_de_venta_original,
				"docstatus": 1,  # Solo reembolsos aprobados
				"name": ["!=", self.name]  # Excluir el reembolso actual
			},
			fields=["name"]
		)

		# Diccionario para acumular cantidades ya reembolsadas
		cantidades_reembolsadas = {}
		for reembolso_prev in reembolsos_previos:
			productos_reemb = frappe.get_all(
				"Productos Reembolso",
				filters={"parent": reembolso_prev.name},
				fields=["producto", "cantidad_reembolso"]
			)
			for p in productos_reemb:
				cantidades_reembolsadas[p.producto] = cantidades_reembolsadas.get(p.producto, 0) + p.cantidad_reembolso

		# Validar cada producto del reembolso actual
		for idx, row in enumerate(self.productos_reembolso, start=1):
			# Verificar que el producto estaba en la venta original
			if row.producto not in productos_vendidos:
				frappe.throw(_("El producto {0} en la línea #{1} no se encuentra en la Nota de Venta Original").format(
					row.producto, idx
				))

			cantidad_vendida = productos_vendidos[row.producto]
			cantidad_ya_reembolsada = cantidades_reembolsadas.get(row.producto, 0)
			cantidad_disponible_reembolso = cantidad_vendida - cantidad_ya_reembolsada

			# Actualizar cantidad_vendida en la fila (para referencia)
			row.cantidad_vendida = cantidad_vendida

			# Validar que no se exceda la cantidad disponible
			if row.cantidad_reembolso > cantidad_disponible_reembolso:
				frappe.throw(_(
					"La cantidad a reembolsar del producto {0} ({1}) excede la cantidad disponible ({2}). "
					"Cantidad vendida: {3}, Ya reembolsada: {4}"
				).format(
					row.producto,
					row.cantidad_reembolso,
					cantidad_disponible_reembolso,
					cantidad_vendida,
					cantidad_ya_reembolsada
				))

	def calcular_total_reembolso(self):
		"""Calcula el total a reembolsar desde los productos"""
		# Obtener precios de la nota de venta original
		nota_productos = frappe.get_all(
			"Productos Nota de Venta",
			filters={"parent": self.nota_de_venta_original},
			fields=["producto", "precio_unitario"]
		)

		precios = {p.producto: p.precio_unitario for p in nota_productos}

		total = 0
		for row in self.productos_reembolso:
			if row.producto in precios:
				# Actualizar precio unitario y calcular total de línea
				row.precio_unitario = precios[row.producto]
				row.total_reembolso = row.cantidad_reembolso * row.precio_unitario
				total += row.total_reembolso
			else:
				frappe.throw(_("No se pudo encontrar el precio del producto {0} en la nota de venta original").format(
					row.producto
				))

		self.total_reembolso = total

	def revertir_stock(self):
		"""Crea un movimiento de stock de entrada para revertir la venta"""
		if not self.almacen:
			frappe.throw(_("No se pudo determinar el almacén para la reversión de stock"))

		# Crear movimiento de stock tipo "Entrada"
		movimiento = frappe.get_doc({
			"doctype": "Movimiento de Stock",
			"tipo_movimiento": "Entrada",
			"almacen": self.almacen,
			"fecha_movimiento": frappe.utils.now(),
			"referencia_doctype": "Reembolso",
			"referencia_docname": self.name,
			"observaciones": f"Reversión de stock por reembolso {self.name} de la venta {self.nota_de_venta_original}"
		})

		# Agregar productos del reembolso
		for row in self.productos_reembolso:
			movimiento.append("detalles_movimiento", {
				"producto": row.producto,
				"cantidad": row.cantidad_reembolso
			})

		# Guardar y enviar el movimiento
		movimiento.insert(ignore_permissions=True)
		movimiento.submit()

		frappe.logger().info(
			f"Reversión de stock creada: {movimiento.name} | "
			f"Reembolso: {self.name} | "
			f"Almacén: {self.almacen}"
		)

	def registrar_devolucion_dinero(self):
		"""Registra la devolución de dinero en el sistema"""
		# Este método puede extenderse para crear un asiento contable
		# o registro de caja según las necesidades del sistema

		frappe.logger().info(
			f"Devolución de dinero registrada | "
			f"Reembolso: {self.name} | "
			f"Monto: {self.total_reembolso} | "
			f"Método: {self.metodo_devolucion} | "
			f"Referencia: {self.referencia_devolucion or 'N/A'}"
		)

	def actualizar_sesion_pos(self):
		"""Actualiza la sesión POS con el reembolso realizado"""
		if not self.sesion_pos:
			return

		try:
			sesion = frappe.get_doc("Sesion POS", self.sesion_pos)

			# Agregar el reembolso a la sesión (si existe una tabla de reembolsos)
			# Por ahora solo emitimos un evento para que se actualicen los totales

			# Emitir evento realtime para actualizar la sesión
			frappe.publish_realtime(
				event='sesion_actualizada',
				message={
					'sesion_pos': self.sesion_pos,
					'tipo': 'reembolso',
					'reembolso': self.name,
					'total': self.total_reembolso
				},
				doctype='Sesion POS',
				docname=self.sesion_pos
			)

		except Exception as e:
			frappe.log_error(
				f"Error actualizando sesión POS con reembolso: {str(e)}",
				"Actualización Sesión POS - Reembolso"
			)


@frappe.whitelist()
def obtener_productos_nota_venta(nota_venta):
	"""Obtiene los productos de una nota de venta para prellenar el reembolso"""
	if not nota_venta:
		return []

	# Verificar permisos
	frappe.has_permission("Nota de Venta", "read", throw=True)

	# Obtener productos de la nota de venta
	productos = frappe.get_all(
		"Productos Nota de Venta",
		filters={"parent": nota_venta},
		fields=["producto", "cantidad", "precio_unitario"]
	)

	# Obtener reembolsos previos
	reembolsos_previos = frappe.get_all(
		"Reembolso",
		filters={
			"nota_de_venta_original": nota_venta,
			"docstatus": 1
		},
		fields=["name"]
	)

	# Calcular cantidades ya reembolsadas
	cantidades_reembolsadas = {}
	for reembolso in reembolsos_previos:
		productos_reemb = frappe.get_all(
			"Productos Reembolso",
			filters={"parent": reembolso.name},
			fields=["producto", "cantidad_reembolso"]
		)
		for p in productos_reemb:
			cantidades_reembolsadas[p.producto] = cantidades_reembolsadas.get(p.producto, 0) + p.cantidad_reembolso

	# Preparar resultado con cantidades disponibles
	resultado = []
	for p in productos:
		cantidad_ya_reembolsada = cantidades_reembolsadas.get(p.producto, 0)
		cantidad_disponible = p.cantidad - cantidad_ya_reembolsada

		if cantidad_disponible > 0:
			resultado.append({
				"producto": p.producto,
				"cantidad_vendida": p.cantidad,
				"cantidad_reembolso": cantidad_disponible,  # Sugerir reembolso total por defecto
				"precio_unitario": p.precio_unitario,
				"total_reembolso": cantidad_disponible * p.precio_unitario
			})

	return resultado
