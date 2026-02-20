frappe.pages['escritorio_ventas'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Ventas',
        single_column: true
    });

    // Guardar referencia
    wrapper.page = page;
    wrapper.escritorio_initialized = false;
}

frappe.pages['escritorio_ventas'].on_page_show = function (wrapper) {
    // Refrescar datos cada vez que se muestra la página
    refresh_dashboard(wrapper.page);
}

function refresh_dashboard(page) {
    // Limpiar contenido previo
    page.main.empty();

    // Verificar si hay sesión POS activa
    frappe.call({
        method: "endersuite.ventas.services.pos_service.get_active_session",
        callback: function (session_r) {
            frappe.call({
                method: "endersuite.ventas.page.escritorio_ventas.escritorio_ventas.get_dashboard_data",
                callback: function (r) {
                    if (r.message) {
                        render_dashboard(page, r.message, session_r.message);
                    }
                }
            });
        }
    });
}

function render_dashboard(page, data, active_session) {
    let $container = $(`<div class="dashboard-container"></div>`).appendTo(page.main);

    // Determinar botones del banner
    let banner_buttons = '';
    if (active_session) {
        // Si hay sesión activa, mostrar botón para regresar
        banner_buttons = `
            <button class="btn btn-success btn-lg" onclick="frappe.set_route('pos')" style="margin-right: 8px;">
                🔄 Regresar a la Sesión
            </button>
            <button class="btn btn-primary btn-lg" onclick="frappe.set_route('pos')">
                🛍️ Punto de Venta
            </button>
        `;
    } else {
        // Si no hay sesión, solo mostrar botón de abrir
        banner_buttons = `
            <button class="btn btn-primary btn-lg" onclick="frappe.set_route('pos')">
                🛍️ Abrir Punto de Venta
            </button>
        `;
    }

    // Welcome Banner
    let $banner = $(`
		<div class="dashboard-banner dashboard-section" data-id="banner">
			<div class="banner-content">
				<h1>¡Hola, ${frappe.session.user_fullname}! 👋</h1>
				<p>Bienvenido al Módulo de Ventas.</p>
                ${active_session ? `<p style="color: #28a745; font-weight: 600;">✓ Sesión POS activa: ${active_session.name}</p>` : ''}
			</div>
            <div class="banner-actions">
                ${banner_buttons}
            </div>
		</div>
	`).appendTo($container);

    // Metrics Cards
    let $metrics = $(`
		<div class="dashboard-metrics dashboard-section" data-id="metrics">
            <div class="section-header hidden">
                <div class="drag-handle-main"><span class="drag-icon">⋮⋮</span></div>
            </div>
			<div class="metric-card">
				<div class="metric-title">Ventas Hoy</div>
				<div class="metric-value">${format_currency(data.sales_today)}</div>
			</div>
			<div class="metric-card">
				<div class="metric-title">Ventas Mes</div>
				<div class="metric-value">${format_currency(data.sales_month)}</div>
			</div>
			<div class="metric-card">
				<div class="metric-title">Pedidos Hoy</div>
				<div class="metric-value">${data.orders_today}</div>
			</div>
			<div class="metric-card">
				<div class="metric-title">Pedidos Mes</div>
				<div class="metric-value">${data.orders_month}</div>
			</div>
		</div>
	`).appendTo($container);

    // Shortcuts Section
    let $shortcuts = $(`
		<div class="dashboard-shortcuts dashboard-section" data-id="shortcuts">
            <div class="section-header hidden">
                <div class="drag-handle-main"><span class="drag-icon">⋮⋮</span></div>
            </div>
			<div class="shortcut-title">Accesos Rápidos</div>
            
            <div class="shortcuts-columns">
                <!-- Column 1 -->
                <div class="shortcuts-column">
                    <!-- Operaciones -->
                    <div class="shortcut-section">
                        <div class="shortcut-category-title"><span>Operaciones</span></div>
                        <div class="shortcut-grid" id="grid-operaciones">
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Nota de Venta')">
                                <div class="shortcut-icon">📄</div>
                                <div class="shortcut-label">Notas de Venta</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Factura de Venta')">
                                <div class="shortcut-icon">🧾</div>
                                <div class="shortcut-label">Facturas</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Cotizacion')">
                                <div class="shortcut-icon">📜</div>
                                <div class="shortcut-label">Cotizaciones</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Orden de Venta')">
                                <div class="shortcut-icon">🛒</div>
                                <div class="shortcut-label">Ordenes de Venta</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Movimiento de Stock')">
                                <div class="shortcut-icon">📊</div>
                                <div class="shortcut-label">Movimiento de Stock</div>
                            </div>
                        </div>
                    </div>

                    <!-- Catálogos -->
                    <div class="shortcut-section">
                        <div class="shortcut-category-title"><span>Catálogos</span></div>
                        <div class="shortcut-grid" id="grid-catalogos">
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Cliente')">
                                <div class="shortcut-icon">👥</div>
                                <div class="shortcut-label">Clientes</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Producto')">
                                <div class="shortcut-icon">📦</div>
                                <div class="shortcut-label">Productos</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Almacen')">
                                <div class="shortcut-icon">🏭</div>
                                <div class="shortcut-label">Almacenes</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Vendedor')">
                                <div class="shortcut-icon">👔</div>
                                <div class="shortcut-label">Vendedores</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Column 2 -->
                <div class="shortcuts-column">
                    <!-- Punto de Venta -->
                    <div class="shortcut-section">
                        <div class="shortcut-category-title"><span>Punto de Venta</span></div>
                        <div class="shortcut-grid" id="grid-pos">
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Sesion POS')">
                                <div class="shortcut-icon">🖥️</div>
                                <div class="shortcut-label">Sesiones POS</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Punto de Venta')">
                                <div class="shortcut-icon">🏪</div>
                                <div class="shortcut-label">Puntos de Venta</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Perfil de POS')">
                                <div class="shortcut-icon">⚙️</div>
                                <div class="shortcut-label">Perfiles POS</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Formato de Ticket')">
                                <div class="shortcut-icon">🎫</div>
                                <div class="shortcut-label">Formatos Ticket</div>
                            </div>
                        </div>
                    </div>

                    <!-- Configuración -->
                    <div class="shortcut-section">
                        <div class="shortcut-category-title"><span>Configuración</span></div>
                        <div class="shortcut-grid" id="grid-config">
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Lista de Precios')">
                                <div class="shortcut-icon">💲</div>
                                <div class="shortcut-label">Listas de Precios</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'UM')">
                                <div class="shortcut-icon">📏</div>
                                <div class="shortcut-label">Unidades Medida</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Categoria')">
                                <div class="shortcut-icon">🏷️</div>
                                <div class="shortcut-label">Categorías</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Descuentos')">
                                <div class="shortcut-icon">💸</div>
                                <div class="shortcut-label">Descuentos</div>
                            </div>
                            <div class="shortcut-card" onclick="frappe.set_route('List', 'Termino de Pago Plantilla')">
                                <div class="shortcut-icon">📅</div>
                                <div class="shortcut-label">Términos Pago</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
		</div>
	`).appendTo($container);

    // Charts Section
    let $charts = $(`
		<div class="dashboard-charts dashboard-section" data-id="charts">
            <div class="section-header hidden">
                <div class="drag-handle-main"><span class="drag-icon">⋮⋮</span></div>
            </div>
			<div class="chart-card">
				<div class="chart-title">Tendencia de Ventas (Últimos 30 días)</div>
				<div id="sales-trend-chart"></div>
			</div>
			<div class="chart-card">
				<div class="chart-title">Top Productos (Este Mes)</div>
				<div id="top-products-chart"></div>
			</div>
		</div>
	`).appendTo($container);

    // Load saved layout
    load_saved_layout();

    // Clear chart containers (in case they were restored with old content)
    $("#sales-trend-chart").empty();
    $("#top-products-chart").empty();

    // Render Sales Trend Chart
    new frappe.Chart("#sales-trend-chart", {
        data: {
            labels: data.sales_trend.labels,
            datasets: [
                {
                    name: "Ventas", type: "line", values: data.sales_trend.values
                }
            ]
        },
        type: 'line',
        height: 250,
        colors: ['#7cd6fd']
    });

    // Render Top Products Chart (Custom with Images)
    let $topProductsChart = $("#top-products-chart");
    $topProductsChart.empty();

    if (data.top_products && data.top_products.length > 0) {
        let maxAmount = Math.max(...data.top_products.map(p => p.amount));

        data.top_products.forEach((product, index) => {
            let percentage = (product.amount / maxAmount) * 100;
            let imageUrl = product.imagen || '/assets/endersuite/images/no-image.svg';

            let $productRow = $(`
                <div class="product-chart-row" style="animation-delay: ${index * 0.1}s;">
                    <div class="product-info">
                        <img src="${imageUrl}" class="product-image" onerror="this.src='/assets/endersuite/images/no-image.svg'">
                        <div class="product-details">
                            <div class="product-name">${product.producto}</div>
                            <div class="product-qty">${product.qty} unidades</div>
                        </div>
                    </div>
                    <div class="product-bar-container">
                        <div class="product-bar" style="width: ${percentage}%"></div>
                        <div class="product-amount">${format_currency(product.amount)}</div>
                    </div>
                </div>
            `);
            $topProductsChart.append($productRow);
        });
    } else {
        $topProductsChart.html('<div class="no-data">No hay datos disponibles</div>');
    }


    // Load CSS
    frappe.require("assets/endersuite/css/escritorio_ventas.css");

    // Load saved layout


    // Apply Entrance Animations
    $container.find('.dashboard-section').addClass('animate-enter');

    // Collapsible Sections Logic
    $container.on('click', '.shortcut-category-title', function () {
        if (!is_edit_mode) {
            $(this).parent().toggleClass('collapsed');
        }
    });

    // Edit Mode Logic
    let is_edit_mode = false;
    let sortables = [];

    // Render Footer Controls
    let $footer = $(`
        <div class="dashboard-footer">
            <div class="footer-actions">
                <button class="btn btn-default btn-sm" id="btn-edit-interface">
                    ✏️ Editar Interfaz
                </button>
                <div class="edit-mode-buttons hidden">
                    <button class="btn btn-default btn-sm" id="btn-cancel-edit">Cancelar</button>
                    <button class="btn btn-danger btn-sm" id="btn-reset-layout">Restablecer</button>
                    <button class="btn btn-primary btn-sm" id="btn-save-shortcuts">Guardar</button>
                </div>
            </div>
        </div>
    `).appendTo($container);

    // Footer Button Events
    $footer.find('#btn-edit-interface').on('click', function () {
        toggle_edit_mode(true);
    });

    $footer.find('#btn-cancel-edit').on('click', function () {
        toggle_edit_mode(false);
        load_saved_layout(); // Revert changes
    });

    $footer.find('#btn-save-shortcuts').on('click', function () {
        save_layout();
        toggle_edit_mode(false);
    });

    $footer.find('#btn-reset-layout').on('click', function () {
        frappe.confirm('¿Estás seguro de que quieres restablecer el diseño original?', function () {
            reset_layout();
        });
    });

    function toggle_edit_mode(enable) {
        is_edit_mode = enable;

        let $editBtn = $footer.find('#btn-edit-interface');
        let $editButtons = $footer.find('.edit-mode-buttons');

        if (enable) {
            $container.addClass('edit-mode');
            $editBtn.addClass('hidden');
            $editButtons.removeClass('hidden');

            // Add enhanced resize handles if they don't exist
            $container.find('.shortcut-card').each(function () {
                if ($(this).find('.resize-handle-btn').length === 0) {
                    $('<div class="resize-handle-btn" title="Cambiar tamaño"><i class="fa fa-expand"></i></div>')
                        .appendTo(this)
                        .on('click', function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            $(this).parent().toggleClass('large');
                        });
                }
            });

            enable_drag_and_drop();
        } else {
            $container.removeClass('edit-mode');
            $editBtn.removeClass('hidden');
            $editButtons.addClass('hidden');

            disable_drag_and_drop();
        }
    }

    function reset_layout() {
        localStorage.removeItem('endersuite_sales_dashboard_layout_v4');
        frappe.show_alert({ message: 'Diseño restablecido. Recargando...', indicator: 'orange' });
        setTimeout(() => {
            location.reload();
        }, 1000);
    }

    function enable_drag_and_drop() {
        // Check if Sortable is loaded
        if (typeof Sortable === 'undefined') {
            frappe.require('https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.14.0/Sortable.min.js', function () {
                init_sortables();
            });
        } else {
            init_sortables();
        }
    }

    function init_sortables() {
        // Shortcuts (Icons) ONLY
        $container.find('.shortcut-grid').each(function () {
            let sortable = new Sortable(this, {
                group: 'shortcuts',
                animation: 300,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag'
            });
            sortables.push(sortable);
        });
    }

    function disable_drag_and_drop() {
        sortables.forEach(s => s.destroy());
        sortables = [];
    }

    function save_layout() {
        let layout = {
            grids: {}
        };

        // Save Grids (Shortcuts)
        $container.find('.shortcut-grid').each(function () {
            let id = $(this).attr('id');
            if (id) {
                let $clone = $(this).clone();
                $clone.find('.resize-handle-btn').remove();
                layout.grids[id] = $clone.html();
            }
        });

        localStorage.setItem('endersuite_sales_dashboard_layout_v4', JSON.stringify(layout));
        frappe.show_alert({ message: 'Diseño guardado exitosamente', indicator: 'green' });
    }

    function load_saved_layout() {
        let saved = localStorage.getItem('endersuite_sales_dashboard_layout_v4');
        if (saved) {
            try {
                let layout = JSON.parse(saved);

                // Restore Grids (Shortcuts content)
                if (layout.grids) {
                    for (let id in layout.grids) {
                        let $grid = $container.find('#' + id);
                        if ($grid.length) {
                            $grid.html(layout.grids[id]);
                        }
                    }
                    // but let's do it to ensure latest shortcut states if we decide to separate them later.
                    // Actually, if we restored columns, we restored the grid HTML as it was when saved.
                    // So we don't strictly need to restore grids separately unless we want to mix-and-match.
                    // Let's stick to restoring columns for section order.

                    // However, we need to re-bind the resize handles if we are in edit mode? 
                    // No, load happens on page load, edit mode is off.

                }
            } catch (e) {
                console.error("Error loading layout:", e);
            }
        }
    }
}
