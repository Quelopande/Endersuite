// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cotizacion", {
	refresh: function(frm) {
		// Botón para convertir a Orden de Venta
		if (frm.doc.docstatus === 0 && frm.doc.workflow_state === "Aceptada") {
			frm.add_custom_button(__('Convertir a Orden de Venta'), function() {
				frappe.confirm(
					__('¿Desea convertir esta cotización a Orden de Venta?'),
					function() {
						frm.call('convertir_a_orden_venta').then(r => {
							if (r.message) {
								frappe.set_route('Form', 'Orden de Venta', r.message);
							}
						});
					}
				);
			}, __('Acciones'));
		}

		// Indicador de total
		if (frm.doc.total_final) {
			frm.dashboard.add_indicator(__('Total: {0}', [
				format_currency(frm.doc.total_final, 'MXN')
			]), 'blue');
		}

		// Indicador de estado
		if (frm.doc.workflow_state) {
			let color = get_estado_color(frm.doc.workflow_state);
			frm.dashboard.add_indicator(frm.doc.workflow_state, color);
		}

		// Alerta si está vencida
		if (frm.doc.fecha_vencimiento && frappe.datetime.get_today() > frm.doc.fecha_vencimiento) {
			frm.dashboard.set_headline_alert(__('Cotización Vencida'), 'red');
		}
	},

	cliente: function(frm) {
		if (frm.doc.cliente) {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Cliente',
					filters: { name: frm.doc.cliente },
					fieldname: ['nombre_del_cliente', 'telefono', 'correo_electronico']
				},
				callback: function(r) {
					if (r.message) {
						frappe.show_alert({
							message: __('Cliente: {0}', [r.message.nombre_del_cliente]),
							indicator: 'green'
						});
					}
				}
			});
		}
	},

	descuento_global_porcentaje: function(frm) {
		frm.trigger('recalculate_totals');
	},

	recalculate_totals: function(frm) {
		frm.trigger('validate');
	}
});

// Handlers para child table Producto de Cotizacion
frappe.ui.form.on("Producto de Cotizacion", {
	productos_add: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (!row.cantidad) {
			frappe.model.set_value(cdt, cdn, 'cantidad', 1);
		}
	},

	producto: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.producto) {
			// Obtener información del producto
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Producto',
					filters: { name: row.producto },
					fieldname: ['sku', 'tipo_de_impuesto']
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'sku', r.message.sku);
						frappe.model.set_value(cdt, cdn, 'impuesto', r.message.tipo_de_impuesto);
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
					callback: function(r) {
						if (r.message && r.message.precio) {
							frappe.model.set_value(cdt, cdn, 'precio_unitario', r.message.precio);
						}
					}
				});
			}
		}
	},

	cantidad: function(frm, cdt, cdn) {
		frm.trigger('recalculate_totals');
	},

	precio_unitario: function(frm, cdt, cdn) {
		frm.trigger('recalculate_totals');
	},

	descuento_porcentaje: function(frm, cdt, cdn) {
		frm.trigger('recalculate_totals');
	},

	productos_remove: function(frm) {
		frm.trigger('recalculate_totals');
	}
});

// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

function get_estado_color(estado) {
	const color_map = {
		'Borrador': 'gray',
		'Enviada': 'blue',
		'Aceptada': 'green',
		'Rechazada': 'red',
		'Vencida': 'orange',
		'Convertida': 'purple'
	};
	return color_map[estado] || 'gray';
}

// Formatear vista de lista
frappe.listview_settings['Cotizacion'] = {
	add_fields: ['total_final', 'cliente', 'fecha', 'fecha_vencimiento', 'workflow_state'],

	get_indicator: function(doc) {
		let color = get_estado_color(doc.workflow_state);
		return [__(doc.workflow_state), color, 'workflow_state,=,' + doc.workflow_state];
	},

	formatters: {
		total_final: function(value) {
			return format_currency(value, 'MXN');
		}
	},

	onload: function(listview) {
		// Filtros rápidos
		listview.page.add_inner_button(__('Este Mes'), function() {
			listview.filter_area.add([
				['Cotizacion', 'fecha', 'This Month']
			]);
		});

		listview.page.add_inner_button(__('Pendientes'), function() {
			listview.filter_area.add([
				['Cotizacion', 'workflow_state', 'in', ['Borrador', 'Enviada']]
			]);
		});
	}
};
