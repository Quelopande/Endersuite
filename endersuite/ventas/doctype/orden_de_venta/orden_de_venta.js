// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Orden de Venta", {
	refresh: function(frm) {
		// Botón para crear Nota de Venta
		if (frm.doc.docstatus === 1 && frm.doc.estado === "Confirmada") {
			frm.add_custom_button(__('Crear Nota de Venta'), function() {
				frappe.confirm(
					__('¿Desea crear una Nota de Venta desde esta orden?'),
					function() {
						frm.call('crear_nota_de_venta').then(r => {
							if (r.message) {
								frappe.set_route('Form', 'Nota de Venta', r.message);
							}
						});
					}
				);
			}, __('Acciones'));
		}

		// Botones para cambiar estado
		if (frm.doc.docstatus === 1) {
			if (frm.doc.estado === "Confirmada") {
				frm.add_custom_button(__('Marcar En Entrega'), function() {
					frm.call({
						method: 'cambiar_estado',
						args: { nuevo_estado: 'En Entrega' },
						callback: () => frm.reload_doc()
					});
				}, __('Estado'));
			}

			if (frm.doc.estado === "En Entrega") {
				frm.add_custom_button(__('Cerrar Orden'), function() {
					frm.call({
						method: 'cambiar_estado',
						args: { nuevo_estado: 'Cerrada' },
						callback: () => frm.reload_doc()
					});
				}, __('Estado'));
			}

			if (['Confirmada', 'En Entrega'].includes(frm.doc.estado)) {
				frm.add_custom_button(__('Cancelar Orden'), function() {
					frappe.confirm(
						__('¿Está seguro de cancelar esta orden?'),
						function() {
							frm.call({
								method: 'cambiar_estado',
								args: { nuevo_estado: 'Cancelada' },
								callback: () => frm.reload_doc()
							});
						}
					);
				}, __('Estado'));
			}
		}

		// Indicador de total
		if (frm.doc.total_final) {
			frm.dashboard.add_indicator(__('Total: {0}', [
				format_currency(frm.doc.total_final, 'MXN')
			]), 'blue');
		}

		// Indicador de estado
		if (frm.doc.estado) {
			let color = get_estado_color(frm.doc.estado);
			frm.dashboard.add_indicator(frm.doc.estado, color);
		}

		// Alerta si la fecha de entrega pasó
		if (frm.doc.fecha_entrega_estimada && frappe.datetime.get_today() > frm.doc.fecha_entrega_estimada) {
			if (frm.doc.estado !== 'Cerrada' && frm.doc.estado !== 'Cancelada') {
				frm.dashboard.set_headline_alert(__('Fecha de Entrega Vencida'), 'red');
			}
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

// Handlers para child table Producto de Orden de Venta
frappe.ui.form.on("Producto de Orden de Venta", {
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
					fieldname: ['sku', 'tipo_de_impuesto', 'mantener_stock', 'cantidad_disponible']
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'sku', r.message.sku);
						frappe.model.set_value(cdt, cdn, 'impuesto', r.message.tipo_de_impuesto);

						// Mostrar alerta si hay poco stock
						if (r.message.mantener_stock && r.message.cantidad_disponible < row.cantidad) {
							frappe.msgprint({
								title: __('Stock Limitado'),
								message: __('El producto {0} tiene stock limitado. Disponible: {1}',
									[row.producto, r.message.cantidad_disponible]),
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
		'Confirmada': 'blue',
		'En Entrega': 'orange',
		'Cerrada': 'green',
		'Cancelada': 'red'
	};
	return color_map[estado] || 'gray';
}

// Formatear vista de lista
frappe.listview_settings['Orden de Venta'] = {
	add_fields: ['total_final', 'cliente', 'fecha', 'fecha_entrega_estimada', 'estado'],

	get_indicator: function(doc) {
		let color = get_estado_color(doc.estado);
		return [__(doc.estado), color, 'estado,=,' + doc.estado];
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
				['Orden de Venta', 'fecha', 'This Month']
			]);
		});

		listview.page.add_inner_button(__('Pendientes'), function() {
			listview.filter_area.add([
				['Orden de Venta', 'estado', 'in', ['Borrador', 'Confirmada', 'En Entrega']]
			]);
		});

		listview.page.add_inner_button(__('Vencidas'), function() {
			listview.filter_area.add([
				['Orden de Venta', 'fecha_entrega_estimada', '<', frappe.datetime.get_today()],
				['Orden de Venta', 'estado', 'not in', ['Cerrada', 'Cancelada']]
			]);
		});
	}
};
