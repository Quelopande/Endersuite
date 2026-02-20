# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TerminodePagoPlantilla(Document):
    def validate(self):
        self.validar_totales()

    def validar_totales(self):
        total_porcentaje = 0
        
        # Iteramos sobre la tabla hija 'terminos'
        for fila in self.terminos:
            total_porcentaje += fila.porcion_de_factura
        
        # Si no suma 100, lanzamos error
        if total_porcentaje != 100:
            frappe.throw(_("La suma de las porciones de factura debe ser exactamente 100%. Actual: {0}%").format(total_porcentaje))
