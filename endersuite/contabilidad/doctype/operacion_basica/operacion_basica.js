// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Operacion Basica', {
	setup: function (frm) {
		// 1. Filtrar 'cuenta_pago' (Bancos/Caja)
		frm.set_query('cuenta_pago', function () {
			return {
				filters: {
					'is_group': 0,
					// CORRECCIÓN: Usamos 'compania' para filtrar
					'company': frm.doc.compania,
					'account_type': ['in', ['Bank', 'Cash']]
				}
			};
		});

		// 2. Filtrar 'cuenta_destino'
		frm.set_query('cuenta_destino', function () {
			return {
				filters: {
					'is_group': 0,
					// CORRECCIÓN: Usamos 'compania' para filtrar
					'company': frm.doc.compania
				}
			};
		});
	},

	categoria: function (frm) {
		if (frm.doc.categoria) {
			// CORRECCIÓN: Nombre del DocType actualizado a "Categoria de Operacion"
			frappe.db.get_value('Categoria de Operacion', frm.doc.categoria, 'cuenta_predeterminada')
				.then(r => {
					if (r && r.message && r.message.cuenta_predeterminada) {
						frm.set_value('cuenta_destino', r.message.cuenta_predeterminada);
					}
				});
		} else {
			frm.set_value('cuenta_destino', null);
		}
	}
});
