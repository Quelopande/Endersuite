// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sesion POS", {
    refresh(frm) {
        // Agregar indicador de estado
        if (frm.doc.estado === "Abierta") {
            frm.dashboard.add_indicator(__("Sesión Abierta"), "green");
        } else if (frm.doc.estado === "Cerrada") {
            frm.dashboard.add_indicator(__("Sesión Cerrada"), "red");
        }

        // Mostrar totales de arqueo si está cerrada
        if (frm.doc.estado === "Cerrada" && frm.doc.diferencia !== undefined) {
            const color = Math.abs(frm.doc.diferencia) < 1 ? "blue" : (frm.doc.diferencia > 0 ? "green" : "orange");
            frm.dashboard.add_indicator(
                __("Diferencia: {0}", [format_currency(frm.doc.diferencia, frm.doc.currency)]),
                color
            );
        }
    },

    efectivo_contado(frm) {
        // Calcular diferencia cuando se ingresa efectivo contado
        if (frm.doc.efectivo_contado !== undefined && frm.doc.total_efectivo_sistema !== undefined) {
            const total_efectivo = (frm.doc.total_efectivo_sistema || 0) + (frm.doc.monto_apertura || 0);
            frm.set_value("diferencia", frm.doc.efectivo_contado - total_efectivo);
        }
    }
});
