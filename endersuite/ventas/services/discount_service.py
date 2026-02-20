"""
Servicios de gestión de descuentos para POS
"""

import frappe
from frappe import _
from frappe.utils import today, getdate


@frappe.whitelist()
def get_active_discounts(lista_de_precios=None):
	"""
	Obtiene descuentos activos y vigentes.
	
	Args:
		lista_de_precios (str, optional): Filtrar por lista de precios
	
	Returns:
		list: Lista de descuentos activos
	"""
	filters = {
		"habilitado": 1,
		"fecha_inicio": ["<=", today()]
	}
	
	# Filtrar por lista de precios si se especifica
	if lista_de_precios:
		filters["lista_de_precios"] = ["in", [lista_de_precios, ""]]
	
	descuentos = frappe.get_all(
		"Descuentos",
		filters=filters,
		fields=[
			"name", "nombre_descuento", "tipo", "valor", 
			"aplicable_a", "producto", "categoria", 
			"minimo_cantidad", "fecha_fin"
		]
	)
	
	# Filtrar por fecha de fin
	descuentos_vigentes = []
	for desc in descuentos:
		if not desc.fecha_fin or getdate(desc.fecha_fin) >= getdate(today()):
			descuentos_vigentes.append(desc)
	
	return descuentos_vigentes


@frappe.whitelist()
def calculate_discount(producto, cantidad, precio_unitario, descuento_id):
	"""
	Calcula el monto de descuento aplicable a un item.
	
	Args:
		producto (str): Nombre del producto
		cantidad (float): Cantidad del producto
		precio_unitario (float): Precio unitario
		descuento_id (str): ID del descuento a aplicar
	
	Returns:
		dict: {"valido": bool, "monto": float, "mensaje": str}
	"""
	cantidad = float(cantidad)
	precio_unitario = float(precio_unitario)
	
	descuento_doc = frappe.get_doc("Descuentos", descuento_id)
	
	# Validar que el descuento esté habilitado y vigente
	if not descuento_doc.habilitado:
		return {"valido": False, "monto": 0, "mensaje": _("Descuento no habilitado")}
	
	if getdate(descuento_doc.fecha_inicio) > getdate(today()):
		return {"valido": False, "monto": 0, "mensaje": _("Descuento aún no vigente")}
	
	if descuento_doc.fecha_fin and getdate(descuento_doc.fecha_fin) < getdate(today()):
		return {"valido": False, "monto": 0, "mensaje": _("Descuento expirado")}
	
	# Validar cantidad mínima
	if cantidad < (descuento_doc.minimo_cantidad or 1):
		return {
			"valido": False, 
			"monto": 0, 
			"mensaje": _("Cantidad mínima requerida: {0}").format(descuento_doc.minimo_cantidad)
		}
	
	# Validar aplicabilidad
	if descuento_doc.aplicable_a == "Producto":
		if descuento_doc.producto != producto:
			return {"valido": False, "monto": 0, "mensaje": _("Descuento no aplicable a este producto")}
	
	elif descuento_doc.aplicable_a == "Categoría":
		producto_doc = frappe.get_doc("Producto", producto)
		if producto_doc.categoria != descuento_doc.categoria:
			return {"valido": False, "monto": 0, "mensaje": _("Descuento no aplicable a esta categoría")}
	
	# Calcular descuento
	subtotal = cantidad * precio_unitario
	
	if descuento_doc.tipo == "Porcentaje":
		monto_descuento = subtotal * (descuento_doc.valor / 100)
	else:  # Monto Fijo
		monto_descuento = descuento_doc.valor
	
	# No puede ser mayor al subtotal
	monto_descuento = min(monto_descuento, subtotal)
	
	return {
		"valido": True,
		"monto": monto_descuento,
		"mensaje": _("Descuento aplicado: {0}").format(descuento_doc.nombre_descuento)
	}


@frappe.whitelist()
def get_best_discount(producto, cantidad, precio_unitario, lista_de_precios=None):
	"""
	Encuentra el mejor descuento aplicable para un producto.
	
	Args:
		producto (str): Nombre del producto
		cantidad (float): Cantidad del producto
		precio_unitario (float): Precio unitario
		lista_de_precios (str, optional): Lista de precios
	
	Returns:
		dict: Descuento con mayor monto o None
	"""
	descuentos = get_active_discounts(lista_de_precios)
	
	mejor_descuento = None
	mejor_monto = 0
	
	for desc in descuentos:
		resultado = calculate_discount(producto, cantidad, precio_unitario, desc["name"])
		
		if resultado["valido"] and resultado["monto"] > mejor_monto:
			mejor_monto = resultado["monto"]
			mejor_descuento = {
				"descuento_id": desc["name"],
				"descuento_nombre": desc["nombre_descuento"],
				"monto": resultado["monto"]
			}
	
	return mejor_descuento
