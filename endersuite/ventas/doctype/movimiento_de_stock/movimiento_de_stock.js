// Copyright (c) 2024, EnderSuite and contributors
// For license information, please see license.txt

frappe.ui.form.on('Movimiento de Stock', {
    refresh: function (frm) {
        // Indicadores de color según estado
        if (frm.doc.estado === "Completado") {
            frm.dashboard.set_headline_alert('Movimiento Completado', 'green');
        } else if (frm.doc.estado === "Cancelado") {
            frm.dashboard.set_headline_alert('Movimiento Cancelado', 'red');
        }

        // Filtrar almacenes activos
        frm.set_query('almacen', function () {
            return {
                filters: {
                    almacen_activo: 1
                }
            };
        });
    },

    tipo_movimiento: function (frm) {
        // Limpiar detalles al cambiar tipo
        if (frm.doc.detalles && frm.doc.detalles.length > 0) {
            frappe.confirm(
                '¿Desea limpiar los productos agregados al cambiar el tipo de movimiento?',
                function () {
                    frm.clear_table('detalles');
                    frm.refresh_field('detalles');
                }
            );
        }
    }
});

frappe.ui.form.on('Detalle Movimiento Stock', {
    producto: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.producto) {
            // Obtener información del producto
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Producto',
                    filters: { name: row.producto },
                    fieldname: ['cantidad_disponible', 'requiere_lote', 'requiere_serie']
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'stock_actual', r.message.cantidad_disponible);

                        // Mostrar advertencia si el stock es bajo
                        if (frm.doc.tipo_movimiento === 'Salida' && r.message.cantidad_disponible <= 0) {
                            frappe.msgprint({
                                title: 'Stock Insuficiente',
                                indicator: 'red',
                                message: `El producto ${row.producto} no tiene stock disponible`
                            });
                        }
                    }
                }
            });
        }
    },

    cantidad: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // Validar cantidad positiva
        if (row.cantidad <= 0) {
            frappe.model.set_value(cdt, cdn, 'cantidad', 1);
            frappe.msgprint('La cantidad debe ser mayor a cero');
        }

        // Advertir si la cantidad excede el stock disponible
        if (frm.doc.tipo_movimiento === 'Salida' && row.stock_actual) {
            if (row.cantidad > row.stock_actual) {
                frappe.msgprint({
                    title: 'Advertencia',
                    indicator: 'orange',
                    message: `La cantidad solicitada (${row.cantidad}) excede el stock disponible (${row.stock_actual})`
                });
            }
        }
    }
});
