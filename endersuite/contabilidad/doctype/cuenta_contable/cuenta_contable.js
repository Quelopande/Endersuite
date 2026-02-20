// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cuenta Contable', {
	refresh: function (frm) {
		// Verificamos si el backend envió el HTML
		if (frm.doc.__onload && frm.doc.__onload.html_cuenta_t) {

			// Inyectamos el HTML en el campo 'visualizacion_t'
			// Si tu campo se llama diferente, cambia 'visualizacion_t' aquí abajo
			frm.fields_dict['visualizacion_t'].$wrapper.html(frm.doc.__onload.html_cuenta_t);
		}
	}
});
