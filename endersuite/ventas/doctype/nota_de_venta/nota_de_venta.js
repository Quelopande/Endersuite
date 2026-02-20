// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nota de Venta", {
    setup(frm) {
        // Limpiar valores al crear nuevo documento
        if (frm.is_new()) {
            frm.doc.tabla_de_productos = [];
            frm.doc.metodos_pago_nota = [];
            frm.doc.subtotal = 0;
            frm.doc.total_impuestos = 0;
            frm.doc.total_final = 0;
            frm.doc.total_pagado = 0;
            frm.doc.cambio = 0;
            frm.doc.descuento_global_porcentaje = 0;
            frm.doc.descuento_global_monto = 0;
            frm.doc.base_imponible_total = 0;
        }
    },

    onload(frm) {
        // Expandir todas las secciones al cargar
        setTimeout(() => {
            frm.layout.sections.forEach(section => {
                if (section.collapse_link) {
                    section.collapse(false);
                }
            });
        }, 100);

        // Si es nuevo, asegurarse de que esté limpio
        if (frm.is_new()) {
            frm.clear_table('tabla_de_productos');
            frm.clear_table('metodos_pago_nota');
            frm.refresh_fields();
        }
    },

    refresh(frm) {
        // Verificar campos requeridos para mostrar/ocultar sección de productos
        frm.trigger('check_required_fields');

        try {
            // Expandir todas las secciones
            setTimeout(() => {
                frm.layout.sections.forEach(section => {
                    if (section.collapse_link) {
                        section.collapse(false);
                    }
                });
            }, 100);

            // Agregar indicadores visuales
            if (frm.doc.docstatus === 1) {
                frm.dashboard.set_headline_alert('Venta Completada', 'green');
            }

            // Botón de impresión rápida
            if (frm.doc.docstatus === 1) {
                frm.add_custom_button(__('Imprimir Ticket'), function () {
                    frappe.call({
                        method: 'endersuite.ventas.services.pos_service.generate_ticket_html',
                        args: {
                            nota_venta_name: frm.doc.name
                        },
                        callback: function (r) {
                            if (r.message) {
                                const printWindow = window.open('', '_blank');
                                printWindow.document.write(r.message);
                                printWindow.document.close();
                                printWindow.focus();
                                printWindow.print();

                                // Marcar como impreso
                                if (frm.doc.estado_impresion === 'Pendiente') {
                                    frm.call('marcar_como_impreso');
                                }
                            }
                        }
                    });
                }, __('Acciones'));

                // Botón para ver sesión POS
                if (frm.doc.sesion_pos) {
                    frm.add_custom_button(__('Ver Sesión POS'), function () {
                        frappe.set_route('Form', 'Sesion POS', frm.doc.sesion_pos);
                    }, __('Ver'));
                }
            }

            // Validar totales y mostrar indicadores
            validate_totals(frm);

            // Resaltar total
            if (frm.doc.total_final) {
                frm.dashboard.add_indicator(__('Total: {0}', [
                    format_currency(frm.doc.total_final, 'MXN')
                ]), 'blue');
            }

            // Mostrar cambio si existe
            if (frm.doc.cambio && frm.doc.cambio > 0) {
                frm.dashboard.add_indicator(__('Cambio: {0}', [
                    format_currency(frm.doc.cambio, 'MXN')
                ]), 'orange');
            }
        } catch (e) {
            console.error('Error en refresh de Nota de Venta:', e);
            frappe.msgprint('Error JS en Nota de Venta: ' + e.message);
        }
    },

    cliente: function (frm) {
        // Cargar información del cliente si existe
        if (frm.doc.cliente) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Cliente',
                    filters: { name: frm.doc.cliente },
                    fieldname: ['nombre_completo', 'teléfono_móvil', 'email']
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Cliente: {0}', [r.message.nombre_completo]),
                            indicator: 'green'
                        });
                    }
                }
            });
        }

        // Mostrar sección de productos si todos los campos requeridos están llenos
        frm.trigger('check_required_fields');
    },

    almacen: function (frm) {
        frm.trigger('check_required_fields');
    },

    lista_de_precios: function (frm) {
        frm.trigger('check_required_fields');
    },

    check_required_fields: function (frm) {
        // Mostrar u ocultar la sección de productos según si los campos requeridos están llenos
        if (frm.is_new()) {
            const has_required = frm.doc.cliente && frm.doc.almacen && frm.doc.lista_de_precios;
            frm.set_df_property('section_break_productos', 'hidden', has_required ? 0 : 1);

            if (!has_required) {
                frappe.show_alert({
                    message: __('Completa Cliente, Almacén y Lista de Precios para agregar productos'),
                    indicator: 'orange'
                }, 3);
            }
        }
    },

    descuento_global_porcentaje: function (frm) {
        // Recalcular cuando cambia el descuento global
        frm.trigger('recalculate_totals');
    },

    recalculate_totals: function (frm) {
        // Disparar recálculo en el servidor sin guardar
        if (frm.doc.__islocal || frm.is_dirty()) {
            frm.script_manager.trigger('validate')
                .then(() => {
                    frm.refresh_fields();
                });
        }
    }
});

// Handlers para child table Tabla de Productos
frappe.ui.form.on("Tabla de Productos", {
    tabla_de_productos_add: function (frm, cdt, cdn) {
        // Inicializar valores por defecto
        let row = locals[cdt][cdn];
        if (!row.cantidad) {
            frappe.model.set_value(cdt, cdn, 'cantidad', 1);
        }
        if (!row.descuento_porcentaje) {
            frappe.model.set_value(cdt, cdn, 'descuento_porcentaje', 0);
        }
    },

    producto: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.producto) {
            // Obtener información del producto
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Producto',
                    filters: { name: row.producto },
                    fieldname: ['sku', 'tipo_de_impuesto', 'mantener_stock', 'cantidad_disponible']
                },
                callback: function (r) {
                    if (r.message) {
                        console.log('Producto data:', r.message);

                        // Establecer SKU
                        frappe.model.set_value(cdt, cdn, 'sku', r.message.sku);

                        // Establecer impuesto - IMPORTANTE: debe ir antes del precio
                        if (r.message.tipo_de_impuesto) {
                            frappe.model.set_value(cdt, cdn, 'impuesto', r.message.tipo_de_impuesto);
                            console.log('Impuesto establecido:', r.message.tipo_de_impuesto);
                        } else {
                            console.warn('Producto sin tipo_de_impuesto:', row.producto);
                        }

                        // Mostrar alerta si no hay stock
                        if (r.message.mantener_stock && r.message.cantidad_disponible <= 0) {
                            frappe.msgprint({
                                title: __('Sin Stock'),
                                message: __('El producto {0} no tiene stock disponible', [row.producto]),
                                indicator: 'orange'
                            });
                        }
                    }
                }
            });

            // Obtener precio desde lista de precios
            if (frm.doc.lista_de_precios) {
                frappe.call({
                    method: 'endersuite.ventas.services.pos_service.get_product_price',
                    args: {
                        producto: row.producto,
                        lista_de_precios: frm.doc.lista_de_precios
                    },
                    callback: function (r) {
                        if (r.message && r.message.precio) {
                            frappe.model.set_value(cdt, cdn, 'precio_unitario', r.message.precio).then(() => {
                                // Forzar recálculo después de establecer precio
                                setTimeout(() => {
                                    frm.trigger('recalculate_totals');
                                }, 100);
                            });
                        }
                    }
                });
            }
        }
    },

    cantidad: function (frm, cdt, cdn) {
        calculate_line_total(frm, cdt, cdn);
    },

    precio_unitario: function (frm, cdt, cdn) {
        calculate_line_total(frm, cdt, cdn);
    },

    descuento_porcentaje: function (frm, cdt, cdn) {
        calculate_line_total(frm, cdt, cdn);
    },

    impuesto: function (frm, cdt, cdn) {
        // Recalcular cuando cambia el impuesto
        calculate_line_total(frm, cdt, cdn);
    },

    tabla_de_productos_remove: function (frm) {
        // Recalcular totales cuando se elimina un item
        frm.trigger('recalculate_totals');
    }
});

// Handlers para child table Metodos de Pago Nota
frappe.ui.form.on("Metodos de Pago Nota", {
    metodos_pago_nota_add: function (frm, cdt, cdn) {
        // Auto-completar con monto restante
        let row = locals[cdt][cdn];
        let remaining = (frm.doc.total_final || 0) - get_total_paid(frm);
        if (remaining > 0) {
            frappe.model.set_value(cdt, cdn, 'monto', remaining);
        }
    },

    metodo: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.metodo) {
            // Validar que no esté duplicado
            let duplicates = frm.doc.metodos_pago_nota.filter(d =>
                d.metodo === row.metodo && d.name !== row.name
            );
            if (duplicates.length > 0) {
                frappe.msgprint(__("El método de pago {0} ya está agregado", [row.metodo]));
                frappe.model.set_value(cdt, cdn, "metodo", "");
            }
        }
    },

    monto: function (frm, cdt, cdn) {
        // Validar y actualizar indicadores
        validate_totals(frm);
    },

    metodos_pago_nota_remove: function (frm) {
        // Revalidar cuando se elimina un método de pago
        validate_totals(frm);
    }
});

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

function calculate_line_total(frm, cdt, cdn) {
    /**
     * Calcular totales de una línea de producto
     * No realiza cálculos reales, solo dispara validación en servidor
     */
    let row = locals[cdt][cdn];

    if (row.cantidad && row.precio_unitario) {
        // Disparar validación en el servidor para calcular correctamente
        frm.trigger('recalculate_totals');
    }
}

function get_total_paid(frm) {
    /**
     * Obtener total pagado de todos los métodos de pago
     */
    let total = 0;
    if (frm.doc.metodos_pago_nota) {
        frm.doc.metodos_pago_nota.forEach(function (row) {
            total += flt(row.monto);
        });
    }
    return total;
}

function validate_totals(frm) {
    /**
     * Validar totales y mostrar indicadores visuales
     */
    if (!frm.doc.total_final || frm.doc.docstatus === 1) {
        return;
    }

    let total_pagado = get_total_paid(frm);

    // Limpiar indicadores previos
    frm.dashboard.clear_headline();

    if (total_pagado < frm.doc.total_final) {
        let falta = frm.doc.total_final - total_pagado;
        frm.dashboard.set_headline_alert(
            __('Pago Incompleto - Falta: {0}', [format_currency(falta, 'MXN')]),
            'orange'
        );
    } else if (total_pagado > frm.doc.total_final) {
        let cambio = total_pagado - frm.doc.total_final;
        frm.dashboard.set_headline_alert(
            __('Cambio: {0}', [format_currency(cambio, 'MXN')]),
            'green'
        );
    } else {
        frm.dashboard.set_headline_alert(__('Pago Completo'), 'green');
    }
}

frappe.ui.form.on("Metodos de Pago Nota", {
    metodo: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.metodo) {
            let duplicates = frm.doc.metodos_pago_nota.filter(d => d.metodo === row.metodo && d.name !== row.name);
            if (duplicates.length > 0) {
                frappe.msgprint(__("El método de pago {0} ya está agregado", [row.metodo]));
                frappe.model.set_value(cdt, cdn, "metodo", "");
            }
        }
    }
});

// Formatear la vista de lista
frappe.listview_settings['Nota de Venta'] = {
    add_fields: ['total_final', 'cliente', 'sesion_pos', 'fecha_y_hora_de_venta', 'estado_impresion'],

    get_indicator: function (doc) {
        if (doc.docstatus === 0) {
            return [__('Borrador'), 'gray', 'docstatus,=,0'];
        } else if (doc.docstatus === 1) {
            if (doc.estado_impresion === 'Impreso') {
                return [__('Completada'), 'green', 'docstatus,=,1|estado_impresion,=,Impreso'];
            } else {
                return [__('Pendiente Impresión'), 'orange', 'docstatus,=,1|estado_impresion,=,Pendiente'];
            }
        } else if (doc.docstatus === 2) {
            return [__('Cancelada'), 'red', 'docstatus,=,2'];
        }
    },

    formatters: {
        total_final: function (value) {
            return format_currency(value, 'MXN');
        }
    },

    onload: function (listview) {
        // Filtros rápidos
        listview.page.add_inner_button(__('Hoy'), function () {
            listview.filter_area.add([
                ['Nota de Venta', 'fecha_y_hora_de_venta', 'Today']
            ]);
        });

        listview.page.add_inner_button(__('Esta Semana'), function () {
            listview.filter_area.add([
                ['Nota de Venta', 'fecha_y_hora_de_venta', 'This Week']
            ]);
        });

        listview.page.add_inner_button(__('Este Mes'), function () {
            listview.filter_area.add([
                ['Nota de Venta', 'fecha_y_hora_de_venta', 'This Month']
            ]);
        });
    }
};
