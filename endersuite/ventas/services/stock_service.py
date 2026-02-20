"""
Servicios de gestión de inventario y stock para POS
"""

import frappe
from frappe import _
import json


@frappe.whitelist()
def get_stock(producto, almacen):
	"""
	Obtiene el stock disponible de un producto en un almacén específico.

	Args:
		producto (str): Nombre del producto
		almacen (str): Nombre del almacén

	Returns:
		float: Cantidad disponible
	"""
	producto_doc = frappe.get_doc("Producto", producto)

	if not producto_doc.mantener_stock:
		return 999999  # Stock infinito para productos sin control

	# TODO: Implementar agregación por almacén cuando tengamos movimientos
	return producto_doc.cantidad_disponible or 0


@frappe.whitelist()
def get_stock_detallado(producto, almacen):
	"""
	Obtiene información detallada de stock incluyendo lotes y series disponibles.

	Args:
		producto (str): Nombre del producto
		almacen (str): Nombre del almacén

	Returns:
		dict: Información detallada de stock
	"""
	producto_doc = frappe.get_doc("Producto", producto)

	resultado = {
		"producto": producto,
		"almacen": almacen,
		"cantidad_disponible": producto_doc.cantidad_disponible or 0,
		"requiere_lote": producto_doc.requiere_lote or 0,
		"requiere_serie": producto_doc.requiere_serie or 0,
		"lotes": [],
		"series": []
	}

	# Obtener lotes disponibles
	if producto_doc.requiere_lote:
		lotes = frappe.get_all(
			"Lote",
			filters={
				"producto": producto,
				"almacen": almacen,
				"cantidad_disponible": [">", 0]
			},
			fields=["name", "cantidad_disponible", "fecha_vencimiento"]
		)
		resultado["lotes"] = lotes

	# Obtener series disponibles
	if producto_doc.requiere_serie:
		series = frappe.get_all(
			"Serie",
			filters={
				"producto": producto,
				"almacen": almacen,
				"estado": "Disponible"
			},
			fields=["name", "numero_serie"]
		)
		resultado["series"] = series

	return resultado


@frappe.whitelist()
def check_availability(items, almacen):
	"""
	Valida la disponibilidad de stock para una lista de items.

	Args:
		items (list): Lista de diccionarios con producto, cantidad, lotes, series
		almacen (str): Nombre del almacén

	Returns:
		dict: {"valido": bool, "errores": list}
	"""
	if isinstance(items, str):
		items = json.loads(items)

	errores = []

	for item in items:
		producto = item.get("producto")
		cantidad = float(item.get("cantidad", 0))

		producto_doc = frappe.get_doc("Producto", producto)

		# Validar stock si mantiene control
		if producto_doc.mantener_stock:
			stock_disponible = producto_doc.cantidad_disponible or 0

			if cantidad > stock_disponible:
				errores.append(
					_("Stock insuficiente para {0}. Disponible: {1}, Requerido: {2}").format(
						producto, stock_disponible, cantidad
					)
				)

		# Validar lotes si es requerido
		if producto_doc.requiere_lote:
			detalle_lotes = item.get("detalle_lote_serie", [])
			total_lotes = sum(float(d.get("cantidad", 0)) for d in detalle_lotes if d.get("lote"))

			if total_lotes < cantidad:
				errores.append(
					_("Debe especificar lotes para {0}").format(producto)
				)

		# Validar series si es requerido
		if producto_doc.requiere_serie:
			detalle_series = item.get("detalle_lote_serie", [])
			series_count = len([d for d in detalle_series if d.get("serie")])

			if series_count < cantidad:
				errores.append(
					_("Debe especificar {0} series para {1}").format(int(cantidad), producto)
				)

	return {
		"valido": len(errores) == 0,
		"errores": errores
	}


def decrement_stock(nota_venta_doc, method=None):
	"""
	Decrementa el stock al enviar una nota de venta.
	Crea un Movimiento de Stock tipo "Salida" para registrar la transacción.
	Llamado desde hook on_submit de Nota de Venta.

	Args:
		nota_venta_doc: Documento de Nota de Venta
		method: Nombre del método del hook (pasado automáticamente por Frappe)
	"""
	# Obtener el almacén - priorizar el del documento, luego del perfil
	almacen = nota_venta_doc.almacen

	if not almacen and nota_venta_doc.perfil_pos:
		# Obtener almacén del perfil POS
		almacen = frappe.get_value("Perfil de POS", nota_venta_doc.perfil_pos, "almacen")
	
	if not almacen:
		# Fallback: buscar primer almacén disponible
		almacen = frappe.db.get_value("Almacen", {"docstatus": 0}, "name")
		
		if not almacen:
			frappe.throw(_("No se encontró ningún almacén disponible. Por favor cree un almacén."))

	if not almacen:
		frappe.throw(_("No se pudo determinar el almacén para el movimiento de stock"))	# Crear documento de Movimiento de Stock
	movimiento = frappe.get_doc({
		"doctype": "Movimiento de Stock",
		"tipo_movimiento": "Salida",
		"almacen": almacen,
		"referencia": f"Nota de Venta: {nota_venta_doc.name}",
		"motivo": f"Venta a cliente {nota_venta_doc.cliente or 'General'}",
		"usuario": nota_venta_doc.owner,
		"detalles": []
	})

	for item in nota_venta_doc.tabla_de_productos:
		producto_doc = frappe.get_doc("Producto", item.producto)

		if not producto_doc.mantener_stock:
			continue

		cantidad = float(item.cantidad)

		# Agregar detalle al movimiento
		detalle = {
			"producto": item.producto,
			"cantidad": cantidad,
			"tipo_operacion": "Salida"
		}

		# Agregar lotes/series si aplica
		if producto_doc.requiere_lote and item.detalle_lote_serie:
			detalle["detalle_lote_serie"] = []
			for det in item.detalle_lote_serie:
				if det.lote:
					detalle["detalle_lote_serie"].append({
						"lote": det.lote,
						"cantidad": det.cantidad
					})

		if producto_doc.requiere_serie and item.detalle_lote_serie:
			if not detalle.get("detalle_lote_serie"):
				detalle["detalle_lote_serie"] = []
			for det in item.detalle_lote_serie:
				if det.serie:
					detalle["detalle_lote_serie"].append({
						"serie": det.serie,
						"cantidad": 1
					})

		movimiento.append("detalles", detalle)

	# Guardar y enviar el movimiento (esto actualizará el stock automáticamente)
	if movimiento.detalles:
		movimiento.insert(ignore_permissions=True)
		movimiento.submit()


def revert_stock(nota_venta_doc, method=None):
	"""
	Revierte el stock al cancelar una nota de venta.
	Busca el Movimiento de Stock relacionado y lo cancela.
	Llamado desde hook on_cancel de Nota de Venta.

	Args:
		nota_venta_doc: Documento de Nota de Venta
		method: Nombre del método del hook (pasado automáticamente por Frappe)
	"""
	# Buscar el movimiento de stock relacionado con esta nota de venta
	movimientos = frappe.get_all(
		"Movimiento de Stock",
		filters={
			"referencia": f"Nota de Venta: {nota_venta_doc.name}",
			"docstatus": 1
		},
		pluck="name"
	)

	# Cancelar el movimiento (esto revertirá el stock automáticamente)
	for mov_name in movimientos:
		mov_doc = frappe.get_doc("Movimiento de Stock", mov_name)
		mov_doc.cancel()
