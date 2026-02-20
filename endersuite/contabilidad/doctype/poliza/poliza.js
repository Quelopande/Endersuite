// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Poliza", {
	refresh(frm) {
		// Agregar indicador visual de cuadre
		if (frm.doc.docstatus === 0) {
			if (frm.doc.cuadra) {
				frm.dashboard.set_headline_alert("✓ La póliza está cuadrada", "green");
			} else if (frm.doc.diferencia != 0) {
				frm.dashboard.set_headline_alert(
					`⚠ Diferencia: ${format_currency(frm.doc.diferencia, frm.doc.currency)}`,
					"orange"
				);
			}
		}
	},

	setup(frm) {
		// Filtrar categorías contables (solo raíces protegidas)
		frm.set_query("categoria_contable", "table_qbss", function () {
			if (frm.doc.compañia) {
				return {
					query: "endersuite.contabilidad.doctype.poliza.poliza.get_categorias_contables",
					filters: {
						compania: frm.doc.compañia
					}
				};
			}
		});

		// Filtrar cuentas según categoría contable seleccionada
		frm.set_query("cuenta", "table_qbss", function (doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			if (row.categoria_contable && frm.doc.compañia) {
				return {
					query: "endersuite.contabilidad.doctype.poliza.poliza.get_cuentas_by_categoria",
					filters: {
						categoria_cuenta: row.categoria_contable,
						compania: frm.doc.compañia
					}
				};
			} else if (frm.doc.compañia) {
				return {
					query: "endersuite.contabilidad.doctype.poliza.poliza.get_cuentas_by_compania",
					filters: {
						compania: frm.doc.compañia
					}
				};
			}
		});
	},

	fecha(frm) {
		// Calcular período automáticamente cuando cambia la fecha
		if (frm.doc.fecha) {
			let fecha = new Date(frm.doc.fecha);
			let meses = [
				"Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
				"Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
			];
			frm.set_value("periodo", meses[fecha.getMonth()]);
		}
	},

	compañia(frm) {
		// Auto-seleccionar año fiscal por defecto
		if (frm.doc.compañia && !frm.doc.anio_fiscal) {
			frappe.db.get_value("Anio Fiscal", {
				"es_por_defecto": 1
			}, "name", (r) => {
				if (r && r.name) {
					frm.set_value("anio_fiscal", r.name);
				}
			});
		}
	}
});

// Eventos de la tabla de movimientos
frappe.ui.form.on("poliza_movimiento", {
	cuenta(frm, cdt, cdn) {
		// Traer el nombre de la cuenta automáticamente
		let row = locals[cdt][cdn];
		if (row.cuenta) {
			frappe.db.get_value("Cuenta", row.cuenta, "cuenta", (r) => {
				if (r && r.cuenta) {
					frappe.model.set_value(cdt, cdn, "nombre_cuenta", r.cuenta);
				}
			});
		}
	},

	debe(frm, cdt, cdn) {
		calcular_totales(frm);
		let row = locals[cdt][cdn];
		// Si se llena debe, limpiar haber
		if (row.debe && row.debe > 0) {
			frappe.model.set_value(cdt, cdn, "haber", 0);
		}
	},

	haber(frm, cdt, cdn) {
		calcular_totales(frm);
		let row = locals[cdt][cdn];
		// Si se llena haber, limpiar debe
		if (row.haber && row.haber > 0) {
			frappe.model.set_value(cdt, cdn, "debe", 0);
		}
	},

	table_qbss_remove(frm) {
		// Recalcular totales cuando se elimina una fila
		calcular_totales(frm);
	}
});

// Función auxiliar para calcular totales
function calcular_totales(frm) {
	let total_debe = 0;
	let total_haber = 0;

	frm.doc.table_qbss.forEach(row => {
		total_debe += flt(row.debe);
		total_haber += flt(row.haber);
	});

	frm.set_value("total_debe", total_debe);
	frm.set_value("total_haber", total_haber);
	frm.set_value("diferencia", total_debe - total_haber);
	frm.set_value("cuadra", (total_debe - total_haber) === 0 ? 1 : 0);

	// Actualizar el indicador visual
	if (frm.doc.cuadra) {
		frm.dashboard.set_headline_alert("✓ La póliza está cuadrada", "green");
	} else if (frm.doc.diferencia != 0) {
		frm.dashboard.set_headline_alert(
			`⚠ Diferencia: ${format_currency(frm.doc.diferencia, frm.doc.currency)}`,
			"orange"
		);
	}
}
