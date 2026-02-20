// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Perfil de POS", {
    refresh(frm) {

    }
});

frappe.ui.form.on("Metodos de Pago POS", {
    metodos_de_pago_add: function (frm, cdt, cdn) {
        if (frm.doc.metodos_de_pago.length === 1) {
            frappe.model.set_value(cdt, cdn, "predeterminado", 1);
        }
    },
    metodo: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.metodo) {
            let duplicates = frm.doc.metodos_de_pago.filter(d => d.metodo === row.metodo && d.name !== row.name);
            if (duplicates.length > 0) {
                frappe.msgprint(__("El método de pago {0} ya está agregado", [row.metodo]));
                frappe.model.set_value(cdt, cdn, "metodo", "");
            }
        }
    },
    predeterminado: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.predeterminado) {
            frm.doc.metodos_de_pago.forEach(d => {
                if (d.name !== row.name && d.predeterminado) {
                    frappe.model.set_value(cdt, d.name, "predeterminado", 0);
                    frappe.show_alert(__("Se ha desactivado el método predeterminado anterior"));
                }
            });
        } else {
            // Prevent unchecking if it's the only one or no other is checked
            let any_checked = frm.doc.metodos_de_pago.some(d => d.predeterminado);
            if (!any_checked) {
                frappe.msgprint(__("Debe haber al menos un método de pago predeterminado"));
                frappe.model.set_value(cdt, cdn, "predeterminado", 1);
            }
        }
    }
});

