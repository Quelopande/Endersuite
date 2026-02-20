// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.pages['pos'].on_page_load = function (wrapper) {
	let page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('POS - Punto de Venta'),
		single_column: true
	});

	// Guardar referencia a la página
	wrapper.page = page;
};

frappe.pages['pos'].on_page_show = function (wrapper) {
	// Inicializar o reinicializar la aplicación POS cada vez que se muestra
	if (!frappe.pos_app || frappe.pos_app.page !== wrapper.page) {
		frappe.pos_app = new POSApp(wrapper.page);
	} else {
		// Refrescar sesión si ya existe la app
		frappe.pos_app.check_session();
	}
};

class POSApp {
	constructor(page) {
		this.page = page;
		this.page_content = $(this.page.body);
		this.sesion = null;
		this.etapa = 'apertura'; // apertura | productos | cierre

		this.init();
	}

	async init() {
		// Verificar si hay sesión activa
		await this.check_session();
	}

	async check_session() {
		try {
			const r = await frappe.call({
				method: 'endersuite.ventas.services.pos_service.get_active_session'
			});

			if (r.message) {
				// Validar que la sesión tenga datos completos
				if (!r.message.almacen || !r.message.lista_de_precios) {
					console.warn('Sesión incompleta encontrada:', r.message);
					frappe.msgprint({
						title: __('Sesión Incompleta'),
						message: __('La sesión activa no tiene configuración completa. Por favor, ciérrala y abre una nueva.'),
						indicator: 'orange'
					});
					// Mostrar pantalla de cierre para que pueda cerrar la sesión corrupta
					this.sesion = r.message;
					this.show_cierre();
					return;
				}

				this.sesion = r.message;
				this.load_state();
				this.show_productos();
			} else {
				this.show_apertura();
			}
		} catch (error) {
			console.error('Error checking session:', error);
			frappe.msgprint(__('Error al verificar la sesión POS'));
			this.show_apertura();
		}
	}

	show_apertura() {
		this.page_content.empty();
		this.etapa = 'apertura';

		// Limpiar acciones del header
		this.page.clear_actions();
		this.page.clear_indicator();

		// Crear componente de apertura (destruir el anterior si existe)
		if (this.apertura && this.apertura.dialog) {
			this.apertura.dialog.hide();
			this.apertura.dialog = null;
		}
		this.apertura = new POSApertura(this);
	}

	show_productos() {
		this.page_content.empty();
		this.etapa = 'productos';

		// Limpiar acciones previas
		this.page.clear_actions();

		// Botón "Regresar al Escritorio" a la izquierda
		this.page.set_primary_action(__('Regresar al Escritorio'), () => {
			frappe.set_route('escritorio_ventas');
		}, 'arrow-left');

		// Agregar botón de cierre en header
		this.page.set_secondary_action(__('Cerrar Sesión'), () => this.show_cierre());

		// Mostrar info de sesión en header
		if (this.sesion) {
			this.page.set_indicator(this.sesion.name, 'blue');
		}

		// Crear componente de productos
		this.productos = new POSProductos(this);
		this.productos.load_state();

		// Setup real-time updates
		this.setup_realtime();
	}

	show_pago(carrito_data) {
		this.page_content.empty();
		this.pago = new POSPago(this, carrito_data);
		frappe.pos_pago_instance = this.pago;
	}

	show_ticket(venta_data) {
		this.page_content.empty();
		this.ticket = new POSTicket(this, venta_data);
	}

	show_cierre() {
		this.cierre = new POSCierre(this);
	}

	setup_realtime() {
		// Suscribirse a actualizaciones de stock
		frappe.realtime.on('stock_updated', (data) => {
			if (this.productos) {
				this.productos.update_stock(data.producto, data.cantidad_disponible);
			}
		});

		// Polling de respaldo cada 30s
		if (this.polling_interval) {
			clearInterval(this.polling_interval);
		}

		this.polling_interval = setInterval(() => {
			if (this.productos && this.etapa === 'productos') {
				this.productos.sync_stock();
			}
		}, 30000);
	}

	set_sesion(sesion) {
		this.sesion = sesion;
		localStorage.setItem('pos_sesion', JSON.stringify(sesion));
		this.show_productos();
	}

	load_state() {
		let saved = localStorage.getItem('pos_sesion');
		if (saved) {
			try {
				this.sesion = JSON.parse(saved);
			} catch (e) {
				console.error('Error loading session state:', e);
			}
		}
	}

	reset() {
		// Limpiar datos de la sesión incluyendo cliente
		if (this.sesion) {
			const session_key = `pos_session_${this.sesion.name}`;
			localStorage.removeItem(session_key);
		}

		this.sesion = null;
		localStorage.removeItem('pos_sesion');
		localStorage.removeItem('pos_carrito');

		if (this.polling_interval) {
			clearInterval(this.polling_interval);
		}

		this.show_apertura();
	}

	get_ventas_sesion() {
		return this.sesion?.ventas || [];
	}
}

// ============================================================================
// COMPONENTE: APERTURA DE SESIÓN
// ============================================================================

class POSApertura {
	constructor(parent) {
		this.parent = parent;
		this.make();
	}

	make() {
		if (this.dialog) {
			this.dialog.show();
			return;
		}

		this.dialog = new frappe.ui.Dialog({
			title: __('Apertura de Caja'),
			fields: [
				{
					fieldtype: 'Link',
					fieldname: 'perfil_pos',
					label: __('Perfil POS'),
					options: 'Perfil de POS',
					reqd: 1,
					get_query: () => {
						return {
							filters: { habilitado: 1 }
						};
					},
					onchange: () => {
						// Auto-completar información del perfil
						let perfil = this.dialog.get_value('perfil_pos');
						if (perfil) {
							frappe.db.get_value('Perfil de POS', perfil,
								['punto_de_venta', 'almacen', 'lista_de_precios'],
								(r) => {
									if (r) {
										frappe.show_alert({
											message: __('Perfil cargado: {0}', [perfil]),
											indicator: 'green'
										});
									}
								}
							);
						}
					}
				},
				{
					fieldtype: 'Section Break'
				},
				{
					fieldtype: 'Currency',
					fieldname: 'monto_apertura',
					label: __('Monto Inicial en Caja'),
					reqd: 1,
					default: 1000
				},
				{
					fieldtype: 'Small Text',
					fieldname: 'observaciones',
					label: __('Observaciones')
				}
			],
			primary_action_label: __('Abrir Caja'),
			primary_action: (values) => {
				this.abrir_sesion(values);
			}
		});

		// Manejar cierre del diálogo
		this.dialog.$wrapper.on('hidden.bs.modal', () => {
			// Asegurar que la página vuelva a ser visible
			$('body').removeClass('modal-open');
			$('.modal-backdrop').remove();
		});

		this.dialog.show();

		// Agregar mensaje informativo
		this.dialog.$wrapper.find('.modal-body').prepend(`
			<div class="alert alert-info">
				<strong>${__('Bienvenido al POS')}</strong><br>
				${__('Seleccione su perfil POS e ingrese el monto inicial en caja para comenzar.')}
			</div>
		`);
	}

	abrir_sesion(values) {
		frappe.call({
			method: 'endersuite.ventas.services.pos_service.open_pos_session',
			args: {
				perfil_pos: values.perfil_pos,
				monto_apertura: values.monto_apertura
			},
			freeze: true,
			freeze_message: __('Abriendo sesión...'),
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({
						message: __('Sesión abierta exitosamente'),
						indicator: 'green'
					});
					this.parent.set_sesion(r.message);
					this.dialog.hide();
				}
			}
		});
	}
}

// ============================================================================
// COMPONENTE: PRODUCTOS Y CARRITO
// ============================================================================

class POSProductos {
	constructor(parent) {
		this.parent = parent;
		this.productos = [];
		this.carrito = [];
		this.cliente_actual = null;
		this.make();
		this.load_session_data();
	}

	load_session_data() {
		// Cargar cliente guardado de la sesión
		const session_key = `pos_session_${this.parent.sesion.name}`;
		const saved_data = localStorage.getItem(session_key);

		if (saved_data) {
			try {
				const data = JSON.parse(saved_data);
				this.cliente_actual = data.cliente;
			} catch (e) {
				console.error('Error loading session data:', e);
			}
		}

		// Si no hay cliente guardado, pedir selección
		if (!this.cliente_actual) {
			this.prompt_cliente();
		} else {
			this.render_cliente_info();
			this.load_productos();
		}
	}

	save_session_data() {
		const session_key = `pos_session_${this.parent.sesion.name}`;
		const data = {
			cliente: this.cliente_actual
		};
		localStorage.setItem(session_key, JSON.stringify(data));
	}

	async prompt_cliente() {
		// Mostrar diálogo para seleccionar cliente
		const dialog = new frappe.ui.Dialog({
			title: __('Seleccionar Cliente'),
			fields: [
				{
					fieldtype: 'Link',
					fieldname: 'cliente',
					label: __('Cliente'),
					options: 'Cliente',
					reqd: 1,
					default: this.cliente_actual || ''
				}
			],
			primary_action_label: __('Continuar'),
			primary_action: (values) => {
				this.cliente_actual = values.cliente;
				this.save_session_data();
				dialog.hide();
				this.render_cliente_info();
				if (this.productos.length === 0) {
					this.load_productos();
				}
			}
		});
		dialog.show();
		dialog.$wrapper.find('.modal-content').css('width', '400px');
		// Deshabilitar cierre del modal clickeando fuera
		dialog.$wrapper.find('.modal').attr('data-backdrop', 'static');
		dialog.$wrapper.find('.modal').attr('data-keyboard', 'false');
	}

	render_cliente_info() {
		const header = this.parent.page_content.find('.pos-cliente-info');
		if (header.length > 0) {
			header.find('.cliente-nombre').text(this.cliente_actual);
		}
	}

	make() {
		// Crear contenedor principal con nuevo layout
		this.parent.page_content.html(`
			<div class="pos-productos-container" style="display: grid; grid-template-columns: 1fr 400px; gap: 16px; height: calc(100vh - 120px);">
				<div class="pos-productos-panel" style="display: flex; flex-direction: column;">
					<div class="pos-filters" style="display: flex; gap: 8px; margin-bottom: 16px;">
						<div class="pos-search-wrapper" style="flex: 1;"></div>
						<div class="pos-categoria-filter" style="width: 200px;"></div>
					</div>
					<div class="productos-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; overflow-y: auto; padding: 8px;"></div>
				</div>
				<div class="pos-carrito-panel" style="display: flex; flex-direction: column; background: #f8f9fa; border-radius: 8px; padding: 16px;">
					<div class="pos-cliente-info" style="background: white; padding: 12px; margin-bottom: 16px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; border: 2px solid #e0e0e0;">
						<div>
							<strong>${__('Cliente')}:</strong><br>
							<span class="cliente-nombre" style="font-size: 14px;">${this.cliente_actual}</span>
						</div>
						<button class="btn btn-sm btn-secondary btn-cambiar-cliente">${__('Cambiar')}</button>
					</div>
					<h4 style="margin-bottom: 12px;">${__('Carrito de Compras')}</h4>
					<div class="carrito-items" style="flex: 1; overflow-y: auto; margin-bottom: 12px; min-height: 200px;"></div>
					<div class="totales-section" style="background: white; padding: 12px; border-radius: 4px; margin-bottom: 12px;"></div>
					<div class="pos-actions"></div>
				</div>
			</div>
		`);

		// Botón cambiar cliente
		this.parent.page_content.find('.btn-cambiar-cliente').on('click', () => {
			this.prompt_cliente();
		});

		// Crear búsqueda
		this.search_field = frappe.ui.form.make_control({
			parent: this.parent.page_content.find('.pos-search-wrapper'),
			df: {
				fieldtype: 'Data',
				label: __('Buscar'),
				placeholder: __('Buscar producto...'),
				onchange: () => this.filter_productos()
			},
			render_input: true
		});

		// Crear filtro de categoría
		this.categoria_field = frappe.ui.form.make_control({
			parent: this.parent.page_content.find('.pos-categoria-filter'),
			df: {
				fieldtype: 'Link',
				label: __('Categoría'),
				options: 'Categoria',
				onchange: () => this.filter_productos()
			},
			render_input: true
		});

		// Botones de acciones
		this.render_actions();
	}

	async load_productos() {
		try {
			// Validar que tenemos los datos necesarios
			if (!this.parent.sesion) {
				frappe.throw(__('No hay sesión activa'));
				return;
			}

			if (!this.parent.sesion.almacen || !this.parent.sesion.lista_de_precios) {
				console.error('Datos de sesión incompletos:', this.parent.sesion);
				frappe.throw(__('La sesión no tiene almacén o lista de precios configurados'));
				return;
			}

			const r = await frappe.call({
				method: 'endersuite.ventas.services.pos_service.get_productos_pos',
				args: {
					almacen: this.parent.sesion.almacen,
					lista_de_precios: this.parent.sesion.lista_de_precios
				}
			});

			if (r.message) {
				this.productos = r.message;
				this.render_productos();
			}
		} catch (error) {
			console.error('Error loading products:', error);
			frappe.msgprint(__('Error al cargar productos: ') + (error.message || error));
		}
	}

	render_productos() {
		const grid = this.parent.page_content.find('.productos-grid');
		const search = (this.search_field.get_value() || '').toLowerCase();
		const categoria = this.categoria_field.get_value();

		let productos_filtrados = this.productos;

		// Filtrar por búsqueda
		if (search) {
			productos_filtrados = productos_filtrados.filter(p =>
				p.nombre.toLowerCase().includes(search) ||
				(p.sku || '').toLowerCase().includes(search)
			);
		}

		// Filtrar por categoría
		if (categoria) {
			productos_filtrados = productos_filtrados.filter(p => p.categoria === categoria);
		}

		grid.empty();
		productos_filtrados.forEach(producto => {
			const sin_stock = producto.mantener_stock && producto.cantidad_disponible <= 0;
			const imagen_url = producto.imagen || '/assets/endersuite/images/default-product.png';

			const card = $(`
				<div class="producto-card ${sin_stock ? 'producto-sin-stock' : ''}"
					 data-producto="${producto.name}"
					 draggable="${!sin_stock}"
					 style="background: white; border-radius: 8px; padding: 8px; cursor: ${sin_stock ? 'not-allowed' : 'grab'}; border: 2px solid #e0e0e0; transition: all 0.2s;">
					<div style="width: 100%; height: 100px; overflow: hidden; border-radius: 4px; margin-bottom: 8px; background: #f5f5f5; display: flex; align-items: center; justify-content: center;">
						<img src="${imagen_url}" 
							 style="max-width: 100%; max-height: 100%; object-fit: contain;"
							 onerror="this.src='/assets/frappe/images/ui-states/placeholder-image.svg'">
					</div>
					<div style="font-weight: 600; font-size: 13px; margin-bottom: 4px; height: 36px; overflow: hidden; line-height: 1.3;">${producto.nombre}</div>
					<div style="color: #666; font-size: 11px; margin-bottom: 4px;">${producto.sku || ''}</div>
					<div style="font-weight: bold; color: #2490ef; font-size: 14px; margin-bottom: 4px;">${format_currency(producto.precio, 'MXN')}</div>
					<div style="font-size: 11px; color: ${sin_stock ? '#d32f2f' : '#666'};">
						${producto.mantener_stock ? __('Stock: {0}', [producto.cantidad_disponible]) : __('Sin control')}
					</div>
				</div>
			`);

			if (!sin_stock) {
				// Click para agregar
				card.on('click', () => this.add_to_cart(producto));

				// Drag and drop
				card.on('dragstart', (e) => {
					e.originalEvent.dataTransfer.setData('producto', JSON.stringify(producto));
					card.css('opacity', '0.5');
				});

				card.on('dragend', () => {
					card.css('opacity', '1');
				});

				// Hover effect
				card.on('mouseenter', () => {
					card.css('border-color', '#2490ef');
					card.css('transform', 'translateY(-2px)');
					card.css('box-shadow', '0 4px 8px rgba(0,0,0,0.1)');
				});

				card.on('mouseleave', () => {
					card.css('border-color', '#e0e0e0');
					card.css('transform', 'translateY(0)');
					card.css('box-shadow', 'none');
				});
			}

			grid.append(card);
		});

		// Configurar drop zone en carrito
		this.setup_drop_zone();
	}

	setup_drop_zone() {
		const carrito_container = this.parent.page_content.find('.carrito-items');

		carrito_container.off('dragover drop');

		carrito_container.on('dragover', (e) => {
			e.preventDefault();
			carrito_container.css('background', '#e3f2fd');
		});

		carrito_container.on('dragleave', () => {
			carrito_container.css('background', '');
		});

		carrito_container.on('drop', (e) => {
			e.preventDefault();
			carrito_container.css('background', '');

			const producto_data = e.originalEvent.dataTransfer.getData('producto');
			if (producto_data) {
				const producto = JSON.parse(producto_data);
				this.add_to_cart(producto);
			}
		});
	}

	filter_productos() {
		this.render_productos();
	}

	add_to_cart(producto) {
		// Verificar si ya está en el carrito
		const existing = this.carrito.find(item => item.producto === producto.name);

		if (existing) {
			// Verificar stock disponible
			if (producto.mantener_stock && existing.cantidad >= producto.cantidad_disponible) {
				frappe.show_alert({
					message: __('No hay suficiente stock disponible'),
					indicator: 'orange'
				});
				return;
			}
			existing.cantidad += 1;
		} else {
			this.carrito.push({
				producto: producto.name,
				nombre: producto.nombre,
				sku: producto.sku,
				precio_unitario: producto.precio,
				cantidad: 1,
				impuesto: producto.tipo_de_impuesto,
				porcentaje_impuesto: producto.porcentaje_impuesto || 0,
				incluido_en_el_precio: producto.incluido_en_el_precio || 0,
				descuento_porcentaje: 0,
				mantener_stock: producto.mantener_stock,
				cantidad_disponible: producto.cantidad_disponible
			});
		}

		this.render_carrito();
		this.save_state();
	}

	render_carrito() {
		const container = this.parent.page_content.find('.carrito-items');
		container.empty();

		if (this.carrito.length === 0) {
			container.html(`
				<div style="text-align: center; padding: 40px; color: #6c757d;">
					<p>${__('El carrito está vacío')}</p>
					<small>${__('Seleccione productos para agregar')}</small>
				</div>
			`);
			this.render_totales();
			return;
		}

		this.carrito.forEach((item, idx) => {
			const subtotal = item.cantidad * item.precio_unitario;
			const item_html = $(`
				<div class="carrito-item">
					<div class="item-info">
						<strong>${item.nombre}</strong>
						<small>${item.sku || ''}</small>
					</div>
					<div class="item-controls">
						<button class="btn btn-sm btn-qty btn-minus">-</button>
						<input type="number" class="qty-input" value="${item.cantidad}" min="1">
						<button class="btn btn-sm btn-qty btn-plus">+</button>
					</div>
					<div class="item-precio">${format_currency(subtotal, 'MXN')}</div>
					<button class="btn-remove">×</button>
				</div>
			`);

			// Event handlers
			item_html.find('.btn-minus').on('click', () => {
				if (item.cantidad > 1) {
					item.cantidad -= 1;
					this.render_carrito();
					this.save_state();
				}
			});

			item_html.find('.btn-plus').on('click', () => {
				if (item.mantener_stock && item.cantidad >= item.cantidad_disponible) {
					frappe.show_alert({
						message: __('No hay suficiente stock disponible'),
						indicator: 'orange'
					});
					return;
				}
				item.cantidad += 1;
				this.render_carrito();
				this.save_state();
			});

			item_html.find('.qty-input').on('change', (e) => {
				const new_qty = parseInt(e.target.value) || 1;
				if (new_qty < 1) {
					e.target.value = 1;
					return;
				}
				if (item.mantener_stock && new_qty > item.cantidad_disponible) {
					frappe.show_alert({
						message: __('No hay suficiente stock disponible'),
						indicator: 'orange'
					});
					e.target.value = item.cantidad;
					return;
				}
				item.cantidad = new_qty;
				this.render_carrito();
				this.save_state();
			});

			item_html.find('.btn-remove').on('click', () => {
				this.carrito.splice(idx, 1);
				this.render_carrito();
				this.save_state();
			});

			container.append(item_html);
		});

		this.render_totales();
	}

	render_totales() {
		const totales = this.calculate_totals();
		const container = this.parent.page_content.find('.totales-section');

		container.html(`
			<div class="total-row">
				<span>${__('Subtotal')}:</span>
				<strong>${format_currency(totales.subtotal, 'MXN')}</strong>
			</div>
			<div class="total-row">
				<span>${__('Impuestos')}:</span>
				<strong>${format_currency(totales.impuestos_totales, 'MXN')}</strong>
			</div>
			<div class="total-row total-final">
				<span>${__('TOTAL')}:</span>
				<strong>${format_currency(totales.total, 'MXN')}</strong>
			</div>
		`);
	}

	calculate_totals() {
		let subtotal = 0;
		let impuestos_trasladados = 0;
		let impuestos_retenidos = 0;

		this.carrito.forEach(item => {
			const precio_total_item = item.cantidad * item.precio_unitario;

			if (item.incluido_en_el_precio) {
				// IVA INCLUIDO - El precio ya incluye impuestos (RETENIDO)
				const precio_sin_impuestos = precio_total_item / (1 + (item.porcentaje_impuesto / 100));
				impuestos_retenidos += precio_total_item - precio_sin_impuestos;
				subtotal += precio_total_item;
			} else {
				// IVA NO INCLUIDO - Los impuestos se suman (TRASLADADO)
				const impuesto_calculado = precio_total_item * (item.porcentaje_impuesto / 100);
				impuestos_trasladados += impuesto_calculado;
				subtotal += precio_total_item;
			}
		});

		return {
			subtotal: subtotal,
			impuestos_trasladados: impuestos_trasladados,
			impuestos_retenidos: impuestos_retenidos,
			impuestos_totales: impuestos_trasladados + impuestos_retenidos,
			total: subtotal + impuestos_trasladados  // Solo sumamos trasladados, retenidos ya están incluidos
		};
	}

	render_actions() {
		const container = this.parent.page_content.find('.pos-actions');
		container.html(`
			<button class="btn btn-default btn-limpiar">${__('Limpiar Carrito')}</button>
			<button class="btn btn-primary btn-pagar">${__('Proceder al Pago')}</button>
		`);

		container.find('.btn-limpiar').on('click', () => {
			if (this.carrito.length === 0) return;

			frappe.confirm(
				__('¿Está seguro de limpiar el carrito?'),
				() => {
					this.carrito = [];
					this.render_carrito();
					this.save_state();
				}
			);
		});

		container.find('.btn-pagar').on('click', () => {
			if (this.carrito.length === 0) {
				frappe.msgprint(__('El carrito está vacío'));
				return;
			}

			if (!this.cliente_actual) {
				frappe.msgprint(__('Debe seleccionar un cliente'));
				return;
			}

			const totales = this.calculate_totals();
			this.parent.show_pago({
				carrito: this.carrito,
				totales: totales,
				cliente: this.cliente_actual
			});
		});
	}

	update_stock(producto, cantidad_disponible) {
		// Actualizar stock en lista de productos
		const prod = this.productos.find(p => p.name === producto);
		if (prod) {
			prod.cantidad_disponible = cantidad_disponible;
			this.render_productos();
		}

		// Actualizar en carrito
		const item = this.carrito.find(i => i.producto === producto);
		if (item) {
			item.cantidad_disponible = cantidad_disponible;
		}
	}

	async sync_stock() {
		// Sincronizar stock de productos en carrito
		if (this.carrito.length === 0) return;

		const productos = this.carrito.map(item => item.producto);

		try {
			const r = await frappe.call({
				method: 'endersuite.ventas.services.pos_service.get_stock_actual',
				args: {
					productos: productos,
					almacen: this.parent.sesion.almacen
				}
			});

			if (r.message) {
				Object.entries(r.message).forEach(([producto, stock]) => {
					this.update_stock(producto, stock);
				});
			}
		} catch (error) {
			console.error('Error syncing stock:', error);
		}
	}

	save_state() {
		localStorage.setItem('pos_carrito', JSON.stringify(this.carrito));
	}

	load_state() {
		const saved = localStorage.getItem('pos_carrito');
		if (saved) {
			try {
				this.carrito = JSON.parse(saved);
				this.render_carrito();
			} catch (e) {
				console.error('Error loading cart state:', e);
			}
		}
	}
}

// ============================================================================
// COMPONENTE: PAGO
// ============================================================================

class POSPago {
	constructor(parent, carrito_data) {
		this.parent = parent;
		this.carrito_data = carrito_data;
		this.cliente = carrito_data.cliente;
		this.metodos_pago = [];
		this.metodo_predeterminado = null;
		this.load_metodo_predeterminado();
	}

	async load_metodo_predeterminado() {
		try {
			const r = await frappe.call({
				method: 'endersuite.ventas.services.pos_service.get_metodos_pago_perfil',
				args: {
					perfil_pos: this.parent.sesion.perfil_pos
				}
			});

			if (r.message && r.message.length > 0) {
				// Buscar método predeterminado o tomar el primero
				const predeterminado = r.message.find(m => m.predeterminado) || r.message[0];
				this.metodo_predeterminado = predeterminado.metodo;

				// Agregar método predeterminado con total completo
				this.metodos_pago.push({
					metodo_de_pago: this.metodo_predeterminado,
					monto: this.carrito_data.totales.total
				});
			}
		} catch (error) {
			console.error('Error loading default payment method:', error);
		}

		this.make();
	}

	make() {
		if (this.dialog) {
			this.dialog.show();
			this.render_resumen();
			this.render_metodos();
			this.update_totales();
			return;
		}

		this.dialog = new frappe.ui.Dialog({
			title: __('Procesar Pago'),
			size: 'large',
			fields: [
				{
					fieldtype: 'Section Break',
					label: __('Resumen de la Venta')
				},
				{
					fieldtype: 'HTML',
					fieldname: 'resumen_html'
				},
				{
					fieldtype: 'Section Break',
					label: __('Métodos de Pago')
				},
				{
					fieldtype: 'HTML',
					fieldname: 'metodos_html'
				},
				{
					fieldtype: 'Button',
					label: __('+ Agregar Método de Pago'),
					click: () => this.agregar_metodo_pago()
				},
				{
					fieldtype: 'Section Break',
					label: ''
				},
				{
					fieldtype: 'HTML',
					fieldname: 'totales_html'
				},
				{
					fieldtype: 'Section Break',
					label: ''
				},
				{
					fieldtype: 'Check',
					fieldname: 'imprimir_ticket',
					label: __('Imprimir ticket después de la venta'),
					default: 1
				}
			],
			primary_action_label: __('Confirmar Venta'),
			primary_action: () => this.confirmar_venta(),
			secondary_action_label: __('Regresar'),
			secondary_action: () => {
				this.dialog.hide();
			}
		});

		// Quitar botón X de cerrar
		this.dialog.$wrapper.find('.modal-header .close').remove();		// Manejar cierre del diálogo
		this.dialog.$wrapper.on('hidden.bs.modal', () => {
			// Asegurar que la página vuelva a ser visible
			$('body').removeClass('modal-open');
			$('.modal-backdrop').remove();
		});

		this.dialog.show();
		this.render_resumen();
		this.render_metodos();
		this.update_totales();
	}

	render_resumen() {
		const html = `
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>${__('Producto')}</th>
						<th class="text-right">${__('Cant.')}</th>
						<th class="text-right">${__('Precio')}</th>
						<th class="text-right">${__('Total')}</th>
					</tr>
				</thead>
				<tbody>
					${this.carrito_data.carrito.map(item => `
						<tr>
							<td>${item.nombre}<br><small class="text-muted">${item.sku || ''}</small></td>
							<td class="text-right">${item.cantidad}</td>
							<td class="text-right">${format_currency(item.precio_unitario, 'MXN')}</td>
							<td class="text-right">${format_currency(item.cantidad * item.precio_unitario, 'MXN')}</td>
						</tr>
					`).join('')}
				</tbody>
				<tfoot>
					<tr>
						<td colspan="3" class="text-right"><strong>${__('Subtotal')}:</strong></td>
						<td class="text-right"><strong>${format_currency(this.carrito_data.totales.subtotal, 'MXN')}</strong></td>
					</tr>
					<tr>
						<td colspan="3" class="text-right"><strong>${__('Impuestos')}:</strong></td>
						<td class="text-right"><strong>${format_currency(this.carrito_data.totales.impuestos, 'MXN')}</strong></td>
					</tr>
					<tr style="font-size: 1.2em;">
						<td colspan="3" class="text-right"><strong>${__('TOTAL')}:</strong></td>
						<td class="text-right"><strong>${format_currency(this.carrito_data.totales.total, 'MXN')}</strong></td>
					</tr>
				</tfoot>
			</table>
		`;
		this.dialog.fields_dict.resumen_html.$wrapper.html(html);
	}

	render_metodos() {
		let html = '';

		if (this.metodos_pago.length === 0) {
			html = `<p class="text-muted">${__('No se han agregado métodos de pago')}</p>`;
		} else {
			html = `
				<table class="table table-bordered" style="margin-bottom: 0;">
					<thead>
						<tr>
							<th style="width: 50%;">${__('Método')}</th>
							<th style="width: 35%;">${__('Monto')}</th>
							<th style="width: 15%; text-align: center;">${__('Acción')}</th>
						</tr>
					</thead>
					<tbody>
						${this.metodos_pago.map((metodo, idx) => `
							<tr>
								<td>${metodo.metodo_de_pago}</td>
								<td>
									<input type="number" 
										   class="form-control monto-pago" 
										   data-idx="${idx}"
										   value="${metodo.monto}"
										   step="0.01"
										   min="0"
										   style="text-align: right;">
								</td>
								<td class="text-center">
									<button class="btn btn-sm btn-danger btn-eliminar-metodo" data-idx="${idx}">
										<i class="fa fa-trash"></i>
									</button>
								</td>
							</tr>
						`).join('')}
					</tbody>
				</table>
			`;
		}

		this.dialog.fields_dict.metodos_html.$wrapper.html(html);

		// Attach event handlers
		this.dialog.fields_dict.metodos_html.$wrapper.find('.monto-pago').on('input', (e) => {
			const idx = $(e.target).data('idx');
			const nuevo_monto = parseFloat($(e.target).val()) || 0;
			this.metodos_pago[idx].monto = nuevo_monto;
			// Usar setTimeout para evitar loops y permitir que el navegador procese el cambio
			clearTimeout(this._update_timeout);
			this._update_timeout = setTimeout(() => this.update_totales(), 100);
		});

		// Seleccionar todo el texto al hacer clic en el input
		this.dialog.fields_dict.metodos_html.$wrapper.find('.monto-pago').on('focus', function () {
			$(this).select();
		});

		this.dialog.fields_dict.metodos_html.$wrapper.find('.btn-eliminar-metodo').on('click', (e) => {
			const idx = $(e.target).closest('button').data('idx');
			this.eliminar_metodo(idx);
		});

		// Solo actualizar totales la primera vez o después de agregar/eliminar métodos
		this.update_totales();
	}

	update_totales() {
		if (!this.dialog || !this.dialog.fields_dict.totales_html || !this.dialog.fields_dict.totales_html.$wrapper) {
			return;
		}

		const total_venta = this.carrito_data.totales.total;
		const total_pagado = this.metodos_pago.reduce((sum, m) => sum + parseFloat(m.monto || 0), 0);
		const diferencia = total_pagado - total_venta;

		const es_cambio = diferencia >= 0;
		const label_diferencia = es_cambio ? __('Cambio') : __('Faltante');
		const color_diferencia = es_cambio ? '#28a745' : '#dc3545';

		const html = `
			<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; padding: 16px; background: #f8f9fa; border-radius: 4px;">
				<div style="text-align: center;">
					<div style="font-size: 12px; color: #666; margin-bottom: 4px;">${__('Total Venta')}</div>
					<div style="font-size: 24px; font-weight: bold; color: #333;">${format_currency(total_venta, 'MXN')}</div>
				</div>
				<div style="text-align: center;">
					<div style="font-size: 12px; color: #666; margin-bottom: 4px;">${__('Total Pagado')}</div>
					<div style="font-size: 24px; font-weight: bold; color: #2490ef;">${format_currency(total_pagado, 'MXN')}</div>
				</div>
				<div style="text-align: center; background: white; padding: 12px; border-radius: 4px; border: 3px solid ${color_diferencia};">
					<div style="font-size: 14px; color: ${color_diferencia}; font-weight: 600; margin-bottom: 4px;">${label_diferencia}</div>
					<div style="font-size: 28px; font-weight: bold; color: ${color_diferencia};">${format_currency(Math.abs(diferencia), 'MXN')}</div>
				</div>
			</div>
		`;

		this.dialog.fields_dict.totales_html.$wrapper.html(html);
	}

	agregar_metodo_pago() {
		const dialog = new frappe.ui.Dialog({
			title: __('Agregar Método de Pago'),
			fields: [
				{
					fieldtype: 'Link',
					fieldname: 'metodo_de_pago',
					label: __('Método de Pago'),
					options: 'Metodos de Pago',
					reqd: 1
				},
				{
					fieldtype: 'Currency',
					fieldname: 'monto',
					label: __('Monto'),
					reqd: 1,
					default: this.carrito_data.totales.total - this.get_total_pagado()
				}
			],
			primary_action_label: __('Agregar'),
			primary_action: (values) => {
				this.metodos_pago.push(values);
				this.render_metodos();
				dialog.hide();
			}
		});

		dialog.show();
	}

	eliminar_metodo(idx) {
		this.metodos_pago.splice(idx, 1);
		this.render_metodos();
	}

	get_total_pagado() {
		return this.metodos_pago.reduce((sum, metodo) => sum + (metodo.monto || 0), 0);
	}

	async confirmar_venta() {
		const total_pagado = this.get_total_pagado();

		if (total_pagado < this.carrito_data.totales.total) {
			frappe.msgprint(__('El monto pagado es menor al total de la venta'));
			return;
		}

		if (this.metodos_pago.length === 0) {
			frappe.msgprint(__('Debe agregar al menos un método de pago'));
			return;
		}

		// Validar disponibilidad de efectivo en caja
		const pago_efectivo = this.metodos_pago
			.filter(m => m.metodo_de_pago === 'Efectivo')
			.reduce((sum, m) => sum + parseFloat(m.monto || 0), 0);

		if (pago_efectivo > this.carrito_data.totales.total) {
			const cambio_requerido = pago_efectivo - this.carrito_data.totales.total;

			// Obtener efectivo disponible en caja ANTES de esta venta
			const { efectivo_disponible } = await frappe.call({
				method: 'endersuite.ventas.services.pos_service.get_efectivo_disponible',
				args: { sesion_name: this.parent.sesion.name }
			}).then(r => r.message);

			// El efectivo REAL disponible incluye lo que el cliente está pagando ahora
			const efectivo_total = efectivo_disponible + pago_efectivo;
			const efectivo_despues_cambio = efectivo_total - cambio_requerido;

			// Verificar si hay suficiente efectivo para dar cambio (incluyendo el pago actual)
			if (cambio_requerido > efectivo_total) {
				frappe.msgprint({
					title: __('Efectivo insuficiente'),
					message: __('No hay suficiente efectivo en caja para dar cambio.<br><br>'
						+ '<b>Efectivo en caja:</b> {0}<br>'
						+ '<b>Efectivo recibido:</b> {1}<br>'
						+ '<b>Efectivo total:</b> {2}<br>'
						+ '<b>Cambio requerido:</b> {3}<br><br>'
						+ 'Por favor, solicite otro método de pago o un monto más cercano al total.',
						[format_currency(efectivo_disponible, 'MXN'),
						format_currency(pago_efectivo, 'MXN'),
						format_currency(efectivo_total, 'MXN'),
						format_currency(cambio_requerido, 'MXN')]),
					indicator: 'red'
				});
				return;
			}

			// Advertir si quedarás con menos del 20% del efectivo que tenías
			const porcentaje_restante = (efectivo_despues_cambio / efectivo_total) * 100;

			if (porcentaje_restante < 20) {
				const confirmacion = await new Promise(resolve => {
					frappe.confirm(
						__('⚠️ Advertencia: Quedarás con muy poco efectivo en caja<br><br>'
							+ '<b>Total de venta:</b> {0}<br>'
							+ '<b>Efectivo recibido:</b> {1}<br>'
							+ '<b>Cambio a entregar:</b> {2}<br>'
							+ '<b>Efectivo en caja antes:</b> {3}<br>'
							+ '<b>Efectivo después del cambio:</b> {4}<br><br>'
							+ '¿Desea continuar con esta transacción?',
							[format_currency(this.carrito_data.totales.total, 'MXN'),
							format_currency(pago_efectivo, 'MXN'),
							format_currency(cambio_requerido, 'MXN'),
							format_currency(efectivo_total, 'MXN'),
							format_currency(efectivo_despues_cambio, 'MXN')]),
						() => resolve(true),
						() => resolve(false)
					);
				});

				if (!confirmacion) {
					return;
				}
			}
		}

		// Obtener valor del checkbox
		const imprimir_ticket = this.dialog.get_value('imprimir_ticket');

		try {
			const r = await frappe.call({
				method: 'endersuite.ventas.services.pos_service.create_sale',
				args: {
					sesion_pos: this.parent.sesion.name,
					productos: this.carrito_data.carrito,
					metodos_pago: this.metodos_pago,
					total: this.carrito_data.totales.total,
					cliente: this.cliente,
					imprimir_ticket: imprimir_ticket ? 1 : 0
				},
				freeze: true,
				freeze_message: __('Procesando venta...')
			});

			if (r.message) {
				// Cerrar diálogo
				this.dialog.hide();

				// Limpiar carrito pero mantener cliente
				this.parent.productos.carrito = [];
				this.parent.productos.render_carrito();
				this.parent.productos.save_state();

				// Si marcó imprimir, mostrar ticket para impresión
				if (imprimir_ticket) {
					this.parent.show_ticket(r.message);
				} else {
					// Solo mostrar mensaje de éxito
					frappe.show_alert({
						message: __('Venta registrada exitosamente: {0}', [r.message.name]),
						indicator: 'green'
					}, 5);
				}

				// Actualizar sesión
				this.parent.check_session();
			}
		} catch (error) {
			console.error('Error creating sale:', error);
			frappe.msgprint(__('Error al procesar la venta'));
		}
	}
}

// Exponer instancia para botones inline
frappe.pos_pago_instance = null;

// ============================================================================
// COMPONENTE: TICKET
// ============================================================================

class POSTicket {
	constructor(parent, venta_data) {
		this.parent = parent;
		this.venta_data = venta_data;
		this.make();
	}

	make() {
		this.dialog = new frappe.ui.Dialog({
			title: __('Venta Completada'),
			size: 'large',
			fields: [
				{
					fieldtype: 'HTML',
					fieldname: 'ticket_html'
				}
			],
			primary_action_label: __('Imprimir'),
			primary_action: () => this.imprimir(),
			secondary_action_label: __('Nueva Venta'),
			secondary_action: () => {
				this.dialog.hide();
				this.parent.productos.carrito = [];
				this.parent.productos.render_carrito();
				this.parent.productos.save_state();
				this.parent.show_productos();
			}
		});

		this.render_ticket();
		this.dialog.show();
	}

	render_ticket() {
		const nota = this.venta_data;
		const html = `
			<div id="pos-ticket" style="max-width: 400px; margin: 0 auto; padding: 20px; font-family: monospace;">
				<div style="text-align: center; margin-bottom: 20px;">
					<h3 style="margin: 0;">${this.parent.sesion.punto_de_venta || 'PUNTO DE VENTA'}</h3>
					<p style="margin: 5px 0; font-size: 12px;">
						RFC: ${frappe.sys_defaults.company || ''}<br>
						${__('Ticket No')}: ${nota.name}
					</p>
					<p style="margin: 5px 0; font-size: 12px;">
						${frappe.datetime.now_datetime()}
					</p>
				</div>

				<div style="border-top: 2px dashed #000; border-bottom: 2px dashed #000; padding: 10px 0; margin: 10px 0;">
					<table style="width: 100%; font-size: 12px;">
						<thead>
							<tr>
								<th style="text-align: left;">${__('Producto')}</th>
								<th style="text-align: right;">${__('Cant')}</th>
								<th style="text-align: right;">${__('Precio')}</th>
								<th style="text-align: right;">${__('Total')}</th>
							</tr>
						</thead>
						<tbody>
							${nota.productos.map(item => `
								<tr>
									<td style="padding: 5px 0;">${item.nombre}</td>
									<td style="text-align: right;">${item.cantidad}</td>
									<td style="text-align: right;">$${item.precio_unitario.toFixed(2)}</td>
									<td style="text-align: right;">$${(item.cantidad * item.precio_unitario).toFixed(2)}</td>
								</tr>
							`).join('')}
						</tbody>
					</table>
				</div>

				<div style="font-size: 12px; margin: 10px 0;">
					<div style="display: flex; justify-content: space-between; padding: 3px 0;">
						<span>${__('Subtotal')}:</span>
						<span>$${nota.subtotal.toFixed(2)}</span>
					</div>
					<div style="display: flex; justify-content: space-between; padding: 3px 0;">
						<span>${__('Impuestos')}:</span>
						<span>$${nota.total_impuestos.toFixed(2)}</span>
					</div>
					<div style="display: flex; justify-content: space-between; padding: 8px 0; font-size: 16px; font-weight: bold; border-top: 2px solid #000;">
						<span>${__('TOTAL')}:</span>
						<span>$${nota.total_final.toFixed(2)}</span>
					</div>
				</div>

				<div style="border-top: 2px dashed #000; padding: 10px 0; margin: 10px 0; font-size: 12px;">
					<strong>${__('Métodos de Pago')}:</strong><br>
					${nota.metodos_pago.map(mp => `
						${mp.metodo_de_pago}: $${mp.monto.toFixed(2)}<br>
					`).join('')}
				</div>

				<div style="text-align: center; margin-top: 20px; font-size: 11px;">
					<p>${__('¡Gracias por su compra!')}</p>
					<p style="margin: 5px 0;">
						${__('Cajero')}: ${frappe.session.user}<br>
						${__('Sesión')}: ${this.parent.sesion.name}
					</p>
				</div>
			</div>
		`;

		this.dialog.fields_dict.ticket_html.$wrapper.html(html);
	}

	imprimir() {
		const printWindow = window.open('', '', 'height=600,width=400');
		printWindow.document.write('<html><head><title>Ticket</title>');
		printWindow.document.write('</head><body>');
		printWindow.document.write(document.getElementById('pos-ticket').innerHTML);
		printWindow.document.write('</body></html>');
		printWindow.document.close();
		printWindow.print();
	}
}

// ============================================================================
// COMPONENTE: CIERRE DE SESIÓN
// ============================================================================

class POSCierre {
	constructor(parent) {
		this.parent = parent;
		this.make();
	}

	async make() {
		// Obtener resumen de la sesión
		const resumen = await this.get_resumen_sesion();

		this.dialog = new frappe.ui.Dialog({
			title: __('Cierre de Caja'),
			size: 'large',
			fields: [
				{
					fieldtype: 'Section Break',
					label: __('Resumen de Ventas')
				},
				{
					fieldtype: 'HTML',
					fieldname: 'resumen_html'
				},
				{
					fieldtype: 'Section Break',
					label: __('Arqueo de Caja')
				},
				{
					fieldtype: 'Currency',
					fieldname: 'monto_esperado',
					label: __('Monto Esperado en Caja'),
					read_only: 1,
					default: resumen.monto_esperado
				},
				{
					fieldtype: 'Column Break'
				},
				{
					fieldtype: 'Currency',
					fieldname: 'monto_real',
					label: __('Monto Real en Caja'),
					reqd: 1
				},
				{
					fieldtype: 'Section Break'
				},
				{
					fieldtype: 'Currency',
					fieldname: 'diferencia',
					label: __('Diferencia'),
					read_only: 1
				},
				{
					fieldtype: 'Small Text',
					fieldname: 'observaciones_cierre',
					label: __('Observaciones')
				}
			],
			primary_action_label: __('Cerrar Sesión'),
			primary_action: (values) => this.cerrar_sesion(values),
			secondary_action_label: __('Cancelar'),
			secondary_action: () => this.dialog.hide()
		});

		// Calcular diferencia automáticamente
		this.dialog.fields_dict.monto_real.$input.on('change', () => {
			const esperado = this.dialog.get_value('monto_esperado');
			const real = this.dialog.get_value('monto_real');
			this.dialog.set_value('diferencia', real - esperado);
		});

		this.render_resumen(resumen);
		this.dialog.show();
	}

	async get_resumen_sesion() {
		const r = await frappe.call({
			method: 'endersuite.ventas.services.pos_service.get_session_summary',
			args: { sesion_pos: this.parent.sesion.name }
		});

		return r.message || {
			total_ventas: 0,
			num_ventas: 0,
			monto_esperado: this.parent.sesion.monto_apertura || 0,
			ventas: []
		};
	}

	render_resumen(resumen) {
		const html = `
			<div style="margin-bottom: 20px;">
				<div class="row">
					<div class="col-sm-4">
						<div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
							<h4 style="margin: 0; color: #007bff;">${resumen.num_ventas}</h4>
							<p style="margin: 5px 0; font-size: 12px;">${__('Total Ventas')}</p>
						</div>
					</div>
					<div class="col-sm-4">
						<div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
							<h4 style="margin: 0; color: #28a745;">${format_currency(resumen.total_ventas, 'MXN')}</h4>
							<p style="margin: 5px 0; font-size: 12px;">${__('Ingresos')}</p>
						</div>
					</div>
					<div class="col-sm-4">
						<div style="text-align: center; padding: 15px; background: #f8f9fa; border-radius: 8px;">
							<h4 style="margin: 0; color: #6c757d;">${format_currency(resumen.monto_esperado, 'MXN')}</h4>
							<p style="margin: 5px 0; font-size: 12px;">${__('En Caja')}</p>
						</div>
					</div>
				</div>
			</div>

			${resumen.ventas && resumen.ventas.length > 0 ? `
				<table class="table table-bordered table-sm">
					<thead>
						<tr>
							<th>${__('Nota')}</th>
							<th>${__('Hora')}</th>
							<th class="text-right">${__('Total')}</th>
						</tr>
					</thead>
					<tbody>
						${resumen.ventas.map(venta => `
							<tr>
								<td>${venta.name}</td>
								<td>${frappe.datetime.str_to_user(venta.fecha)}</td>
								<td class="text-right">${format_currency(venta.total_final, 'MXN')}</td>
							</tr>
						`).join('')}
					</tbody>
				</table>
			` : ''}
		`;

		this.dialog.fields_dict.resumen_html.$wrapper.html(html);
	}

	async cerrar_sesion(values) {
		try {
			const r = await frappe.call({
				method: 'endersuite.ventas.services.pos_service.close_pos_session',
				args: {
					sesion_pos: this.parent.sesion.name,
					monto_real: values.monto_real,
					observaciones: values.observaciones_cierre
				},
				freeze: true,
				freeze_message: __('Cerrando sesión...')
			});

			if (r.message) {
				frappe.show_alert({
					message: __('Sesión cerrada exitosamente'),
					indicator: 'green'
				});

				this.dialog.hide();

				// Limpiar todos los datos
				this.parent.reset();

				// Forzar reinicialización completa
				this.parent.apertura = null;
				this.parent.productos = null;
				this.parent.cierre = null;

				// Reinicializar la aplicación
				this.parent.check_session();
			}
		} catch (error) {
			console.error('Error closing session:', error);
			frappe.msgprint(__('Error al cerrar la sesión'));
		}
	}
}

// Inicializar CSS básico
frappe.provide('frappe.pos');
frappe.pos.init_css = function () {
	if (!$('#pos-custom-css').length) {
		$('head').append(`
			<style id="pos-custom-css">
				.pos-productos-container {
					display: flex;
					height: calc(100vh - 150px);
					gap: 20px;
					padding: 20px;
				}
				.pos-productos-panel {
					flex: 2;
					overflow-y: auto;
				}
				.pos-carrito-panel {
					flex: 0 0 400px;
					background: var(--card-bg, #f8f9fa);
					padding: 20px;
					border-left: 1px solid var(--border-color, #dee2e6);
					overflow-y: auto;
					display: flex;
					flex-direction: column;
				}
				.productos-grid {
					display: grid;
					grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
					gap: 16px;
					padding: 10px;
				}
				.producto-card {
					background: white;
					border: 1px solid #dee2e6;
					border-radius: 8px;
					padding: 12px;
					cursor: pointer;
					transition: all 0.2s;
					text-align: center;
				}
				.producto-card:hover {
					transform: translateY(-2px);
					box-shadow: 0 4px 12px rgba(0,0,0,0.15);
					border-color: var(--primary-color, #007bff);
				}
				.producto-nombre {
					font-weight: 600;
					margin-bottom: 4px;
					font-size: 14px;
				}
				.producto-sku {
					color: #6c757d;
					font-size: 12px;
					margin-bottom: 8px;
				}
				.producto-precio {
					color: var(--primary-color, #007bff);
					font-weight: bold;
					font-size: 16px;
				}
				.producto-stock {
					font-size: 11px;
					color: #28a745;
					margin-top: 4px;
				}
				.producto-sin-stock {
					opacity: 0.5;
					cursor: not-allowed;
				}
				.carrito-items {
					flex: 1;
					overflow-y: auto;
					margin-bottom: 16px;
				}
				.carrito-item {
					background: white;
					border: 1px solid #dee2e6;
					border-radius: 6px;
					padding: 12px;
					margin-bottom: 8px;
					display: flex;
					align-items: center;
					gap: 12px;
				}
				.item-info {
					flex: 1;
				}
				.item-info strong {
					display: block;
					font-size: 14px;
				}
				.item-info small {
					color: #6c757d;
					font-size: 12px;
				}
				.item-controls {
					display: flex;
					align-items: center;
					gap: 8px;
				}
				.btn-qty {
					width: 30px;
					height: 30px;
					padding: 0;
					border-radius: 4px;
				}
				.qty-input {
					width: 60px;
					text-align: center;
					border: 1px solid #dee2e6;
					border-radius: 4px;
					padding: 4px;
				}
				.item-precio {
					font-weight: 600;
					color: var(--primary-color, #007bff);
					min-width: 80px;
					text-align: right;
				}
				.btn-remove {
					background: #dc3545;
					color: white;
					border: none;
					border-radius: 4px;
					width: 30px;
					height: 30px;
					cursor: pointer;
				}
				.totales-section {
					border-top: 2px solid #dee2e6;
					padding-top: 16px;
					margin-top: 16px;
				}
				.total-row {
					display: flex;
					justify-content: space-between;
					padding: 8px 0;
					font-size: 14px;
				}
				.total-row.total-final {
					font-size: 18px;
					border-top: 1px solid #dee2e6;
					padding-top: 12px;
					margin-top: 8px;
				}
				.pos-search {
					margin-bottom: 20px;
				}
				.pos-actions {
					margin-top: 16px;
					display: flex;
					gap: 8px;
				}
				.pos-actions .btn {
					flex: 1;
				}
			</style>
		`);
	}
};

// Inicializar CSS cuando se carga el script
frappe.pos.init_css();
