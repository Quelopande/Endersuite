// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt


frappe.ui.form.on("Producto", {
    refresh(frm) {
        // Recalcular precios al cargar el formulario
        frm.events.recalcular_precios(frm);
    },

    tipo_de_impuesto(frm) {
        frm.events.recalcular_precios(frm);
    },

    costo(frm) {
        frm.events.recalcular_precios(frm);
    },

    recalcular_precios(frm) {
        const impuesto_name = frm.doc.tipo_de_impuesto;

        if (impuesto_name) {
            frappe.db.get_value("Impuestos", impuesto_name, ["porciento_impuesto", "incluido_en_el_precio"], (r) => {
                const porcentaje = r && r.porciento_impuesto ? r.porciento_impuesto : 0;
                const incluido = r && r.incluido_en_el_precio ? r.incluido_en_el_precio : 0;
                const costo = flt(frm.doc.costo);

                frm.doc.table_rzld.forEach(row => {
                    const precio_unitario = flt(row.precio_unitario);

                    if (incluido) {
                        // IVA INCLUIDO - El precio ya incluye impuestos (RETENIDO)
                        // La empresa absorbe/paga el impuesto
                        const precio_sin_impuestos = precio_unitario / (1 + (porcentaje / 100));
                        row.impuestos_retenidos = precio_unitario - precio_sin_impuestos;
                        row.impuestos_trasladados = 0;
                        row.precio_total = precio_unitario;
                        // Ganancia = Precio - Costo - Impuesto que paga la empresa
                        row.ganancia_bruta = precio_unitario - costo - row.impuestos_retenidos;
                    } else {
                        // IVA NO INCLUIDO - Los impuestos se suman al precio (TRASLADADO)
                        // El cliente paga el impuesto
                        const impuesto_calculado = precio_unitario * (porcentaje / 100);
                        row.impuestos_retenidos = 0;
                        row.impuestos_trasladados = impuesto_calculado;
                        row.precio_total = precio_unitario + impuesto_calculado;
                        // Ganancia = Precio - Costo (el impuesto lo paga el cliente)
                        row.ganancia_bruta = precio_unitario - costo;
                    }
                });
                frm.refresh_field("table_rzld");
            });
        } else {
            const costo = flt(frm.doc.costo);
            frm.doc.table_rzld.forEach(row => {
                const precio_unitario = flt(row.precio_unitario);
                row.impuestos_trasladados = 0;
                row.impuestos_retenidos = 0;
                row.precio_total = precio_unitario;
                row.ganancia_bruta = precio_unitario - costo;
            });
            frm.refresh_field("table_rzld");
        }
    }
});

frappe.ui.form.on("precios productos", {
    precio_unitario(frm, cdt, cdn) {
        frm.events.recalcular_precios(frm);
    }
});
