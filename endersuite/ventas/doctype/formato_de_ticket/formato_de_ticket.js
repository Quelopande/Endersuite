// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Formato de Ticket", {
    refresh(frm) {
        if (!frm.is_new()) {
            // Botón para vista previa
            frm.add_custom_button(__('Vista Previa'), function () {
                // Obtener una nota de venta de ejemplo
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Nota de Venta',
                        filters: {
                            docstatus: 1
                        },
                        fields: ['name'],
                        limit: 1,
                        order_by: 'creation desc'
                    },
                    callback: function (r) {
                        if (r.message && r.message.length > 0) {
                            // Generar vista previa
                            frappe.call({
                                method: 'endersuite.ventas.doctype.formato_de_ticket.formato_de_ticket.generar_ticket_html',
                                args: {
                                    nota_venta_name: r.message[0].name,
                                    formato_name: frm.doc.name
                                },
                                callback: function (r) {
                                    if (r.message) {
                                        const previewWindow = window.open('', '_blank');
                                        previewWindow.document.write(r.message);
                                        previewWindow.document.close();
                                    }
                                }
                            });
                        } else {
                            frappe.msgprint(__('No hay notas de venta para generar vista previa'));
                        }
                    }
                });
            }, __('Acciones'));
        }
    }
});
