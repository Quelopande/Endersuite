"""
Servicio centralizado para el manejo de métodos de pago y cálculos de totales
"""

import frappe
from frappe import _


@frappe.whitelist()
def calcular_totales_por_metodo(notas_de_venta):
	"""
	Calcula totales agrupados por método de pago usando los datos reales de las notas.

	Args:
		notas_de_venta (list): Lista de nombres de Notas de Venta

	Returns:
		dict: Totales agrupados por método de pago
	"""
	if isinstance(notas_de_venta, str):
		import json
		notas_de_venta = json.loads(notas_de_venta)

	totales = {}

	for nota_name in notas_de_venta:
		# Obtener métodos de pago de esta nota
		metodos = frappe.get_all(
			"Metodos de Pago Nota",
			filters={"parent": nota_name, "parenttype": "Nota de Venta"},
			fields=["metodo", "monto"]
		)

		for metodo_pago in metodos:
			metodo = metodo_pago.metodo
			monto = metodo_pago.monto or 0

			if metodo not in totales:
				totales[metodo] = 0
			totales[metodo] += monto

	return totales


def validar_metodo_pago_existe(metodo):
	"""
	Valida que un método de pago existe y está activo.

	Args:
		metodo (str): Nombre del método de pago

	Returns:
		bool: True si existe, False en caso contrario
	"""
	if not metodo:
		return False

	return frappe.db.exists("Metodos de Pago", metodo)


def obtener_cuenta_contable(metodo):
	"""
	Obtiene la cuenta contable asociada a un método de pago.

	Args:
		metodo (str): Nombre del método de pago

	Returns:
		str: Nombre de la cuenta contable o None
	"""
	if not metodo:
		return None

	return frappe.db.get_value("Metodos de Pago", metodo, "cuenta_contable")


@frappe.whitelist()
def validar_metodos_pago_perfil(perfil_pos):
	"""
	Valida que todos los métodos de pago configurados en un perfil POS existan.

	Args:
		perfil_pos (str): Nombre del Perfil POS

	Returns:
		dict: {"valido": bool, "errores": list, "advertencias": list}
	"""
	errores = []
	advertencias = []

	# Obtener métodos configurados en el perfil
	metodos_perfil = frappe.get_all(
		"Metodos de Pago POS",
		filters={"parent": perfil_pos, "parenttype": "Perfil de POS"},
		fields=["metodo", "habilitado", "predeterminado"]
	)

	if not metodos_perfil:
		errores.append(_("El perfil POS no tiene métodos de pago configurados"))
		return {
			"valido": False,
			"errores": errores,
			"advertencias": advertencias
		}

	for metodo_config in metodos_perfil:
		metodo = metodo_config.metodo

		# Validar que el método existe
		if not frappe.db.exists("Metodos de Pago", metodo):
			errores.append(
				_("El método de pago '{0}' configurado en el perfil no existe").format(metodo)
			)
			continue

		# Validar que tiene cuenta contable si está habilitado
		if metodo_config.habilitado:
			cuenta = obtener_cuenta_contable(metodo)
			if not cuenta:
				advertencias.append(
					_("El método de pago '{0}' no tiene cuenta contable asociada").format(metodo)
				)

	# Validar que hay al menos un método habilitado
	metodos_habilitados = [m for m in metodos_perfil if m.habilitado]
	if not metodos_habilitados:
		errores.append(_("El perfil POS no tiene ningún método de pago habilitado"))

	# Validar que no hay más de un método predeterminado
	metodos_predeterminados = [m for m in metodos_perfil if m.predeterminado]
	if len(metodos_predeterminados) > 1:
		advertencias.append(
			_("El perfil POS tiene {0} métodos de pago marcados como predeterminados. Solo debería haber uno.").format(
				len(metodos_predeterminados)
			)
		)

	return {
		"valido": len(errores) == 0,
		"errores": errores,
		"advertencias": advertencias
	}


def obtener_metodo_predeterminado(perfil_pos):
	"""
	Obtiene el método de pago predeterminado de un perfil POS.

	Args:
		perfil_pos (str): Nombre del Perfil POS

	Returns:
		str: Nombre del método predeterminado o el primero habilitado
	"""
	# Buscar método marcado como predeterminado
	predeterminado = frappe.db.get_value(
		"Metodos de Pago POS",
		{
			"parent": perfil_pos,
			"parenttype": "Perfil de POS",
			"predeterminado": 1,
			"habilitado": 1
		},
		"metodo"
	)

	if predeterminado:
		return predeterminado

	# Si no hay predeterminado, devolver el primer método habilitado
	primer_habilitado = frappe.db.get_value(
		"Metodos de Pago POS",
		{
			"parent": perfil_pos,
			"parenttype": "Perfil de POS",
			"habilitado": 1
		},
		"metodo"
	)

	return primer_habilitado
