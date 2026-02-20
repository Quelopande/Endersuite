# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate


def _bool(value):
	return bool(value) and str(value).lower() not in ("0", "false", "none", "")

class FacturadeVenta(Document):
	def on_submit(self):
		"""Acciones al enviar el documento"""
		# Actualizar estado de notas relacionadas
		self.actualizar_estado_notas("Facturado")
	
	def on_cancel(self):
		"""Acciones al cancelar el documento"""
		# Liberar notas relacionadas
		self.actualizar_estado_notas("Pendiente")
		
		if self.uuid:
			frappe.msgprint(_("Recuerde cancelar la factura también en el SAT"))
		frappe.msgprint(_("Factura de Venta {0} cancelada").format(self.name))

	def actualizar_estado_notas(self, estado):
		"""Actualiza el estado de las notas de venta relacionadas"""
		if not self.notas_relacionadas:
			return
			
		factura_link = self.name if estado == "Facturado" else None
		
		for item in self.notas_relacionadas:
			if item.nota_de_venta:
				frappe.db.set_value("Nota de Venta", item.nota_de_venta, {
					"estado_facturacion": estado,
					"factura_de_venta": factura_link
				})

@frappe.whitelist()
def get_notas_pendientes(cliente=None, fecha_inicio=None, fecha_fin=None):
	"""Obtiene notas de venta pendientes de facturar"""
	filters = {
		"estado_facturacion": "Pendiente",
		"docstatus": 1  # Solo notas enviadas
	}
	
	if cliente:
		filters["cliente"] = cliente
		
	if fecha_inicio and fecha_fin:
		filters["fecha_y_hora_de_venta"] = ["between", [fecha_inicio, fecha_fin]]
	elif fecha_inicio:
		filters["fecha_y_hora_de_venta"] = [">=", fecha_inicio]
		
	notas = frappe.get_all(
		"Nota de Venta",
		filters=filters,
		fields=["name", "fecha_y_hora_de_venta", "total_final", "cliente", "perfil_pos"],
		order_by="fecha_y_hora_de_venta desc"
	)
	
	return notas

@frappe.whitelist()
def get_notas_details(notas_list):
	"""
	Retorna los detalles de las notas seleccionadas para poblar la factura (sin guardar)
	"""
	import json
	if isinstance(notas_list, str):
		notas_list = json.loads(notas_list)
		
	if not notas_list:
		return {}
		
	data = {
		"notas_relacionadas": [],
		"items": [],
		"totales": {
			"subtotal": 0.0,
			"descuento_total": 0.0,
			"total_impuestos_trasladados": 0.0,
			"total_impuestos_retenidos": 0.0,
			"total": 0.0
		}
	}
	
	for nota_name in notas_list:
		nota = frappe.get_doc("Nota de Venta", nota_name)
		
		if nota.estado_facturacion == "Facturado":
			continue
			
		# Acumular totales
		data["totales"]["subtotal"] += nota.subtotal or 0.0
		data["totales"]["descuento_total"] += nota.descuento_global_monto or 0.0
		
		# Calcular impuestos desde líneas si el total de cabecera es 0 (fallback) o para desglose preciso
		# Nota: Siempre iteramos para desglosar retenidos vs trasladados correctamente,
		# ya que la Nota de Venta solo tiene 'total_impuestos' global.
		
		impuestos_trasladados_nota = 0.0
		impuestos_retenidos_nota = 0.0
		
		if nota.tabla_de_productos:
			for item in nota.tabla_de_productos:
				monto_impuesto = item.impuesto_monto or 0.0
				
				# Si el monto es 0 pero tiene impuesto, intentamos recalcular (para notas antiguas)
				if monto_impuesto == 0 and item.impuesto:
					impuesto_data = frappe.db.get_value("Impuestos", item.impuesto, ["porciento_impuesto", "incluido_en_el_precio"], as_dict=True)
					if impuesto_data:
						tasa = float(impuesto_data.porciento_impuesto or 0)
						incluido = impuesto_data.incluido_en_el_precio
						
						# Reconstruimos base desde el total de línea o precio unitario
						# item.base_imponible en nota podría estar mal si no se calculó bien antes.
						# Usamos item.total_linea o (cantidad * precio) como referencia de "lo cobrado"
						total_linea = item.total_linea or (item.cantidad * item.precio_unitario)
						
						if incluido:
							# Total = Base + Impuesto = Base * (1 + tasa/100)
							base = total_linea / (1 + (tasa / 100))
							monto_impuesto = total_linea - base
						else:
							# Asumimos que si era 0, tal vez el precio era base. 
							# Pero si la nota se creó con precio con IVA pero lógica vieja, 
							# es arriesgado. Mejor asumimos que el precio cobrado era el total final.
							# Si no incluido, Impuesto = Base * Tasa. 
							# Si total_linea es Base + Impuesto...
							# Vamos a asumir comportamiento estándar: recalcular sobre la base registrada si existe, sino sobre total.
							base = item.base_imponible or total_linea
							monto_impuesto = base * (tasa / 100)

				if monto_impuesto > 0 and item.impuesto:
					# Verificar si es retenido o trasladado
					# Ya tenemos impuesto_data si recalculamos, sino lo buscamos
					if 'impuesto_data' not in locals():
						impuesto_data = frappe.db.get_value("Impuestos", item.impuesto, ["incluido_en_el_precio"], as_dict=True)
					
					es_retenido = impuesto_data.incluido_en_el_precio if impuesto_data else 0
					
					if es_retenido:
						impuestos_retenidos_nota += monto_impuesto
					else:
						impuestos_trasladados_nota += monto_impuesto
		else:
			# Fallback si no hay líneas (raro), asumimos todo trasladado
			impuestos_trasladados_nota = nota.total_impuestos or 0.0

		data["totales"]["total_impuestos_trasladados"] += impuestos_trasladados_nota
		data["totales"]["total_impuestos_retenidos"] += impuestos_retenidos_nota
		data["totales"]["total"] += nota.total_final or 0.0
		
		# Datos para tabla de referencias
		data["notas_relacionadas"].append({
			"nota_de_venta": nota.name,
			"fecha": nota.fecha_y_hora_de_venta,
			"total": nota.total_final
		})
		
		# Datos para tabla de productos
		for item in nota.tabla_de_productos:
			data["items"].append({
				"producto__servicio": item.producto,
				"cantidad": item.cantidad,
				"valor": item.precio_unitario, # Precio unitario original
				"descuento": item.descuento_porcentaje,
				"descripcion": f"Nota: {nota.name} - {item.producto}"
			})
			
	return data


@frappe.whitelist()
def timbrar_en_sat(factura_name: str):
	"""Timbra una Factura de Venta mediante el servicio PAC.

	Guarda `uuid`, `xml_timbrado` y `fecha_de_timbrado` en el documento.
	"""
	if not factura_name:
		frappe.throw(_("Falta el nombre de la factura"))

	factura = frappe.get_doc("Factura de Venta", factura_name)
	if factura.docstatus != 1:
		frappe.throw(_("La factura debe estar enviada (docstatus=1) para timbrarse"))
	if getattr(factura, "uuid", None):
		frappe.throw(_("Esta factura ya está timbrada"))

	# Validar configuración PAC
	config = frappe.get_doc("Configuracion PAC", "Configuracion PAC")
	if not _bool(getattr(config, "activo", 0)):
		frappe.throw(_("El PAC no está activo. Revise Configuracion PAC"))

	from endersuite.ventas.services.pac_service import ServicioPAC

	servicio = ServicioPAC()
	resultado = servicio.timbrar_factura(factura)

	if not resultado or not resultado.get("success"):
		error_msg = (resultado or {}).get("error") or _("Error al timbrar")
		frappe.throw(error_msg)

	uuid = resultado.get("uuid")
	xml = resultado.get("xml")
	fecha = resultado.get("fecha_timbrado")

	# Persistir resultados
	if uuid:
		factura.db_set("uuid", uuid, update_modified=True)
	if xml:
		factura.db_set("xml_timbrado", xml, update_modified=True)

	# `fecha_de_timbrado` es Date, guardamos fecha simple
	if fecha:
		factura.db_set("fecha_de_timbrado", fecha.date(), update_modified=True)
	else:
		factura.db_set("fecha_de_timbrado", nowdate(), update_modified=True)

	return {
		"success": True,
		"uuid": uuid,
		"xml": xml,
		"fecha_de_timbrado": factura.get("fecha_de_timbrado"),
		"message": _("Factura timbrada correctamente")
	}


