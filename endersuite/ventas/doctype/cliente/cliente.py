# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import re


class Cliente(Document):
	def before_save(self):
		"""Auto-completar datos según tipo de cliente"""
		
		# Auto-rellenar Público General Nacional
		if self.tipo_de_cliente == "Publico General Nacional":
			self.rfc = "XAXX010101000"
			self.nombre_completo = "PUBLICO EN GENERAL"
			self.codigo_postal = "06000"
			self.primer_nombre = None
			self.segundo_nombre = None
			self.primer_apellido = None
			self.segundo_apellido = None
			self.razon_social = None
			
		# Auto-rellenar Público General Extranjero
		elif self.tipo_de_cliente == "Publico General Extranjero":
			self.rfc = "XEXX010101000"
			self.nombre_completo = "PUBLICO EN GENERAL (EXTRANJERO)"
			self.codigo_postal = "00000"
			self.primer_nombre = None
			self.segundo_nombre = None
			self.primer_apellido = None
			self.segundo_apellido = None
			self.razon_social = None
			
		# Construir nombre para Persona Moral
		elif self.tipo_de_cliente == "Persona Moral":
			if self.razon_social:
				self.nombre_completo = self.razon_social.upper()
			self.primer_nombre = None
			self.segundo_nombre = None
			self.primer_apellido = None
			self.segundo_apellido = None
			
		# Construir nombre para Persona Física
		elif self.tipo_de_cliente == "Persona Física":
			partes = [
				self.primer_nombre,
				self.segundo_nombre,
				self.primer_apellido,
				self.segundo_apellido
			]
			self.nombre_completo = ' '.join(filter(None, partes)).upper()
			self.razon_social = None
		
		# Normalizar RFC a mayúsculas
		if self.rfc:
			self.rfc = self.rfc.upper().strip()
	
	def validate(self):
		"""Validaciones según tipo de cliente"""
		
		# Validar Persona Física
		if self.tipo_de_cliente == "Persona Física":
			if not self.primer_nombre or not self.primer_apellido:
				frappe.throw("Primer nombre y apellido son obligatorios para Persona Física")
			
			if self.rfc and self.rfc not in ["XAXX010101000", "XEXX010101000"]:
				if len(self.rfc) != 13:
					frappe.throw(f"RFC de Persona Física debe tener 13 caracteres. Tiene {len(self.rfc)}")
		
		# Validar Persona Moral
		elif self.tipo_de_cliente == "Persona Moral":
			if not self.razon_social:
				frappe.throw("Razón Social es obligatoria para Persona Moral")
			
			if self.rfc and self.rfc not in ["XAXX010101000", "XEXX010101000"]:
				if len(self.rfc) != 12:
					frappe.throw(f"RFC de Persona Moral debe tener 12 caracteres. Tiene {len(self.rfc)}")
		
		# Validar formato de RFC
		if self.rfc and not self.rfc.startswith("X"):
			# RFC debe contener solo letras y números
			if not re.match(r'^[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}$', self.rfc):
				frappe.throw(f"Formato de RFC inválido: {self.rfc}")
		
		# Validar código postal (5 dígitos)
		if self.codigo_postal and not re.match(r'^\d{5}$', self.codigo_postal):
			frappe.throw(f"Código Postal debe tener 5 dígitos. Proporcionado: {self.codigo_postal}")
