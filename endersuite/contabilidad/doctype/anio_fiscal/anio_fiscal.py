# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from datetime import date, timedelta


class AnioFiscal(Document):
	def before_validate(self):
		"""Autoestablece la fecha de fin al seleccionar fecha de inicio.
		Permite modificación posterior, pero la validación garantizará duración exacta de un año.
		"""
		if self.desde and not self.hasta:
			self.hasta = self._calcular_fecha_fin_automatica(self.desde)

	def validate(self):
		"""Garantiza que el año fiscal dure exactamente un año (365 o 366 días).
		Considera años bisiestos. No permite más ni menos.
		"""
		if not self.desde or not self.hasta:
			return

		inicio = getdate(self.desde)
		fin = getdate(self.hasta)
		if fin < inicio:
			# Normalizar: fin no puede ser antes que inicio
			raise_frappe("La fecha de fin no puede ser anterior a la fecha de inicio.")

		# Duración inclusiva en días
		duracion = (fin - inicio).days + 1
		if duracion not in (365, 366):
			raise_frappe(
				"El año fiscal debe durar exactamente 1 año. Duración actual: {0} días".format(duracion)
			)

		# Sugerencia: si el fin esperado difiere, mostrar alerta (no forzar cambio)
		fin_esperado = self._calcular_fecha_fin_automatica(inicio)
		# No modificamos automáticamente si el usuario lo cambió, solo validamos duración
		# Se puede agregar un info log si se requiere.

	def _calcular_fecha_fin_automatica(self, fecha_inicio):
		"""Calcula la fecha de fin como un año menos un día desde la fecha de inicio.
		Maneja años bisiestos (p. ej., inicio 29-Feb).
		"""
		inicio = getdate(fecha_inicio)
		# Intentar mover un año adelante la misma fecha
		try:
			fin_siguiente_anio = inicio.replace(year=inicio.year + 1)
		except ValueError:
			# Caso 29-Feb en año bisiesto: tomar 1-Mar del siguiente año y restar un día
			fin_siguiente_anio = date(inicio.year + 1, 3, 1)
		# Restar un día para tener fin inclusivo
		return fin_siguiente_anio - timedelta(days=1)


def raise_frappe(msg):
	import frappe
	from frappe import _
	frappe.throw(_(msg))