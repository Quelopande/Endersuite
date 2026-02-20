// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Lote", {
    refresh(frm) {
        // Indicador de stock
        if (frm.doc.cantidad_disponible <= 0) {
            frm.dashboard.add_indicator(__("Sin Stock"), "red");
        } else {
            frm.dashboard.add_indicator(__("Stock: {0}", [frm.doc.cantidad_disponible]), "green");
        }
    }
});
