"""
Patch para recalcular los precios de todos los productos
corrigiendo el cálculo de impuestos retenidos y trasladados
"""

import frappe


def execute():
	"""Recalcular todos los precios de productos existentes"""
	frappe.reload_doc("ventas", "doctype", "impuestos")
	frappe.reload_doc("ventas", "doctype", "producto")
	frappe.reload_doc("ventas", "doctype", "precios_productos")
	
	productos = frappe.get_all("Producto", fields=["name"])
	
	for producto_data in productos:
		try:
			producto = frappe.get_doc("Producto", producto_data.name)
			producto.calcular_precios()
			producto.save()
			frappe.db.commit()
			print(f"✓ Recalculado: {producto.name}")
		except Exception as e:
			print(f"✗ Error en {producto_data.name}: {str(e)}")
			frappe.db.rollback()
	
	print(f"\n✓ Patch completado: {len(productos)} productos procesados")
