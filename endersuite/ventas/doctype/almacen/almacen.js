// Copyright (c) 2025, RenderCores.com and contributors
// For license information, please see license.txt

frappe.ui.form.on("Almacen", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.trigger("render_movimientos");
        }
    },

    render_movimientos(frm) {
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Movimiento de Stock",
                filters: {
                    almacen: frm.doc.name
                },
                fields: ["name", "fecha", "tipo_movimiento", "referencia", "estado", "usuario"],
                order_by: "fecha desc"
            },
            callback: function (r) {
                let html = `
					<div class="frappe-list">
						<div class="result">
							<table class="table table-bordered table-hover">
								<thead>
									<tr>
										<th>${__("Fecha")}</th>
										<th>${__("Movimiento")}</th>
										<th>${__("Tipo")}</th>
										<th>${__("Referencia")}</th>
										<th>${__("Estado")}</th>
										<th>${__("Usuario")}</th>
									</tr>
								</thead>
								<tbody>
				`;

                if (r.message && r.message.length > 0) {
                    r.message.forEach(row => {
                        html += `
							<tr>
								<td>${frappe.datetime.str_to_user(row.fecha)}</td>
								<td><a href="/app/movimiento-de-stock/${row.name}">${row.name}</a></td>
								<td>${row.tipo_movimiento}</td>
								<td>${row.referencia || ""}</td>
								<td>${row.estado}</td>
								<td>${row.usuario}</td>
							</tr>
						`;
                    });
                } else {
                    html += `<tr><td colspan="6" class="text-center text-muted">${__("No hay movimientos registrados")}</td></tr>`;
                }

                html += `
								</tbody>
							</table>
						</div>
					</div>
				`;

                frm.set_df_property("movimientos_html", "options", html);
            }
        });
    }
});

