// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cliente", {
    refresh(frm) {
        // Si es un nuevo documento, establecer Persona Física por defecto
        if (frm.is_new() && !frm.doc.tipo_de_cliente) {
            frm.set_value('tipo_de_cliente', 'Persona Física');
        }
    },

    tipo_de_cliente(frm) {
        // Auto-rellenar según tipo de cliente
        if (frm.doc.tipo_de_cliente === "Publico General Nacional") {
            auto_rellenar_publico_general_nacional(frm);
        } else if (frm.doc.tipo_de_cliente === "Publico General Extranjero") {
            auto_rellenar_publico_general_extranjero(frm);
        } else {
            // Limpiar campos de públicos generales
            if (frm.doc.rfc && (frm.doc.rfc === "XAXX010101000" || frm.doc.rfc === "XEXX010101000")) {
                frm.set_value('rfc', '');
                frm.set_value('nombre_completo', '');
            }
        }

        // Refrescar campos para que se muestren/oculten según depends_on
        frm.refresh_fields();
    }
});

function auto_rellenar_publico_general_nacional(frm) {
    frappe.confirm(
        '¿Desea auto-completar los datos para Público General Nacional?',
        () => {
            // Usuario confirmó
            frm.set_value('rfc', 'XAXX010101000');
            frm.set_value('nombre_completo', 'PUBLICO EN GENERAL');
            frm.set_value('codigo_postal', '06000');            // Limpiar campos de persona física y moral
            frm.set_value('primer_nombre', '');
            frm.set_value('segundo_nombre', '');
            frm.set_value('primer_apellido', '');
            frm.set_value('segundo_apellido', '');
            frm.set_value('razon_social', '');
            frm.set_value('nombre_comercial', '');

            frappe.show_alert({
                message: 'Datos de Público General Nacional configurados',
                indicator: 'green'
            }, 3);

            // Hacer el guardado más fácil
            frm.dirty();
        },
        () => {
            // Usuario canceló, no hacer nada
        }
    );
}

function auto_rellenar_publico_general_extranjero(frm) {
    frappe.confirm(
        '¿Desea auto-completar los datos para Público General Extranjero?',
        () => {
            // Usuario confirmó
            frm.set_value('rfc', 'XEXX010101000');
            frm.set_value('nombre_completo', 'PUBLICO EN GENERAL (EXTRANJERO)');
            frm.set_value('codigo_postal', '00000');            // Limpiar campos de persona física y moral
            frm.set_value('primer_nombre', '');
            frm.set_value('segundo_nombre', '');
            frm.set_value('primer_apellido', '');
            frm.set_value('segundo_apellido', '');
            frm.set_value('razon_social', '');
            frm.set_value('nombre_comercial', '');

            frappe.show_alert({
                message: 'Datos de Público General Extranjero configurados',
                indicator: 'green'
            }, 3);

            // Hacer el guardado más fácil
            frm.dirty();
        },
        () => {
            // Usuario canceló, no hacer nada
        }
    );
}
