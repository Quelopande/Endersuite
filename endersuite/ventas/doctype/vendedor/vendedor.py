# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Vendedor(Document):
	def validate(self):
		# Validar que el usuario no este asignado a otro vendedor activo
		if self.user_id:
			exists = frappe.db.exists("Vendedor", {
				"user_id": self.user_id,
				"name": ["!=", self.name],
				"estado": "Activo"
			})
			
			if exists:
				frappe.throw(f"El usuario {self.user_id} ya está asignado a otro vendedor.")