// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Configuracion PAC', {
    refresh: function (frm) {
        // Oculta completamente los campos de credenciales
        frm.set_df_property('cuenta', 'hidden', 1);
        frm.set_df_property('api_key', 'hidden', 1);

        // Agrega mensaje informativo
        if (!frm.is_new()) {
            frm.dashboard.add_comment(__('Las credenciales del PAC están pre-configuradas y encriptadas por seguridad.'), 'blue', true);
        }

        // Botón de prueba de conexión
        frm.add_custom_button(__('Probar Conexión'), function () {
            frappe.call({
                method: 'endersuite.ventas.doctype.configuracion_pac.configuracion_pac.test_connection',
                callback: function (r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint({
                            title: __('Conexión Exitosa'),
                            indicator: 'green',
                            message: r.message.message || __('Conexión exitosa con el PAC')
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Error de Conexión'),
                            indicator: 'red',
                            message: r.message ? r.message.message : __('No se pudo conectar con el PAC')
                        });
                    }
                }
            });
        });
    }
});
