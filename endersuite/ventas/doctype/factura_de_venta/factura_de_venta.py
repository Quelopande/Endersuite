# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, nowdate


class FacturadeVenta(Document):
	def autoname(self):
		"""Genera el folio automáticamente si no está asignado"""
		if not self.folio:
			# Obtiene el último número de folio
			last_folio = frappe.db.sql("""
				SELECT MAX(CAST(SUBSTRING(name, 4) AS UNSIGNED)) as max_folio
				FROM `tabFactura de Venta`
				WHERE name LIKE 'FV-%'
			""", as_dict=True)
			
			next_number = 1
			if last_folio and last_folio[0].max_folio:
				next_number = int(last_folio[0].max_folio) + 1
			
			self.folio = f"FV-{str(next_number).zfill(5)}"
		
		# Establece el nombre del documento
		self.name = self.folio
	
	def validate(self):
		"""Validaciones antes de guardar"""
		self.validar_fecha_emision()
		self.validar_productos()
		self.calcular_totales()
	
	def validar_fecha_emision(self):
		"""Valida que la fecha de emisión no sea futura"""
		if self.fecha_de_emision and getdate(self.fecha_de_emision) > getdate(nowdate()):
			frappe.throw(_("La fecha de emisión no puede ser futura"))
	
	def validar_productos(self):
		"""Valida que existan productos en la tabla"""
		if not self.tabla_con_los_productos_o_servicios:
			frappe.throw(_("Debe agregar al menos un producto o servicio"))
		
		# Valida que cada producto tenga cantidad y precio
		for item in self.tabla_con_los_productos_o_servicios:
			if not item.cantidad or item.cantidad <= 0:
				frappe.throw(_("La cantidad del producto {0} debe ser mayor a cero").format(item.producto__servicio))
			
			if not item.valor or item.valor <= 0:
				frappe.throw(_("El precio del producto {0} debe ser mayor a cero").format(item.producto__servicio))
	
	def calcular_totales(self):
		"""Calcula subtotal, descuentos, impuestos y total"""
		subtotal = 0
		impuestos_trasladados = 0
		descuento_total = 0
		
		# Primero calcula subtotal e impuestos (antes de descuentos)
		for item in self.tabla_con_los_productos_o_servicios:
			cantidad = item.cantidad or 0
			valor = item.valor or 0
			
			# Subtotal del producto (precio base sin impuestos)
			importe_producto = cantidad * valor
			subtotal += importe_producto
			
			# Calcula impuestos del producto
			if item.producto__servicio:
				producto = frappe.get_doc("Producto", item.producto__servicio)
				
				if producto.tipo_de_impuesto:
					impuesto = frappe.get_doc("Impuestos", producto.tipo_de_impuesto)
					
					if impuesto.porciento_impuesto:
						tasa = impuesto.porciento_impuesto / 100
						impuesto_producto = importe_producto * tasa
						impuestos_trasladados += impuesto_producto
		
		# Subtotal con impuestos incluidos
		subtotal_con_impuestos = subtotal + impuestos_trasladados
		
		# Ahora calcula descuentos sobre el subtotal con impuestos
		for item in self.tabla_con_los_productos_o_servicios:
			cantidad = item.cantidad or 0
			valor = item.valor or 0
			descuento_pct = item.descuento or 0
			
			if descuento_pct > 0 and item.producto__servicio:
				# Obtiene el precio con impuestos del producto
				producto = frappe.get_doc("Producto", item.producto__servicio)
				precio_con_impuestos = valor  # precio base
				
				if producto.tipo_de_impuesto:
					impuesto = frappe.get_doc("Impuestos", producto.tipo_de_impuesto)
					if impuesto.porciento_impuesto:
						tasa = impuesto.porciento_impuesto / 100
						precio_con_impuestos = valor * (1 + tasa)
				
				# Calcula descuento sobre precio con impuestos
				importe_con_impuestos = cantidad * precio_con_impuestos
				descuento_producto = importe_con_impuestos * (descuento_pct / 100)
				descuento_total += descuento_producto
		
		# Establece los valores
		self.subtotal = subtotal
		self.total_de_impuestos_trasladados = impuestos_trasladados
		self.descuento_total = descuento_total
		self.total_de_impuestos_retenidos = 0
		
		# Total final: subtotal + impuestos - descuentos
		self.total = subtotal + impuestos_trasladados - descuento_total
	
	def before_submit(self):
		"""Validaciones antes de enviar"""
		if not self.fecha_de_emision:
			frappe.throw(_("La fecha de emisión es obligatoria"))
		
		if not self.cliente:
			frappe.throw(_("El cliente es obligatorio"))
		
		if not self.compañia:
			frappe.throw(_("La compañía es obligatoria"))
	
	def on_submit(self):
		"""Acciones al enviar el documento"""
		# Actualizar estado de notas relacionadas
		self.actualizar_estado_notas("Facturado")
		
		# El timbrado se maneja desde el cliente (JavaScript) con confirmación
		pass
	
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
def importar_notas(factura_name, notas_list):
	"""
	Importa los items de las notas seleccionadas a la factura
	"""
	import json
	if isinstance(notas_list, str):
		notas_list = json.loads(notas_list)
		
	if not notas_list:
		return []
		
	factura = frappe.get_doc("Factura de Venta", factura_name)
	items_agregados = []
	
	# Limpiar items actuales si se desea (opcional, aquí asumimos que se agregan)
	# factura.tabla_con_los_productos_o_servicios = []
	
	for nota_name in notas_list:
		nota = frappe.get_doc("Nota de Venta", nota_name)
		
		if nota.estado_facturacion == "Facturado":
			frappe.throw(_("La nota {0} ya está facturada").format(nota_name))
			
		# Agregar referencia a la tabla de notas
		factura.append("notas_relacionadas", {
			"nota_de_venta": nota.name,
			"fecha": nota.fecha_y_hora_de_venta,
			"total": nota.total_final
		})
		
		# Copiar items
		for item in nota.tabla_de_productos:
			factura.append("tabla_con_los_productos_o_servicios", {
				"producto__servicio": item.producto,
				"cantidad": item.cantidad,
				"valor": item.precio_unitario,
				"descuento": item.descuento_porcentaje,
				"descripcion": f"Nota: {nota.name} - {item.producto}"
			})
			
	factura.save()
	return factura.tabla_con_los_productos_o_servicios


@frappe.whitelist()
def timbrar_en_sat(factura_name):
	"""
	Timbra una factura en el SAT a través del PAC
	Método público llamado desde el frontend
	"""
	from endersuite.ventas.services.pac_service import ServicioPAC
	
	try:
		# Obtiene el documento
		factura = frappe.get_doc("Factura de Venta", factura_name)
		
		# Valida que esté en estado correcto
		if factura.docstatus != 1:
			frappe.throw(_("La factura debe estar enviada (submitted) para timbrarla"))
		
		# Valida que no esté timbrada
		if factura.uuid:
			frappe.throw(_("Esta factura ya ha sido timbrada con UUID: {0}").format(factura.uuid))
		
		# Crea el servicio PAC y timbra
		servicio = ServicioPAC()
		resultado = servicio.timbrar_factura(factura)
		
		if resultado.get("success"):
			# Actualizar campos permitidos después de submit (allow_on_submit=1)
			factura.uuid = resultado.get("uuid")
			
			# Guardar XML y PDF en formato JSON para facilitar extracción
			import json
			datos_timbrado = {
				"XML": resultado.get("xml"),
				"PDF": resultado.get("pdf"),
				"UUID": resultado.get("uuid"),
				"fecha_timbrado": str(resultado.get("fecha_timbrado"))
			}
			factura.xml_timbrado = json.dumps(datos_timbrado)
			factura.fecha_de_timbrado = resultado.get("fecha_timbrado")
			
			# Flags para permitir actualización de documento submitted
			factura.flags.ignore_validate_update_after_submit = True
			factura.save()
			frappe.db.commit()
			
			return {
				"success": True,
				"message": _("Factura timbrada exitosamente"),
				"uuid": resultado.get("uuid")
			}
		else:
			return {
				"success": False,
				"error": resultado.get("error")
			}
	
	except Exception as e:
		frappe.log_error(f"Error al timbrar factura {factura_name}: {str(e)}")
		error_msg = str(e)
		error_type = "unknown"
		
		# Clasifica el tipo de error
		if "credencial" in error_msg.lower() or "certificado" in error_msg.lower() or "password" in error_msg.lower():
			error_type = "credentials"
		elif "pac" in error_msg.lower() or "api" in error_msg.lower() or "conexión" in error_msg.lower():
			error_type = "pac"
		elif "validación" in error_msg.lower() or "campo requerido" in error_msg.lower():
			error_type = "validation"
		
		return {
			"success": False,
			"error": error_msg,
			"error_type": error_type
		}


@frappe.whitelist()
def check_pac_credentials():
	"""Verifica si existe la configuración PAC y si tiene certificados cargados.

	Returns:
		 dict: { configurado: bool, tiene_certificados: bool, faltantes: [str] }
	"""
	info = {
		"configurado": False,
		"tiene_certificados": False,
		"faltantes": []
	}
	try:
		if not frappe.db.exists("Configuracion PAC", "Configuracion PAC"):
			info["faltantes"].append("configuracion")
			return info
		config = frappe.get_doc("Configuracion PAC", "Configuracion PAC")
		info["configurado"] = True
		csd_key = (config.csd_key_pem or "").strip()
		csd_cer = (config.csd_cer_pem or "").strip()
		if csd_key and csd_cer:
			info["tiene_certificados"] = True
		else:
			if not csd_key:
				info["faltantes"].append("csd_key_pem")
			if not csd_cer:
				info["faltantes"].append("csd_cer_pem")
		return info
	except Exception as e:
		frappe.log_error(f"Error verificando credenciales PAC: {str(e)}")
		return info


def _leer_contenido_archivo(file_url_or_name):
	"""Lee el contenido de un archivo de Frappe dado su URL o nombre."""
	if not file_url_or_name:
		return None
	try:
		# Normalizar nombre (puede venir como /files/xyz.pem)
		file_doc = None
		if file_url_or_name.startswith("/files/"):
			file_doc = frappe.get_doc("File", {"file_url": file_url_or_name})
		else:
			# Intentar por name
			if frappe.db.exists("File", file_url_or_name):
				file_doc = frappe.get_doc("File", file_url_or_name)
			else:
				file_doc = frappe.get_doc("File", {"file_name": file_url_or_name})
		if not file_doc:
			return None
		return file_doc.get_content()
	except Exception:
		return None


@frappe.whitelist()
def timbrar_con_credenciales(
	factura_name,
	archivo_cer=None,
	archivo_key=None,
	password_key=None,
	guardar_credenciales=None
):
	"""Timbrar usando credenciales configuradas o nuevas proporcionadas.

	Args:
		factura_name (str): Nombre de la factura
		archivo_cer (str): URL del archivo .cer subido (opcional)
		archivo_key (str): URL del archivo .key subido (opcional)
		password_key (str): Contraseña de la llave privada (opcional)
		guardar_credenciales (int): 1 para guardar, 0 para no guardar

	Returns:
		dict con success/error/uuid
	"""
	from endersuite.ventas.services.pac_service import ServicioPAC
	import frappe
	
	# Log de debugging para ver qué parámetros recibimos
	frappe.log_error(
		title="DEBUG: Parámetros recibidos en timbrar_con_credenciales",
		message=f"""
		factura_name: {factura_name}
		archivo_cer: {archivo_cer}
		archivo_key: {archivo_key}
		password_key presente: {bool(password_key)}
		guardar_credenciales: {guardar_credenciales}
		"""
	)

	try:
		factura = frappe.get_doc("Factura de Venta", factura_name)
		if factura.docstatus != 1:
			return {"success": False, "error": _("La factura debe estar enviada para timbrarla"), "error_type": "validation"}
		if factura.uuid:
			return {"success": False, "error": _("Esta factura ya tiene UUID: {0}").format(factura.uuid), "error_type": "validation"}

		# Obtener configuración PAC
		config = None
		if frappe.db.exists("Configuracion PAC", "Configuracion PAC"):
			config = frappe.get_doc("Configuracion PAC", "Configuracion PAC")

		# Determinar si usar credenciales configuradas o proporcionadas
		usar_credenciales_config = not (archivo_cer and archivo_key)
		
		frappe.log_error(
			title="DEBUG: Decisión de credenciales",
			message=f"""
			usar_credenciales_config: {usar_credenciales_config}
			config existe: {bool(config)}
			config.csd_key_pem presente: {bool(config and config.csd_key_pem)}
			config.csd_cer_pem presente: {bool(config and config.csd_cer_pem)}
			"""
		)

		if usar_credenciales_config:
			# Usar credenciales de la configuración
			if not config:
				return {"success": False, "error": _("No existe Configuración PAC"), "error_type": "credentials"}
			if not config.csd_key_pem or not config.csd_cer_pem:
				return {
					"success": False, 
					"error": _("Las credenciales CSD no están completas en la configuración."), 
					"error_type": "credentials"
				}
			
			frappe.log_error(
				title="DEBUG: Usando credenciales de configuración",
				message=f"Longitud csd_key_pem: {len(config.csd_key_pem or '')}, Longitud csd_cer_pem: {len(config.csd_cer_pem or '')}"
			)
			servicio = ServicioPAC()
		else:
			# Usar credenciales proporcionadas (archivos subidos)
			key_contenido = _leer_contenido_archivo(archivo_key)
			cer_contenido = _leer_contenido_archivo(archivo_cer)
			
			frappe.log_error(
				title="DEBUG: Leyendo archivos proporcionados",
				message=f"""
				archivo_key: {archivo_key}
				archivo_cer: {archivo_cer}
				key_contenido longitud: {len(key_contenido) if key_contenido else 0}
				cer_contenido longitud: {len(cer_contenido) if cer_contenido else 0}
				"""
			)
			
			if not key_contenido or not cer_contenido:
				return {
					"success": False, 
					"error": _("No se pudieron leer los archivos de certificados. Key leído: {0}, Cer leído: {1}").format(
						bool(key_contenido), bool(cer_contenido)
					), 
					"error_type": "credentials"
				}
			
			# Crear servicio y usar credenciales temporales
			if not config:
				return {"success": False, "error": _("No existe Configuración PAC base"), "error_type": "credentials"}
				
			servicio = ServicioPAC()
			servicio.config.csd_key_pem = key_contenido
			servicio.config.csd_cer_pem = cer_contenido
			
			# Guardar si se solicita
			if guardar_credenciales == 1 or guardar_credenciales == "1":
				config.csd_key_pem = key_contenido
				config.csd_cer_pem = cer_contenido
				config.save(ignore_permissions=True)
				frappe.db.commit()
				frappe.log_error(
					title="DEBUG: Credenciales guardadas",
					message="Las nuevas credenciales se han guardado en Configuración PAC"
				)

		# Intentar timbrar
		frappe.log_error(
			title="DEBUG: Iniciando timbrado",
			message=f"Timbrando factura {factura_name}"
		)
		
		resultado = servicio.timbrar_factura(factura)
		
		frappe.log_error(
			title="DEBUG: Resultado de timbrado",
			message=f"Success: {resultado.get('success')}, Error: {resultado.get('error')}"
		)
		
		if resultado.get("success"):
			# Actualizar campos permitidos después de submit (allow_on_submit=1)
			factura.uuid = resultado.get("uuid")
			
			# Guardar XML y PDF en formato JSON para facilitar extracción
			import json
			datos_timbrado = {
				"XML": resultado.get("xml"),
				"PDF": resultado.get("pdf"),
				"UUID": resultado.get("uuid"),
				"fecha_timbrado": str(resultado.get("fecha_timbrado"))
			}
			factura.xml_timbrado = json.dumps(datos_timbrado)
			factura.fecha_de_timbrado = resultado.get("fecha_timbrado")
			
			# Flags para permitir actualización de documento submitted
			factura.flags.ignore_validate_update_after_submit = True
			factura.save()
			frappe.db.commit()
			
			frappe.log_error(
				title="DEBUG: Factura actualizada correctamente",
				message=f"UUID: {resultado.get('uuid')}"
			)
			
			return {"success": True, "uuid": resultado.get("uuid"), "message": _("Factura timbrada exitosamente")}
		else:
			error_msg = resultado.get("error", "Error desconocido")
			error_type = "unknown"
			
			if "credencial" in error_msg.lower() or "certificado" in error_msg.lower():
				error_type = "credentials"
			elif "pac" in error_msg.lower() or "api" in error_msg.lower():
				error_type = "pac"
				
			return {"success": False, "error": error_msg, "error_type": error_type}

	except Exception as e:
		frappe.log_error(
			title="ERROR: Exception en timbrar_con_credenciales",
			message=f"Exception: {str(e)}\nType: {type(e)}"
		)
		error_msg = str(e)
		error_type = "unknown"
		
		# Clasifica el tipo de error
		if "credencial" in error_msg.lower() or "certificado" in error_msg.lower() or "password" in error_msg.lower():
			error_type = "credentials"
		elif "pac" in error_msg.lower() or "api" in error_msg.lower() or "conexión" in error_msg.lower():
			error_type = "pac"
		elif "validación" in error_msg.lower() or "campo requerido" in error_msg.lower():
			error_type = "validation"
		
		return {"success": False, "error": error_msg, "error_type": error_type}

@frappe.whitelist()
def descargar_xml(factura_name):
	"""
	Descarga el XML timbrado de la factura
	"""
	import json
	
	try:
		factura = frappe.get_doc("Factura de Venta", factura_name)
		
		if not factura.xml_timbrado:
			frappe.throw(_("Esta factura no tiene XML timbrado"))
		
		xml_content = factura.xml_timbrado
		
		# Si está guardado como JSON, extraer el XML
		try:
			xml_data = json.loads(xml_content)
			if isinstance(xml_data, dict):
				# Buscar XML en diferentes ubicaciones posibles
				xml_content = xml_data.get("XML") or xml_data.get("xml") or xml_content
		except json.JSONDecodeError:
			# Ya es un string XML directo
			pass
		
		# Limpiar nombre del archivo
		uuid_clean = (factura.uuid or 'timbrado').replace('-', '')
		filename = f"{factura.name}_{uuid_clean}.xml"
		
		return {
			"xml": xml_content,
			"filename": filename
		}
		
	except Exception as e:
		frappe.log_error(f"Error al descargar XML: {str(e)}", "Descarga XML")
		frappe.throw(_("Error al descargar XML: {0}").format(str(e)))

@frappe.whitelist()
def descargar_pdf(factura_name):
	"""
	Descarga el PDF timbrado de la factura
	"""
	import json
	
	try:
		factura = frappe.get_doc("Factura de Venta", factura_name)
		
		if not factura.xml_timbrado:
			frappe.throw(_("Esta factura no tiene datos de timbrado"))
		
		xml_data = factura.xml_timbrado
		pdf_base64 = None
		
		# Intentar extraer PDF del JSON
		try:
			response_data = json.loads(xml_data)
			if isinstance(response_data, dict):
				# Buscar PDF en el formato nuevo
				pdf_base64 = response_data.get("PDF") or response_data.get("pdf")
		except json.JSONDecodeError:
			pass
		
		if not pdf_base64:
			frappe.throw(_("No se encontró el PDF. El PDF se genera automáticamente durante el timbrado."))
		
		# Limpiar nombre del archivo
		uuid_clean = (factura.uuid or 'timbrado').replace('-', '')
		filename = f"{factura.name}_{uuid_clean}.pdf"
		
		return {
			"pdf_base64": pdf_base64,
			"filename": filename
		}
		
	except Exception as e:
		frappe.log_error(f"Error al descargar PDF: {str(e)}", "Descarga PDF")
		frappe.throw(_("Error al descargar PDF: {0}").format(str(e)))
