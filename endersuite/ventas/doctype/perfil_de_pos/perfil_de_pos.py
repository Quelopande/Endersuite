# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PerfildePOS(Document):
	def validate(self):
		"""Validaciones del Perfil POS"""
		self.validar_metodos_de_pago()
		self.validar_almacen()

	def validar_metodos_de_pago(self):
		"""Valida que no haya métodos de pago duplicados y solo un predeterminado"""
		if not self.metodos_de_pago:
			frappe.throw(_("Debe configurar al menos un método de pago para el perfil POS"))

		metodos = []
		predeterminados = 0
		habilitados = 0

		for idx, row in enumerate(self.metodos_de_pago, start=1):
			# Validar duplicados
			if row.metodo in metodos:
				frappe.throw(
					_("El método de pago '{0}' está duplicado en la fila #{1}. No se puede agregar el mismo método dos veces.").format(
						row.metodo, idx
					)
				)
			metodos.append(row.metodo)

			# Contar predeterminados
			if row.predeterminado:
				predeterminados += 1

			# Contar habilitados
			if row.habilitado:
				habilitados += 1

		# Validar solo un predeterminado
		if predeterminados > 1:
			frappe.throw(_("Solo puede haber un método de pago marcado como predeterminado"))

		# Validar que hay al menos un método habilitado
		if habilitados == 0:
			frappe.throw(_("Debe tener al menos un método de pago habilitado"))

	def validar_almacen(self):
		"""Valida que el almacén esté configurado"""
		if not self.almacen:
			frappe.throw(_("Debe seleccionar un almacén para el perfil POS"))
