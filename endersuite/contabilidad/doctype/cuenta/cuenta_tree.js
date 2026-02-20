frappe.treeview_settings['Cuenta'] = {
    get_tree_nodes: 'endersuite.contabilidad.doctype.cuenta.cuenta.get_children',
    breadcrumb: 'Contabilidad',
    get_tree_root: true,
    show_expand_all: true,
    toolbar: [
        {
            label: __('Nueva Cuenta'),
            condition: function (node) {
                return node.expandable;
            },
            click: function (node) {
                const parent_account = node.data.value;

                frappe.prompt([
                    {
                        fieldname: 'cuenta',
                        fieldtype: 'Data',
                        label: __('Nombre de Cuenta'),
                        reqd: 1
                    },
                    {
                        fieldname: 'is_group',
                        fieldtype: 'Check',
                        label: __('Es Grupo'),
                        default: 0
                    }
                ], function (values) {
                    // Obtener el catálogo y compañía del nodo padre
                    frappe.call({
                        method: 'frappe.client.get',
                        args: {
                            doctype: 'Cuenta',
                            name: parent_account
                        },
                        callback: function (r) {
                            if (r.message) {
                                frappe.call({
                                    method: 'frappe.client.insert',
                                    args: {
                                        doc: {
                                            doctype: 'Cuenta',
                                            cuenta: values.cuenta,
                                            catalogo: r.message.catalogo,
                                            parent_cuenta: parent_account,
                                            is_group: values.is_group ? 1 : 0
                                        }
                                    },
                                    callback: function (r2) {
                                        if (r2.message) {
                                            node.load_children();
                                            frappe.show_alert({
                                                message: __('Cuenta creada'),
                                                indicator: 'green'
                                            });
                                        }
                                    }
                                });
                            }
                        }
                    });
                }, __('Crear Nueva Cuenta'), __('Crear'));
            }
        },
        {
            label: __('Editar'),
            condition: function (node) {
                return true;
            },
            click: function (node) {
                frappe.set_route('Form', 'Cuenta', node.data.value);
            }
        }
    ],
    extend_toolbar: true,
    onload: function (treeview) {
        // Seleccionar catálogo de la compañía por defecto y ponerlo como etiqueta raíz
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Compania',
                fieldname: 'catalogo',
                filters: { name: frappe.defaults.get_default('Company') }
            },
            callback: function (r) {
                let catalogo = r && r.message && r.message.catalogo;
                const applyCatalog = function (name) {
                    if (name) {
                        treeview.args.catalogo = name;
                        treeview.root_label = name;
                        treeview.make_tree();
                    }
                };
                if (!catalogo) {
                    frappe.call({
                        method: 'frappe.client.get_list',
                        args: { doctype: 'Catalogo', fields: ['name'], limit: 1 },
                        callback: function (r2) {
                            const first = (r2.message && r2.message[0] && r2.message[0].name) || null;
                            applyCatalog(first);
                        }
                    });
                } else {
                    applyCatalog(catalogo);
                }
            }
        });
    },
    get_label: function (node) {
        // Mostrar solo el nombre de la cuenta
        return __(node.title || node.label || node.value || 'Sin nombre');
    }
};
