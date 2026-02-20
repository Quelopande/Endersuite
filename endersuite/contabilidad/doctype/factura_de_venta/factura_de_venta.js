// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Factura de Venta", {
    refresh(frm) {
        // Botón para obtener notas de venta (siempre visible si no está enviada)
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Obtener Notas de Venta'), function () {
                mostrar_dialogo_seleccion_notas(frm);
            }, __('Acciones'));
        }

        // Muestra UUID si existe
        if (frm.doc.uuid) {
            frm.dashboard.add_indicator(__('Timbrada - UUID: {0}', [frm.doc.uuid]), 'green');
        }

        // Botón de timbrado (solo si está enviada y aún no timbrada)
        if (frm.doc.docstatus === 1 && !frm.doc.uuid) {
            frm.add_custom_button(__('Timbrar en SAT'), function () {
                frappe.confirm(
                    __('Esto enviará la factura al PAC para timbrado. ¿Continuar?'),
                    () => timbrar_en_sat(frm)
                );
            }, __('Acciones'));
        }
    },

    tabla_con_los_productos_o_servicios_add(frm, cdt, cdn) {
        calcular_totales(frm);
    },

    tabla_con_los_productos_o_servicios_remove(frm, cdt, cdn) {
        calcular_totales(frm);
    }
});

function timbrar_en_sat(frm) {
    frappe.call({
        method: 'endersuite.contabilidad.doctype.factura_de_venta.factura_de_venta.timbrar_en_sat',
        args: {
            factura_name: frm.doc.name
        },
        freeze: true,
        freeze_message: __('Timbrando en SAT...'),
        callback: function (r) {
            if (r.message && r.message.success) {
                frm.reload_doc();
                frappe.msgprint({
                    title: __('Timbrado exitoso'),
                    indicator: 'green',
                    message: __('UUID: {0}', [r.message.uuid || frm.doc.uuid || ''])
                });
            }
        }
    });
}

frappe.ui.form.on("Producto Factura de Ventas", {
    cantidad: function (frm, cdt, cdn) {
        calcular_totales(frm);
    },
    valor: function (frm, cdt, cdn) {
        calcular_totales(frm);
    },
    descuento: function (frm, cdt, cdn) {
        calcular_totales(frm);
    }
});

function calcular_totales(frm) {
    let subtotal = 0;
    let impuestos_trasladados = 0;
    let impuestos_retenidos = 0;
    let descuento_total = 0;

    let productos = frm.doc.tabla_con_los_productos_o_servicios || [];

    productos.forEach(function (item) {
        let cantidad = item.cantidad || 0;
        let valor = item.valor || 0;
        let descuento_pct = item.descuento || 0;

        let importe = cantidad * valor;
        let descuento_monto = importe * (descuento_pct / 100);
        let base = importe - descuento_monto;

        subtotal += importe;
        descuento_total += descuento_monto;

        // Aquí deberíamos calcular impuestos si tuviéramos la tasa
        // Por ahora, asumimos que el valor ya incluye impuestos o se calcula en backend
        // Si necesitamos cálculo preciso en frontend, necesitamos traer las tasas de impuesto del producto
    });

    let total = subtotal - descuento_total + impuestos_trasladados - impuestos_retenidos;

    frm.set_value('subtotal', subtotal);
    frm.set_value('descuento_total', descuento_total);
    frm.set_value('total_de_impuestos_trasladados', impuestos_trasladados);
    frm.set_value('total_de_impuestos_retenidos', impuestos_retenidos);
    frm.set_value('total', total);
}

// ============================================================================
// IMPORTACIÓN DE NOTAS DE VENTA
// ============================================================================

function mostrar_dialogo_seleccion_notas(frm) {
    let fields = [
        {
            fieldtype: 'Date',
            fieldname: 'fecha_inicio',
            label: __('Fecha Inicio'),
            default: frappe.datetime.add_days(frappe.datetime.nowdate(), -7)
        },
        {
            fieldtype: 'Date',
            fieldname: 'fecha_fin',
            label: __('Fecha Fin'),
            default: frappe.datetime.nowdate()
        },
        {
            fieldtype: 'Link',
            fieldname: 'cliente',
            label: __('Cliente'),
            options: 'Cliente',
            default: frm.doc.cliente
        },
        {
            fieldtype: 'HTML',
            fieldname: 'lista_notas_html'
        }
    ];

    let d = new frappe.ui.Dialog({
        title: __('Seleccionar Notas de Venta'),
        fields: fields,
        primary_action_label: __('Importar Seleccionadas'),
        primary_action: function () {
            let seleccionadas = [];
            d.$wrapper.find('.nota-checkbox:checked').each(function () {
                seleccionadas.push($(this).val());
            });

            if (seleccionadas.length === 0) {
                frappe.msgprint(__('Por favor selecciona al menos una nota'));
                return;
            }

            importar_notas_seleccionadas(frm, seleccionadas, d);
        }
    });

    // Función para buscar notas
    let buscar_notas = function () {
        let values = d.get_values();
        frappe.call({
            method: 'endersuite.contabilidad.doctype.factura_de_venta.factura_de_venta.get_notas_pendientes',
            args: {
                cliente: values.cliente,
                fecha_inicio: values.fecha_inicio,
                fecha_fin: values.fecha_fin
            },
            callback: function (r) {
                let html = '';

                // Filtrar notas que ya están en la tabla de referencias
                let notas_existentes = (frm.doc.notas_relacionadas || []).map(row => row.nota_de_venta);
                let notas_disponibles = (r.message || []).filter(nota => !notas_existentes.includes(nota.name));

                if (notas_disponibles.length > 0) {
                    html = `
						<table class="table table-bordered table-hover">
							<thead>
								<tr>
									<th width="40px"><input type="checkbox" id="select-all-notas"></th>
									<th>Nota</th>
									<th>Fecha</th>
									<th>Cliente</th>
									<th class="text-right">Total</th>
								</tr>
							</thead>
							<tbody>
					`;

                    notas_disponibles.forEach(nota => {
                        html += `
							<tr>
								<td><input type="checkbox" class="nota-checkbox" value="${nota.name}"></td>
								<td>${nota.name}</td>
								<td>${frappe.datetime.str_to_user(nota.fecha_y_hora_de_venta)}</td>
								<td>${nota.cliente || '-'}</td>
								<td class="text-right">${format_currency(nota.total_final)}</td>
							</tr>
						`;
                    });

                    html += '</tbody></table>';
                } else {
                    html = '<div class="text-muted text-center p-4">' + __('No se encontraron notas pendientes (o ya fueron agregadas)') + '</div>';
                }

                d.fields_dict.lista_notas_html.$wrapper.html(html);

                // Evento select all
                d.$wrapper.find('#select-all-notas').change(function () {
                    d.$wrapper.find('.nota-checkbox').prop('checked', $(this).is(':checked'));
                });
            }
        });
    };

    // Trigger búsqueda inicial y al cambiar filtros
    d.show();
    buscar_notas();

    d.fields_dict.fecha_inicio.$input.on('change', buscar_notas);
    d.fields_dict.fecha_fin.$input.on('change', buscar_notas);
    d.fields_dict.cliente.$input.on('change', buscar_notas);
}

function importar_notas_seleccionadas(frm, notas_list, dialog) {
    frappe.call({
        method: 'endersuite.contabilidad.doctype.factura_de_venta.factura_de_venta.get_notas_details',
        args: {
            notas_list: JSON.stringify(notas_list)
        },
        freeze: true,
        freeze_message: __('Obteniendo datos de notas...'),
        callback: function (r) {
            dialog.hide();
            if (r.message) {
                // Agregar notas a la tabla de referencias
                if (r.message.notas_relacionadas) {
                    r.message.notas_relacionadas.forEach(nota => {
                        let row = frm.add_child('notas_relacionadas');
                        row.nota_de_venta = nota.nota_de_venta;
                        row.fecha = nota.fecha;
                        row.total = nota.total;
                    });
                    frm.refresh_field('notas_relacionadas');
                }

                // Agregar items a la tabla de productos
                if (r.message.items) {
                    r.message.items.forEach(item => {
                        let row = frm.add_child('tabla_con_los_productos_o_servicios');
                        row.producto__servicio = item.producto__servicio;
                        row.cantidad = item.cantidad;
                        row.valor = item.valor;
                        row.descuento = item.descuento;
                        row.descripcion = item.descripcion;
                    });
                    frm.refresh_field('tabla_con_los_productos_o_servicios');
                }

                // Asignar totales calculados desde las notas
                if (r.message.totales) {
                    frm.set_value('subtotal', r.message.totales.subtotal);
                    frm.set_value('descuento_total', r.message.totales.descuento_total);
                    frm.set_value('total_de_impuestos_trasladados', r.message.totales.total_impuestos_trasladados);
                    frm.set_value('total_de_impuestos_retenidos', r.message.totales.total_impuestos_retenidos);
                    frm.set_value('total', r.message.totales.total);
                }

                frappe.show_alert({ message: __('Notas importadas exitosamente'), indicator: 'green' });
            }
        }
    });
}
