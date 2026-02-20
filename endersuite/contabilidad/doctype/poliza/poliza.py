# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, get_datetime


class Poliza(Document):
	def before_validate(self):
		"""Se ejecuta antes de validar el documento"""
		self.calcular_periodo()
	
	def validate(self):
		"""Validaciones antes de guardar"""
		self.validar_anio_fiscal()
		self.calcular_totales()
		self.validar_cuadre()
		self.validar_movimientos()
	
	def calcular_periodo(self):
		"""Calcula el período (mes) automáticamente desde la fecha"""
		if self.fecha:
			fecha = get_datetime(self.fecha)
			meses = [
				"Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
				"Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
			]
			self.periodo = meses[fecha.month - 1]
	
	def calcular_totales(self):
		"""Calcula los totales de debe, haber y diferencia"""
		self.total_debe = 0
		self.total_haber = 0
		
		for movimiento in self.table_qbss:
			self.total_debe += flt(movimiento.debe)
			self.total_haber += flt(movimiento.haber)
		
		self.diferencia = flt(self.total_debe - self.total_haber, 2)
		self.cuadra = 1 if self.diferencia == 0 else 0
	
	def validar_cuadre(self):
		"""Valida que la póliza esté cuadrada (debe = haber)"""
		if self.diferencia != 0:
			frappe.throw(_(
				"La póliza no está cuadrada. Debe: {0}, Haber: {1}, Diferencia: {2}"
			).format(
				frappe.format(self.total_debe, {'fieldtype': 'Currency'}),
				frappe.format(self.total_haber, {'fieldtype': 'Currency'}),
				frappe.format(self.diferencia, {'fieldtype': 'Currency'})
			))
	
	def validar_movimientos(self):
		"""Valida que haya al menos 2 movimientos"""
		if len(self.table_qbss) < 2:
			frappe.throw(_("Debe haber al menos 2 movimientos contables"))
		
		# Validar que cada movimiento tenga cuenta y al menos debe o haber
		for idx, movimiento in enumerate(self.table_qbss, start=1):
			if not movimiento.cuenta:
				frappe.throw(_("Fila {0}: Debe seleccionar una cuenta").format(idx))
			
			if flt(movimiento.debe) == 0 and flt(movimiento.haber) == 0:
				frappe.throw(_(
					"Fila {0}: Debe ingresar un monto en Debe o Haber"
				).format(idx))
			
			if flt(movimiento.debe) > 0 and flt(movimiento.haber) > 0:
				frappe.throw(_(
					"Fila {0}: No puede tener monto en Debe y Haber simultáneamente"
				).format(idx))
	
	def validar_anio_fiscal(self):
		"""Valida que la fecha esté dentro del año fiscal"""
		if not self.anio_fiscal:
			return
		
		anio = frappe.get_doc("Anio Fiscal", self.anio_fiscal)
		fecha_poliza = get_datetime(self.fecha).date()
		
		if fecha_poliza < getdate(anio.desde) or fecha_poliza > getdate(anio.hasta):
			frappe.throw(_(
				"La fecha {0} está fuera del rango del año fiscal {1} ({2} - {3})"
			).format(
				frappe.format(fecha_poliza, {'fieldtype': 'Date'}),
				anio.nombre,
				frappe.format(anio.desde, {'fieldtype': 'Date'}),
				frappe.format(anio.hasta, {'fieldtype': 'Date'})
			))
		
		# Validar que el año fiscal esté abierto
		if anio.estado == "Cerrado":
			frappe.throw(_(
				"No se pueden crear pólizas en el año fiscal {0} porque está cerrado"
			).format(anio.nombre))


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_cuentas_by_compania(doctype, txt, searchfield, start, page_len, filters):
	"""Filtra las cuentas del catálogo según la compañía seleccionada en la póliza"""
	compania = filters.get("compania")
	
	if not compania:
		return []
	
	# Obtener el catálogo de la compañía
	catalogo = frappe.db.get_value("Compania", compania, "catalogo")
	
	if not catalogo:
		return []
	
	# Filtrar solo cuentas que NO sean grupo (para que puedan usarse en movimientos)
	return frappe.db.sql("""
		SELECT name, cuenta
		FROM `tabCuenta`
		WHERE catalogo = %(catalogo)s
			AND is_group = 0
			AND (cuenta LIKE %(txt)s OR name LIKE %(txt)s)
		ORDER BY cuenta
		LIMIT %(start)s, %(page_len)s
	""", {
		"catalogo": catalogo,
		"txt": "%%{0}%%".format(txt),
		"start": start,
		"page_len": page_len
	})


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_categorias_contables(doctype, txt, searchfield, start, page_len, filters):
	"""Obtiene las categorías contables (cuentas raíz protegidas) del catálogo de la compañía"""
	compania = filters.get("compania")
	
	if not compania:
		return []
	
	# Obtener el catálogo de la compañía
	catalogo = frappe.db.get_value("Compania", compania, "catalogo")
	
	if not catalogo:
		return []
	
	# Devolver solo las cuentas raíz protegidas (categorías) y mostrar solo el nombre limpio en el selector
	return frappe.db.sql("""
		SELECT name, cuenta as description
		FROM `tabCuenta`
		WHERE catalogo = %(catalogo)s
			AND protected_root = 1
			AND is_group = 1
			AND (cuenta LIKE %(txt)s OR name LIKE %(txt)s)
		ORDER BY cuenta
		LIMIT %(start)s, %(page_len)s
	""", {
		"catalogo": catalogo,
		"txt": "%%{0}%%".format(txt),
		"start": start,
		"page_len": page_len
	})


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_cuentas_by_categoria(doctype, txt, searchfield, start, page_len, filters):
	"""Filtra cuentas según la categoría contable (cuenta raíz) seleccionada"""
	categoria_cuenta = filters.get("categoria_cuenta")
	compania = filters.get("compania")
	
	if not categoria_cuenta or not compania:
		return []
	
	# Obtener el catálogo de la compañía
	catalogo = frappe.db.get_value("Compania", compania, "catalogo")
	
	if not catalogo:
		return []
	
	# Obtener el rango lft/rgt de la categoría
	categoria_data = frappe.db.get_value("Cuenta", categoria_cuenta, ["lft", "rgt"], as_dict=1)
	
	if not categoria_data:
		return []
	
	# Filtrar solo cuentas que NO sean grupo y estén dentro del rango de la categoría, mostrando solo el nombre limpio en el selector
	return frappe.db.sql("""
		SELECT name, cuenta as description
		FROM `tabCuenta`
		WHERE catalogo = %(catalogo)s
			AND is_group = 0
			AND lft > %(lft)s
			AND rgt < %(rgt)s
			AND (cuenta LIKE %(txt)s OR name LIKE %(txt)s)
		ORDER BY lft
		LIMIT %(start)s, %(page_len)s
	""", {
		"catalogo": catalogo,
		"lft": categoria_data.lft,
		"rgt": categoria_data.rgt,
		"txt": "%%{0}%%".format(txt),
		"start": start,
		"page_len": page_len
	})
