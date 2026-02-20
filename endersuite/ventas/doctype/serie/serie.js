// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Serie", {
    refresh(frm) {
        // Indicador de estado
        if (frm.doc.estado === "Disponible") {
            frm.dashboard.add_indicator(__("Disponible"), "green");
        } else if (frm.doc.estado === "Vendido") {
            frm.dashboard.add_indicator(__("Vendido"), "red");
        } else if (frm.doc.estado === "Dañado") {
            frm.dashboard.add_indicator(__("Dañado"), "orange");
        }
    }
});
