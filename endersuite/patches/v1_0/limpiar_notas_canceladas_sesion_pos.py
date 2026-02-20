"""
Patch para limpiar notas de venta canceladas de las sesiones POS
"""

import frappe
from frappe import _


def execute():
	"""
	Remueve las notas de venta canceladas de todas las sesiones POS
	"""
	frappe.logger().info("Iniciando limpieza de notas canceladas en sesiones POS...")

	# Obtener todas las sesiones POS
	sesiones = frappe.get_all("Sesion POS", fields=["name", "estado"])

	sesiones_actualizadas = 0
	ventas_removidas = 0

	for sesion_data in sesiones:
		try:
			sesion = frappe.get_doc("Sesion POS", sesion_data.name)

			if not sesion.ventas:
				continue

			# Filtrar ventas válidas (solo enviadas, no canceladas)
			ventas_validas = []
			for venta in sesion.ventas:
				if venta.nota_de_venta:
					# Verificar que la nota existe y está enviada
					docstatus = frappe.db.get_value("Nota de Venta", venta.nota_de_venta, "docstatus")

					if docstatus == 1:  # Solo enviadas
						ventas_validas.append(venta)
					else:
						ventas_removidas += 1
						frappe.logger().info(
							f"Removiendo nota cancelada {venta.nota_de_venta} de sesión {sesion.name}"
						)

			# Si hubo cambios, actualizar la sesión
			if len(ventas_validas) != len(sesion.ventas):
				# Limpiar y reagregar solo ventas válidas
				sesion.ventas = []
				for venta in ventas_validas:
					sesion.append('ventas', {
						'nota_de_venta': venta.nota_de_venta,
						'total': venta.total,
						'metodo_pago': venta.metodo_pago
					})

				# Guardar sin disparar validaciones completas
				sesion.flags.ignore_validate = True
				sesion.flags.ignore_mandatory = True
				sesion.save(ignore_permissions=True)

				sesiones_actualizadas += 1

		except Exception as e:
			frappe.log_error(
				f"Error procesando sesión {sesion_data.name}: {str(e)}",
				"Limpieza Sesiones POS"
			)
			continue

	frappe.db.commit()

	frappe.logger().info(
		f"Limpieza completada: {sesiones_actualizadas} sesiones actualizadas, "
		f"{ventas_removidas} ventas canceladas removidas"
	)

	print(f"✓ Sesiones actualizadas: {sesiones_actualizadas}")
	print(f"✓ Ventas canceladas removidas: {ventas_removidas}")
