// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

// Eventos del child table poliza_movimiento
frappe.ui.form.on("poliza_movimiento", {
    categoria_contable(frm, cdt, cdn) {
        // Al seleccionar categoría contable, limpiar cuenta
        const row = locals[cdt][cdn];
        if (row.categoria_contable) {
            frappe.model.set_value(cdt, cdn, "cuenta", "");
            frappe.model.set_value(cdt, cdn, "nombre_cuenta", "");
        }
    },

    cuenta(frm, cdt, cdn) {
        // Autollenar nombre de cuenta si está vacío
        const row = locals[cdt][cdn];
        if (row.cuenta && !row.nombre_cuenta) {
            frappe.db.get_value("Cuenta", row.cuenta, "cuenta").then(r => {
                if (r && r.message && r.message.cuenta) {
                    frappe.model.set_value(cdt, cdn, "nombre_cuenta", r.message.cuenta);
                }
            });
        }
    },

    debe(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        // Si se captura Debe, limpiar Haber
        if (row.debe && flt(row.debe) > 0) {
            frappe.model.set_value(cdt, cdn, "haber", 0);
        }
        recalc_totals(frm);
    },

    haber(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        // Si se captura Haber, limpiar Debe
        if (row.haber && flt(row.haber) > 0) {
            frappe.model.set_value(cdt, cdn, "debe", 0);
        }
        recalc_totals(frm);
    }
});

function recalc_totals(frm) {
    let total_debe = 0;
    let total_haber = 0;

    (frm.doc.table_qbss || []).forEach(r => {
        total_debe += flt(r.debe);
        total_haber += flt(r.haber);
    });

    frm.set_value("total_debe", total_debe);
    frm.set_value("total_haber", total_haber);
    frm.set_value("diferencia", total_debe - total_haber);
    frm.set_value("cuadra", (total_debe - total_haber) === 0 ? 1 : 0);
}
