# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Compania(Document):
    def autoname(self):
        """Genera las iniciales automáticamente desde el nombre de la empresa"""
        if self.nombre_de_la_empresa:
            words = self.nombre_de_la_empresa.split()
            initials = "".join([word[0] for word in words if word])
            self.iniciales_de_la_empresa = initials.upper()
            # Establece el nombre del documento
            self.name = self.iniciales_de_la_empresa
