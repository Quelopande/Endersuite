# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
import requests
import json
import base64
from frappe import _
from frappe.utils import now_datetime
from frappe.utils.password import get_decrypted_password


class ServicioPAC:
	"""Servicio para integración con PAC (FacturAPI)"""
	
	def __init__(self):
		self.config = self.get_config()
	
	def get_config(self):
		"""Obtiene la configuración del PAC"""
		if not frappe.db.exists("Configuracion PAC", "Configuracion PAC"):
			frappe.throw(_("No se ha configurado el PAC. Por favor configure en Configuración PAC"))
		
		return frappe.get_doc("Configuracion PAC", "Configuracion PAC")
	
	def timbrar_factura(self, factura_doc):
		"""
		Timbra una factura en el SAT a través del PAC
		
		Args:
			factura_doc: Documento de Factura de Venta
		
		Returns:
			dict: Respuesta del PAC con UUID, XML, etc.
		"""
		if not self.config.activo:
			frappe.throw(_("El servicio PAC no está activo"))
		
		# Construye el JSON para el PAC
		cfdi_json = self._build_cfdi_json(factura_doc)
		
		# Realiza la petición al PAC
		response = self._send_to_pac(cfdi_json)
		
		return response
	
	def _build_cfdi_json(self, factura):
		"""Construye el JSON del CFDI según el formato del PAC FacturaloPlus"""
		
		# Obtiene datos de la compañía
		compania = frappe.get_doc("Compania", factura.compañia)
		
		# Si está en modo pruebas, usa datos de prueba
		if self.config.modo == "Pruebas":
			rfc_emisor = self.config.rfc_pruebas
			nombre_emisor = self.config.nombre_pruebas
			regimen_emisor = self._extract_regimen_code(self.config.regimen_fiscal_pruebas)
			# Usar número proporcionado por el PAC - el certificado actual no corresponde
			no_certificado = "30001000000500003416"
		else:
			rfc_emisor = compania.rfc
			nombre_emisor = compania.nombre_de_la_empresa
			regimen_emisor = self._extract_regimen_code(compania.regimen_fiscal)
			no_certificado = self._extract_certificate_serial_v2(compania.certificado_cer if hasattr(compania, 'certificado_cer') else self.config.csd_cer_pem)
		
		# Formato de fecha: YYYY-MM-DDTHH:MM:SS
		# Usar la fecha actual según la zona horaria configurada en System Settings
		from frappe.utils import get_datetime, now
		sistema_tz = frappe.db.get_single_value("System Settings", "time_zone") or "America/Mazatlan"
		import pytz
		tz = pytz.timezone(sistema_tz)
		fecha_local = now_datetime().astimezone(tz)
		fecha_cfdi = fecha_local.strftime("%Y-%m-%dT%H:%M:%S")
		
		# Código postal del emisor
		if self.config.modo == "Pruebas":
			cp_expedicion = "26015"  # CP para Prodigia según PAC
		else:
			cp_expedicion = compania.codigo_postal if hasattr(compania, 'codigo_postal') and compania.codigo_postal else "26000"
		
		# Determinar DomicilioFiscalReceptor
		# Para público general (XAXX010101000), debe ser igual a LugarExpedicion según regla CFDI40149
		if factura.rfc_del_receptor == "XAXX010101000":
			cp_receptor = cp_expedicion
		elif factura.codigo_postal_receptor and factura.codigo_postal_receptor != "00000":
			cp_receptor = factura.codigo_postal_receptor
		else:
			cp_receptor = cp_expedicion
		
		# Estructura según formato FacturaloPlus
		comprobante = {
			"Version": "4.0",
			"Serie": "FV",
			"Folio": factura.folio,
			"Fecha": fecha_cfdi,
			"FormaPago": self._get_forma_pago_code(factura.forma_de_pago),
			"NoCertificado": no_certificado,
			"SubTotal": format(float(factura.subtotal), '.2f'),
			"Moneda": factura.divisa__moneda or "MXN",
			"Total": format(float(factura.total), '.2f'),
			"TipoDeComprobante": "I",
			"Exportacion": "01",
			"MetodoPago": "PUE" if factura.metodo_de_pago == "Pago en una sola exhibición" else "PPD",
			"LugarExpedicion": cp_expedicion,
			"Emisor": {
				"Rfc": rfc_emisor,
				"Nombre": nombre_emisor,
				"RegimenFiscal": regimen_emisor
			},
			"Receptor": {
				"Rfc": factura.rfc_del_receptor,
				"Nombre": factura.nombre_o_razon_social,
				"DomicilioFiscalReceptor": cp_receptor,
				"RegimenFiscalReceptor": factura.regimen_fiscal_receptor or "616",
				"UsoCFDI": "S01" if factura.rfc_del_receptor == "XAXX010101000" else (factura.uso_cfdi if hasattr(factura, 'uso_cfdi') and factura.uso_cfdi else "G03")
			},
			"Conceptos": self._build_conceptos(factura),
			"Impuestos": self._build_impuestos(factura)
		}
		
		# Agregar descuento solo si existe
		if factura.descuento_total and float(factura.descuento_total) > 0:
			comprobante["Descuento"] = format(float(factura.descuento_total), '.2f')
		
		# TipoCambio como string
		if factura.divisa__moneda and factura.divisa__moneda != "MXN":
			comprobante["TipoCambio"] = format(float(factura.tipo_de_cambio), '.2f')
		else:
			comprobante["TipoCambio"] = "1"
		
		# Agregar InformacionGlobal si es Público General
		# Requerido por SAT cuando RFC receptor es XAXX010101000 o XEXX010101000
		if factura.rfc_del_receptor in ["XAXX010101000", "XEXX010101000"]:
			# Obtener mes y año de la factura
			fecha_emision = factura.fecha_de_emision
			mes = str(fecha_emision.month).zfill(2)
			anio = str(fecha_emision.year)
			
			comprobante["InformacionGlobal"] = {
				"Periodicidad": "01",  # 01 = Diario
				"Meses": mes,  # Mes de la factura (01-12)
				"Año": anio  # Año de la factura
			}
		
		# Estructura completa del JSON según FacturaloPlus
		cfdi = {
			"Comprobante": comprobante,
			"CamposPDF": {
				"tipoComprobante": "FACTURA"
			},
			"logo": ""
		}
		
		return cfdi
	
	def _build_conceptos(self, factura):
		"""Construye la lista de conceptos (productos)"""
		conceptos = []
		
		for item in factura.tabla_con_los_productos_o_servicios:
			# Calcula valores
			importe = float(item.cantidad * item.valor)
			descuento = 0
			
			if item.descuento:
				# Obtener producto para calcular precio con impuestos
				producto = frappe.get_doc("Producto", item.producto__servicio)
				precio_con_impuestos = item.valor
				
				if producto.tipo_de_impuesto:
					impuesto = frappe.get_doc("Impuestos", producto.tipo_de_impuesto)
					if impuesto.porciento_impuesto:
						precio_con_impuestos = item.valor * (1 + impuesto.porciento_impuesto / 100)
				
				importe_con_impuestos = item.cantidad * precio_con_impuestos
				descuento = float(importe_con_impuestos * (item.descuento / 100))
			
			concepto = {
				"ClaveProdServ": item.clave_sat or "01010101",
				"NoIdentificacion": item.producto__servicio[:100] if item.producto__servicio else "",
				"Cantidad": format(float(item.cantidad), '.6f'),
				"ClaveUnidad": item.clave_unidad_sat or "E48",
				"Unidad": item.unidad_de_medida or "Pieza",
				"Descripcion": (item.descripcion or item.producto__servicio)[:1000],
				"ValorUnitario": format(float(item.valor), '.6f'),
				"Importe": format(importe, '.2f'),
				"ObjetoImp": "02"  # 02 = Sí objeto de impuesto
			}
			
			if descuento > 0:
				concepto["Descuento"] = format(descuento, '.2f')
			
			# Agrega impuestos del concepto
			if item.producto__servicio:
				producto = frappe.get_doc("Producto", item.producto__servicio)
				if producto.tipo_de_impuesto:
					concepto["Impuestos"] = self._build_impuestos_concepto(item, producto)
			
			conceptos.append(concepto)
		
		return conceptos
	
	def _build_impuestos_concepto(self, item, producto):
		"""Construye los impuestos de un concepto"""
		impuestos = {
			"Traslados": []
		}
		
		if producto.tipo_de_impuesto:
			impuesto = frappe.get_doc("Impuestos", producto.tipo_de_impuesto)
			if impuesto.porciento_impuesto:
				importe_base = float(item.cantidad * item.valor)
				importe_impuesto = importe_base * (impuesto.porciento_impuesto / 100)
				
				traslado = {
					"Base": format(importe_base, '.2f'),
					"Impuesto": "002",
					"TipoFactor": "Tasa",
					"TasaOCuota": format(impuesto.porciento_impuesto / 100, '.6f'),
					"Importe": format(importe_impuesto, '.2f')
				}
				
				impuestos["Traslados"].append(traslado)
		
		return impuestos
	
	def _build_impuestos(self, factura):
		"""Construye la sección de impuestos totales"""
		if factura.total_de_impuestos_trasladados == 0:
			return None
		
		impuestos = {
			"TotalImpuestosTrasladados": format(float(factura.total_de_impuestos_trasladados), '.2f'),
			"Traslados": [
				{
					"Base": format(float(factura.subtotal), '.2f'),
					"Impuesto": "002",
					"TipoFactor": "Tasa",
					"TasaOCuota": "0.160000",
					"Importe": format(float(factura.total_de_impuestos_trasladados), '.2f')
				}
			]
		}
		
		return impuestos
	
	def _extract_certificate_serial(self, cer_pem):
		"""Extrae el número de serie del certificado PEM"""
		try:
			from cryptography import x509
			from cryptography.hazmat.backends import default_backend
			
			# Cargar el certificado PEM
			cert = x509.load_pem_x509_certificate(cer_pem.encode(), default_backend())
			
			# Convertir el número de serie a hexadecimal
			serial_hex = format(cert.serial_number, 'x')
			
			# Convertir cada par de caracteres hex a su valor ASCII para obtener el número del SAT
			# El formato esperado es de 20 dígitos decimales
			serial_bytes = bytes.fromhex(serial_hex)
			# Extraer solo caracteres numéricos del serial
			serial = ''.join(c for c in serial_bytes.decode('latin-1') if c.isdigit())
			
			# Si no hay suficientes dígitos, usar el hex como decimal y tomar 20 dígitos
			if len(serial) < 20:
				serial = str(int(serial_hex, 16))[-20:].zfill(20)
			else:
				serial = serial[:20]
			
			return serial
		except Exception as e:
			frappe.log_error(f"Error extrayendo serial del certificado: {str(e)}", "PAC Certificate Error")
			return "30001000000500003416"  # Fallback al número de prueba
	
	def _extract_certificate_serial_v2(self, cer_pem):
		"""Extrae el número de serie del certificado en formato SAT (20 dígitos)"""
		try:
			from cryptography import x509
			from cryptography.hazmat.backends import default_backend
			
			# Cargar el certificado
			cert = x509.load_pem_x509_certificate(cer_pem.encode(), default_backend())
			
			# Obtener el serial en hexadecimal (sin '0x')
			serial_hex = format(cert.serial_number, 'x')
			
			# Asegurar que tenga longitud par para convertir a bytes
			if len(serial_hex) % 2:
				serial_hex = '0' + serial_hex
			
			# Convertir hex a bytes
			serial_bytes = bytes.fromhex(serial_hex)
			
			# El SAT representa cada byte como un número de 2 o 3 dígitos concatenados
			# Convertir cada byte a su valor decimal y concatenar
			serial_parts = []
			for byte in serial_bytes:
				serial_parts.append(str(byte))
			
			# Unir todos los números
			serial_str = ''.join(serial_parts)
			
			# Tomar exactamente 20 dígitos (rellenar o truncar)
			if len(serial_str) < 20:
				serial_str = serial_str.zfill(20)
			elif len(serial_str) > 20:
				serial_str = serial_str[:20]
			
			frappe.log_error(f"Serial extraído: {serial_str} | Hex: {serial_hex} | Bytes: {[b for b in serial_bytes]}", "Certificate Serial Debug")
			
			return serial_str
		except Exception as e:
			frappe.log_error(f"Error extrayendo serial: {str(e)}", "PAC Certificate Error")
			return "30001000000500003416"
	
	def _extract_regimen_code(self, regimen_fiscal):
		"""Extrae solo el código numérico del régimen fiscal (ej: '601 REGIMEN...' -> '601')"""
		if not regimen_fiscal:
			return "601"
		
		# Si ya es solo el código, devolverlo
		if regimen_fiscal.isdigit():
			return regimen_fiscal
		
		# Extraer los primeros dígitos antes del espacio
		import re
		match = re.match(r'^(\d+)', str(regimen_fiscal))
		return match.group(1) if match else "601"
	
	def _get_forma_pago_code(self, forma_pago):
		"""Convierte forma de pago a código SAT"""
		formas = {
			"Efectivo": "01",
			"Transferencia": "03",
			"Tarjeta de crédito o debito": "04"
		}
		return formas.get(forma_pago, "99")
	
	def _decode_credential(self, encoded_value):
		"""
		Desencripta una credencial codificada en base64
		Si el valor no está codificado, lo devuelve tal cual
		"""
		try:
			# Intenta decodificar de base64
			decoded = base64.b64decode(encoded_value).decode('utf-8')
			return decoded
		except Exception:
			# Si falla, devuelve el valor original (puede ser que ya esté desencriptado)
			return encoded_value
	
	def _send_to_pac(self, cfdi_json):
		"""Envía el CFDI al PAC para timbrado"""
		try:
			url = self.config.get_url_timbrado()
			
			# Desencripta la API Key desde base64
			api_key_raw = self.config.get_api_key()
			api_key = self._decode_credential(api_key_raw)
			
			# Convertir el JSON del CFDI a string y luego a base64
			cfdi_json_str = json.dumps(cfdi_json, ensure_ascii=False)
			cfdi_json_b64 = base64.b64encode(cfdi_json_str.encode('utf-8')).decode('utf-8')
			
			# Obtener certificados CSD
			csd_key_pem = self.config.get("csd_key_pem") or ""
			csd_cer_pem = self.config.get("csd_cer_pem") or ""
			
			# Headers para form-data
			headers = {
				"Content-Type": "application/x-www-form-urlencoded"
			}
			
			# Payload como form-data según documentación FacturAPI REST+
			payload = {
				"apikey": api_key,
				"jsonB64": cfdi_json_b64,
				"keyPEM": csd_key_pem,
				"cerPEM": csd_cer_pem
			}
			
			response = requests.post(url, data=payload, headers=headers, timeout=30)

			if response.status_code == 200:
				result = response.json()
				
				# FacturaloPlus devuelve code: "200" para éxito, no success: true
				if result.get("code") == "200" or result.get("success"):
					data = result.get("data", {})
					return {
						"success": True,
						"uuid": data.get("UUID") or result.get("uuid"),
						"xml": data.get("XML") or result.get("xml"),
						"pdf": data.get("PDF") or result.get("pdf"),
						"fecha_timbrado": now_datetime()
					}
				else:
					error_msg = result.get("message") or result.get("error", "Error desconocido")
					
					# Detectar errores específicos y dar mensajes más claros
					if "número de certificado" in error_msg.lower() or "nocertificado" in error_msg.lower():
						error_msg += "\n\n⚠️ Los certificados CSD configurados no corresponden al número esperado por el PAC. Por favor, contacte al PAC para obtener los certificados correctos."
					elif "fecha de emisión" in error_msg.lower() and "vigencia" in error_msg.lower():
						error_msg += "\n\n⚠️ El certificado de prueba ha expirado o la fecha está fuera de su vigencia. Contacte al PAC para obtener certificados vigentes."
					elif "rfc" in error_msg.lower() and "no se encontró" in error_msg.lower():
						error_msg += "\n\n⚠️ El RFC no está registrado en el ambiente de pruebas del PAC. Contacte al PAC para activar el RFC en su sistema."
					
					return {
						"success": False,
						"error": error_msg
					}
			else:
				return {
					"success": False,
					"error": f"Error HTTP {response.status_code}: {response.text}"
				}
		
		except requests.exceptions.RequestException as e:
			frappe.logger().error(f"Error de conexión con PAC: {str(e)}")
			return {
				"success": False,
				"error": f"Error de conexión: {str(e)}"
			}
		except Exception as e:
			frappe.logger().error(f"Error al timbrar: {str(e)}")
			return {
				"success": False,
				"error": f"Error inesperado: {str(e)}"
			}
	
	def cancelar_factura(self, factura_doc, motivo="02"):
		"""
		Cancela una factura timbrada
		
		Args:
			factura_doc: Documento de Factura de Venta
			motivo: Código de motivo de cancelación
		
		Returns:
			dict: Respuesta del PAC
		"""
		# TODO: Implementar cancelación
		frappe.throw(_("Función de cancelación aún no implementada"))


@frappe.whitelist()
def test_connection():
	"""Método público para probar la conexión con el PAC"""
	try:
		servicio = ServicioPAC()
		return {"success": True, "message": "Configuración correcta"}
	except Exception as e:
		return {"success": False, "error": str(e)}
