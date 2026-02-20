// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Factura de Venta", {
    refresh(frm) {
        // Calcula totales al cargar el formulario
        calcular_totales(frm);

        // Agrega botón de timbrado si está submitted y no tiene UUID
        if (frm.doc.docstatus === 1 && !frm.doc.uuid) {
            frm.add_custom_button(__('Timbrar en SAT'), function () {
                mostrar_modal_timbrado(frm);
            }, __('Acciones'));
        }

        // Muestra UUID si existe
        if (frm.doc.uuid) {
            frm.dashboard.add_indicator(__('Timbrada - UUID: {0}', [frm.doc.uuid]), 'green');
        }

        // Botón para obtener notas de venta (solo si no está enviada)
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Obtener Notas de Venta'), function () {
                mostrar_dialogo_seleccion_notas(frm);
            }, __('Acciones'));
        }
    },

    tabla_con_los_productos_o_servicios_add(frm, cdt, cdn) {
        // Calcula cuando se agrega una fila
        calcular_totales(frm);
    },

    tabla_con_los_productos_o_servicios_remove(frm, cdt, cdn) {
        // Calcula cuando se elimina una fila
        calcular_totales(frm);
    }
});

frappe.ui.form.on("Producto Factura de Ventas", {
    cantidad: function (frm, cdt, cdn) {
        calcular_totales(frm);
    },

    valor: function (frm, cdt, cdn) {
        calcular_totales(frm);
    },

    descuento: function (frm, cdt, cdn) {
        calcular_totales(frm);
    },

    producto__servicio: function (frm, cdt, cdn) {
        // Cuando se selecciona un producto, espera a que se carguen los datos y calcula
        setTimeout(() => {
            calcular_totales(frm);
        }, 300);
    }
});

function calcular_totales(frm) {
    let subtotal = 0;
    let impuestos_trasladados = 0;
    let descuento_total = 0;

    // Recorre todos los productos
    let productos = frm.doc.tabla_con_los_productos_o_servicios || [];

    // Calcula impuestos para cada producto
    let productos_con_impuestos = [];
    productos.forEach(function (item) {
        if (item.producto__servicio) {
            productos_con_impuestos.push(item);
        }
    });

    // Si hay productos, obtiene sus impuestos
    if (productos_con_impuestos.length > 0) {
        let producto_names = productos_con_impuestos.map(p => p.producto__servicio);

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Producto',
                filters: [['name', 'in', producto_names]],
                fields: ['name', 'tipo_de_impuesto']
            },
            async: false,
            callback: function (r) {
                if (r.message) {
                    let productos_map = {};
                    r.message.forEach(p => {
                        productos_map[p.name] = p.tipo_de_impuesto;
                    });

                    // Obtiene las tasas de impuesto
                    let impuesto_names = [...new Set(Object.values(productos_map).filter(Boolean))];

                    if (impuesto_names.length > 0) {
                        frappe.call({
                            method: 'frappe.client.get_list',
                            args: {
                                doctype: 'Impuestos',
                                filters: [['name', 'in', impuesto_names]],
                                fields: ['name', 'porciento_impuesto']
                            },
                            async: false,
                            callback: function (r2) {
                                if (r2.message) {
                                    let impuestos_map = {};
                                    r2.message.forEach(imp => {
                                        impuestos_map[imp.name] = imp.porciento_impuesto;
                                    });

                                    // Primero calcula subtotal e impuestos
                                    productos.forEach(function (item) {
                                        let cantidad = item.cantidad || 0;
                                        let valor = item.valor || 0;

                                        // Subtotal del producto (precio base)
                                        let importe_producto = cantidad * valor;
                                        subtotal += importe_producto;

                                        // Calcula impuestos del producto
                                        if (item.producto__servicio) {
                                            let tipo_impuesto = productos_map[item.producto__servicio];
                                            if (tipo_impuesto && impuestos_map[tipo_impuesto]) {
                                                let tasa = impuestos_map[tipo_impuesto] / 100;
                                                let impuesto_producto = importe_producto * tasa;
                                                impuestos_trasladados += impuesto_producto;
                                            }
                                        }
                                    });

                                    // Ahora calcula descuentos sobre precio con impuestos
                                    productos.forEach(function (item) {
                                        let cantidad = item.cantidad || 0;
                                        let valor = item.valor || 0;
                                        let descuento_pct = item.descuento || 0;

                                        if (descuento_pct > 0 && item.producto__servicio) {
                                            let tipo_impuesto = productos_map[item.producto__servicio];
                                            let precio_con_impuestos = valor;

                                            if (tipo_impuesto && impuestos_map[tipo_impuesto]) {
                                                let tasa = impuestos_map[tipo_impuesto] / 100;
                                                precio_con_impuestos = valor * (1 + tasa);
                                            }

                                            // Calcula descuento sobre precio con impuestos
                                            let importe_con_impuestos = cantidad * precio_con_impuestos;
                                            let descuento_producto = importe_con_impuestos * (descuento_pct / 100);
                                            descuento_total += descuento_producto;
                                        }
                                    });

                                    // Total final: subtotal + impuestos - descuentos
                                    let total = subtotal + impuestos_trasladados - descuento_total;

                                    // Actualiza los campos en el formulario
                                    frm.set_value('subtotal', subtotal);
                                    frm.set_value('descuento_total', descuento_total);
                                    frm.set_value('total_de_impuestos_trasladados', impuestos_trasladados);
                                    frm.set_value('total', total);

                                    // Refresca los campos para mostrar los cambios
                                    frm.refresh_field('subtotal');
                                    frm.refresh_field('descuento_total');
                                    frm.refresh_field('total_de_impuestos_trasladados');
                                    frm.refresh_field('total');
                                }
                            }
                        });
                    } else {
                        // No hay impuestos, calcula solo subtotal y descuentos
                        productos.forEach(function (item) {
                            let cantidad = item.cantidad || 0;
                            let valor = item.valor || 0;
                            let descuento_pct = item.descuento || 0;

                            let importe_producto = cantidad * valor;
                            subtotal += importe_producto;

                            if (descuento_pct > 0) {
                                let descuento_producto = importe_producto * (descuento_pct / 100);
                                descuento_total += descuento_producto;
                            }
                        });

                        let total = subtotal - descuento_total;

                        frm.set_value('subtotal', subtotal);
                        frm.set_value('descuento_total', descuento_total);
                        frm.set_value('total_de_impuestos_trasladados', 0);
                        frm.set_value('total', total);

                        frm.refresh_field('subtotal');
                        frm.refresh_field('descuento_total');
                        frm.refresh_field('total_de_impuestos_trasladados');
                        frm.refresh_field('total');
                    }
                }
            }
        });
    } else {
        // No hay productos, resetea valores
        frm.set_value('subtotal', 0);
        frm.set_value('descuento_total', 0);
        frm.set_value('total_de_impuestos_trasladados', 0);
        frm.set_value('total', 0);

        frm.refresh_field('subtotal');
        frm.refresh_field('descuento_total');
        frm.refresh_field('total_de_impuestos_trasladados');
        frm.refresh_field('total');
    }
}

// Función para mostrar el modal de timbrado con opciones de credenciales
function mostrar_modal_timbrado(frm) {
    // Primero verifica si hay credenciales PAC configuradas
    frappe.call({
        method: 'endersuite.ventas.doctype.factura_de_venta.factura_de_venta.check_pac_credentials',
        callback: function (r) {
            if (r.message && r.message.configurado) {
                // Hay credenciales configuradas, muestra opciones
                mostrar_dialogo_opciones_credenciales(frm);
            } else {
                // No hay credenciales, muestra diálogo para subir archivos
                mostrar_dialogo_subir_credenciales(frm, true);
            }
        }
    });
}

// Diálogo cuando hay credenciales configuradas
function mostrar_dialogo_opciones_credenciales(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Opciones de Timbrado'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'mensaje',
                options: '<p>' + __('Ya tienes credenciales PAC configuradas. ¿Cómo deseas timbrar esta factura?') + '</p>'
            },
            {
                fieldtype: 'Button',
                fieldname: 'usar_configuradas',
                label: __('Usar Credenciales Configuradas'),
                click: function () {
                    d.hide();
                    confirmar_y_timbrar(frm, null, null, false);
                }
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Button',
                fieldname: 'usar_nuevas',
                label: __('Usar Otras Credenciales'),
                click: function () {
                    d.hide();
                    mostrar_dialogo_subir_credenciales(frm, false);
                }
            }
        ]
    });
    d.show();
}

// Diálogo para subir archivos de credenciales
function mostrar_dialogo_subir_credenciales(frm, es_primera_vez) {
    let d = new frappe.ui.Dialog({
        title: __('Cargar Credenciales PAC'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'instrucciones',
                options: '<p>' + __('Sube los archivos de tu certificado (.cer) y llave privada (.key) del SAT para timbrar.') + '</p>'
            },
            {
                fieldtype: 'Attach',
                fieldname: 'archivo_cer',
                label: __('Archivo de Certificado (.cer)'),
                reqd: 1
            },
            {
                fieldtype: 'Attach',
                fieldname: 'archivo_key',
                label: __('Archivo de Llave Privada (.key)'),
                reqd: 1
            },
            {
                fieldtype: 'Password',
                fieldname: 'password_key',
                label: __('Contraseña de la Llave Privada'),
                reqd: 1
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'Check',
                fieldname: 'guardar_credenciales',
                label: __('Guardar estas credenciales para futuras facturas'),
                default: es_primera_vez ? 1 : 0
            }
        ],
        primary_action_label: __('Timbrar Factura'),
        primary_action: function (values) {
            if (!values.archivo_cer || !values.archivo_key || !values.password_key) {
                frappe.msgprint(__('Por favor completa todos los campos requeridos'));
                return;
            }

            d.hide();
            confirmar_y_timbrar(
                frm,
                values.archivo_cer,
                values.archivo_key,
                values.password_key,
                values.guardar_credenciales
            );
        }
    });
    d.show();
}

// Confirma el timbrado y ejecuta
function confirmar_y_timbrar(frm, archivo_cer, archivo_key, password_key, guardar) {
    frappe.confirm(
        __('¿Está seguro que desea timbrar esta factura en el SAT?') + '<br><br>' +
        '<strong style="color: red;">' + __('Esta acción generará un CFDI fiscal y no se puede deshacer.') + '</strong>',
        function () {
            // Usuario confirmó, procede con el timbrado
            let args = {
                factura_name: frm.doc.name
            };

            // Si hay credenciales personalizadas, las agrega
            if (archivo_cer && archivo_key) {
                args.archivo_cer = archivo_cer;
                args.archivo_key = archivo_key;
                args.password_key = password_key;
                args.guardar_credenciales = guardar ? 1 : 0;
            }

            frappe.call({
                method: 'endersuite.ventas.doctype.factura_de_venta.factura_de_venta.timbrar_con_credenciales',
                args: args,
                freeze: true,
                freeze_message: __('Timbrando factura en el SAT...'),
                callback: function (r) {
                    manejar_respuesta_timbrado(frm, r);
                }
            });
        },
        function () {
            // Usuario canceló
            frappe.show_alert({
                message: __('Timbrado cancelado'),
                indicator: 'orange'
            }, 3);
        }
    );
}

// Maneja la respuesta del servidor después del timbrado
function manejar_respuesta_timbrado(frm, r) {
    if (r.message && r.message.success) {
        // Recargar documento primero para obtener datos actualizados
        frm.reload_doc().then(() => {
            mostrar_dialogo_exito_timbrado(frm, r.message.uuid);
        });
    } else {
        // Maneja diferentes tipos de errores
        let error_msg = r.message ? r.message.error : __('Error desconocido al timbrar la factura');
        let error_type = r.message ? r.message.error_type : 'unknown';

        mostrar_error_timbrado(error_msg, error_type, frm);
    }
}

// Muestra diálogo de éxito con información completa del timbrado
function mostrar_dialogo_exito_timbrado(frm, uuid) {
    // Reproducir sonido de éxito
    frappe.utils.play_sound("success");

    let html_contenido = `
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 48px; color: #28a745; margin-bottom: 15px;">
                <i class="fa fa-check-circle"></i>
            </div>
            <h3 style="color: #28a745; margin-bottom: 25px;">¡Factura Timbrada Exitosamente!</h3>
            
            <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: left;">
                <div style="margin-bottom: 15px;">
                    <strong style="color: #495057;">Folio Fiscal (UUID):</strong>
                    <div style="font-family: monospace; font-size: 14px; color: #007bff; margin-top: 5px;">
                        ${uuid || frm.doc.uuid}
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong style="color: #495057;">RFC Emisor:</strong>
                    <div style="font-size: 14px; margin-top: 5px;">
                        ${frm.doc.rfc}
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong style="color: #495057;">RFC Receptor:</strong>
                    <div style="font-size: 14px; margin-top: 5px;">
                        ${frm.doc.rfc_del_receptor}
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong style="color: #495057;">Fecha de Timbrado:</strong>
                    <div style="font-size: 14px; margin-top: 5px;">
                        ${frm.doc.fecha_de_timbrado || frappe.datetime.nowdate()}
                    </div>
                </div>
                
                <div style="margin-bottom: 0;">
                    <strong style="color: #495057;">Estado:</strong>
                    <div style="font-size: 14px; color: #28a745; margin-top: 5px;">
                        <i class="fa fa-check"></i> Solicitud procesada con éxito
                    </div>
                </div>
            </div>
            
            <div style="background-color: #e7f3ff; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0; text-align: left;">
                <strong style="color: #004085;">
                    <i class="fa fa-info-circle"></i> Verificación en el SAT
                </strong>
                <p style="margin: 10px 0 5px 0; color: #004085;">
                    Puedes verificar tu factura en el portal del SAT:
                </p>
                <a href="https://verificacfdi.facturaelectronica.sat.gob.mx/" 
                   target="_blank" 
                   style="color: #007bff; text-decoration: none; font-weight: 500;">
                    <i class="fa fa-external-link"></i> verificacfdi.facturaelectronica.sat.gob.mx
                </a>
            </div>
            
            <div style="margin-top: 25px;">
                <button class="btn btn-primary btn-sm btn-descargar-xml" style="margin-right: 10px;">
                    <i class="fa fa-download"></i> Descargar XML
                </button>
                <button class="btn btn-success btn-sm btn-descargar-pdf">
                    <i class="fa fa-file-pdf-o"></i> Descargar PDF
                </button>
            </div>
        </div>
    `;

    let d = new frappe.ui.Dialog({
        title: __('Timbrado Exitoso'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'contenido',
                options: html_contenido
            }
        ],
        primary_action_label: __('Cerrar'),
        primary_action: function () {
            d.hide();
        }
    });

    d.show();

    // Hacer el diálogo más ancho
    d.$wrapper.find('.modal-dialog').css('max-width', '600px');

    // Agregar event listeners a los botones
    d.$wrapper.find('.btn-descargar-xml').on('click', function () {
        descargar_xml_timbrado(frm);
    });

    d.$wrapper.find('.btn-descargar-pdf').on('click', function () {
        descargar_pdf_timbrado(frm);
    });
}

// Descarga el XML timbrado
function descargar_xml_timbrado(frm) {
    frappe.call({
        method: 'endersuite.ventas.doctype.factura_de_venta.factura_de_venta.descargar_xml',
        args: {
            factura_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                // Crear blob y descargar
                let blob = new Blob([r.message.xml], { type: 'application/xml' });
                let url = window.URL.createObjectURL(blob);
                let a = document.createElement('a');
                a.href = url;
                a.download = r.message.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                frappe.show_alert({
                    message: __('XML descargado exitosamente'),
                    indicator: 'green'
                }, 3);
            }
        },
        error: function (r) {
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('No se pudo descargar el XML')
            });
        }
    });
}

// Descarga el PDF timbrado
function descargar_pdf_timbrado(frm) {
    frappe.call({
        method: 'endersuite.ventas.doctype.factura_de_venta.factura_de_venta.descargar_pdf',
        args: {
            factura_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                // Decodificar base64 y descargar
                let byteCharacters = atob(r.message.pdf_base64);
                let byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                let byteArray = new Uint8Array(byteNumbers);
                let blob = new Blob([byteArray], { type: 'application/pdf' });
                let url = window.URL.createObjectURL(blob);
                let a = document.createElement('a');
                a.href = url;
                a.download = r.message.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                frappe.show_alert({
                    message: __('PDF descargado exitosamente'),
                    indicator: 'green'
                }, 3);
            }
        },
        error: function (r) {
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('No se pudo descargar el PDF')
            });
        }
    });
}// Muestra errores de timbrado con diálogos específicos
function mostrar_error_timbrado(mensaje, tipo_error, frm) {
    let opciones_dialogo = {
        title: __('Error al Timbrar'),
        indicator: 'red'
    };

    // Personaliza el mensaje según el tipo de error
    if (tipo_error === 'credentials') {
        opciones_dialogo.message = '<p><strong>' + __('Error de Credenciales') + '</strong></p>' +
            '<p>' + mensaje + '</p>' +
            '<p>' + __('¿Deseas intentar con otras credenciales?') + '</p>';

        opciones_dialogo.primary_action_label = __('Reintentar con Otras Credenciales');
        opciones_dialogo.primary_action = function () {
            mostrar_dialogo_subir_credenciales(frm, false);
        };
    } else if (tipo_error === 'pac') {
        opciones_dialogo.message = '<p><strong>' + __('Error del Proveedor PAC') + '</strong></p>' +
            '<p>' + mensaje + '</p>' +
            '<p>' + __('Verifica tu configuración del PAC o contacta a tu proveedor.') + '</p>';
    } else if (tipo_error === 'validation') {
        opciones_dialogo.message = '<p><strong>' + __('Error de Validación') + '</strong></p>' +
            '<p>' + mensaje + '</p>' +
            '<p>' + __('Verifica los datos de la factura antes de intentar nuevamente.') + '</p>';
    } else {
        opciones_dialogo.message = '<p><strong>' + __('Error Inesperado') + '</strong></p>' +
            '<p>' + mensaje + '</p>';
    }

    frappe.msgprint(opciones_dialogo);
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
            method: 'endersuite.ventas.doctype.factura_de_venta.factura_de_venta.get_notas_pendientes',
            args: {
                cliente: values.cliente,
                fecha_inicio: values.fecha_inicio,
                fecha_fin: values.fecha_fin
            },
            callback: function (r) {
                let html = '';
                if (r.message && r.message.length > 0) {
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

                    r.message.forEach(nota => {
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
                    html = '<div class="text-muted text-center p-4">' + __('No se encontraron notas pendientes') + '</div>';
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
        method: 'endersuite.ventas.doctype.factura_de_venta.factura_de_venta.importar_notas',
        args: {
            factura_name: frm.doc.name,
            notas_list: JSON.stringify(notas_list)
        },
        freeze: true,
        freeze_message: __('Importando notas...'),
        callback: function (r) {
            dialog.hide();
            if (r.message) {
                frappe.show_alert({ message: __('Notas importadas exitosamente'), indicator: 'green' });
                frm.reload_doc();
            }
        }
    });
}
