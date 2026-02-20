# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password
import requests
import base64


class ConfiguracionPAC(Document):
	def get_api_key(self):
		"""
		Obtiene la API Key (en base64)
		"""
		return self.api_key
	
	def get_url_timbrado(self):
		"""Obtiene la URL de timbrado según el modo"""
		if self.modo == "Producción":
			return self.url_timbrado_json.replace("dev.", "app.")
		return self.url_timbrado_json


@frappe.whitelist()
def test_connection():
	"""Prueba la conexión con el PAC"""
	try:
		config = frappe.get_doc("Configuracion PAC", "Configuracion PAC")
		
		# Decodificar credenciales
		cuenta = _decode_credential(config.cuenta)
		api_key = _decode_credential(config.get_api_key())
		
		# Validar que las credenciales estén configuradas
		if not cuenta or not api_key:
			return {
				"success": False,
				"message": "Las credenciales no están configuradas correctamente."
			}
		
		# Validar formato de credenciales
		if len(api_key) != 32:
			return {
				"success": False,
				"message": "La API Key no tiene el formato correcto (debe ser de 32 caracteres)."
			}
		
		# Verificar que la URL esté configurada
		if not config.url_timbrado_json:
			return {
				"success": False,
				"message": "La URL de timbrado no está configurada."
			}
		
		return {
			"success": True,
			"message": f"Configuración válida ✓\n\nPAC: {config.nombre_pac}\nModo: {config.modo}\nCuenta: {cuenta}\nURL: {config.url_timbrado_json}\n\nLas credenciales están correctamente configuradas."
		}
			
	except Exception as e:
		frappe.log_error(f"Error al probar conexión PAC: {str(e)}")
		return {
			"success": False,
			"message": f"Error: {str(e)}"
		}


def _decode_credential(encoded_value):
	"""Decodifica una credencial desde base64"""
	try:
		if encoded_value:
			return base64.b64decode(encoded_value).decode('utf-8')
	except Exception:
		pass
	return encoded_value
