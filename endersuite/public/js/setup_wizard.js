// Add custom company setup slide to Frappe's Setup Wizard
// This must run BEFORE the setup wizard page loads

frappe.provide("frappe.setup");

// Initialize slides_settings if it doesn't exist yet
if (!frappe.setup.slides_settings) {
	frappe.setup.slides_settings = [];
}

// Push our custom slide configuration
frappe.setup.slides_settings.push({
	name: "company_setup",
	title: __("Configuración de Compañía"),
	icon: "fa fa-building",
	fields: [
		{
			fieldname: "nombre_de_la_empresa",
			label: __("Nombre de la Empresa"),
			fieldtype: "Data",
			reqd: 1
		},
		{
			fieldname: "iniciales_de_la_empresa",
			label: __("Iniciales de la Empresa"),
			fieldtype: "Data",
			reqd: 1
		},
		{
			fieldname: "rfc",
			label: __("RFC"),
			fieldtype: "Data",
			reqd: 1,
			description: __("Registro Federal de Contribuyentes")
		},
		{
			fieldname: "tipo_de_persona",
			label: __("Tipo de Persona"),
			fieldtype: "Select",
			options: "Fisica\nMoral",
			reqd: 1
		},
		{
			fieldname: "regimen_fiscal",
			label: __("Régimen Fiscal"),
			fieldtype: "Select",
			options: [
				"601 REGIMEN GENERAL DE LEY PERSONAS MORALES",
				"602 RÉGIMEN SIMPLIFICADO DE LEY PERSONAS MORALES",
				"603 PERSONAS MORALES CON FINES NO LUCRATIVOS",
				"604 RÉGIMEN DE PEQUEÑOS CONTRIBUYENTES",
				"605 RÉGIMEN DE SUELDOS Y SALARIOS E INGRESOS ASIMILADOS A SALARIOS",
				"606 RÉGIMEN DE ARRENDAMIENTO",
				"607 RÉGIMEN DE ENAJENACIÓN O ADQUISICIÓN DE BIENES",
				"608 RÉGIMEN DE LOS DEMÁS INGRESOS",
				"609 RÉGIMEN DE CONSOLIDACIÓN",
				"610 RÉGIMEN RESIDENTES EN EL EXTRANJERO SIN ESTABLECIMIENTO PERMANENTE EN MÉXICO",
				"611 RÉGIMEN DE INGRESOS POR DIVIDENDOS (SOCIOS Y ACCIONISTAS)",
				"612 RÉGIMEN DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES Y PROFESIONALES",
				"613 RÉGIMEN INTERMEDIO DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES",
				"614 RÉGIMEN DE LOS INGRESOS POR INTERESES",
				"615 RÉGIMEN DE LOS INGRESOS POR OBTENCIÓN DE PREMIOS",
				"616 SIN OBLIGACIONES FISCALES",
				"617 PEMEX",
				"618 RÉGIMEN SIMPLIFICADO DE LEY PERSONAS FÍSICAS",
				"619 INGRESOS POR LA OBTENCIÓN DE PRÉSTAMOS",
				"620 SOCIEDADES COOPERATIVAS DE PRODUCCIÓN QUE OPTAN POR DIFERIR SUS INGRESOS.",
				"621 RÉGIMEN DE INCORPORACIÓN FISCAL",
				"622 RÉGIMEN DE ACTIVIDADES AGRÍCOLAS, GANADERAS, SILVÍCOLAS Y PESQUERAS PM",
				"623 RÉGIMEN DE OPCIONAL PARA GRUPOS DE SOCIEDADES",
				"624 RÉGIMEN DE LOS COORDINADOS",
				"625 RÉGIMEN DE LAS ACTIVIDADES EMPRESARIALES CON INGRESOS A TRAVÉS DE PLATAFORMAS TECNOLÓGICAS.",
				"626 RÉGIMEN SIMPLIFICADO DE CONFIANZA"
			].join("\n"),
			reqd: 1,
			default: "616 SIN OBLIGACIONES FISCALES"
		},
		{
			fieldname: "ano_fiscal",
			label: __("Año Fiscal"),
			fieldtype: "Link",
			options: "Anio Fiscal",
			reqd: 1
		}
	],
	help: __("Configure la información básica de su compañía. El catálogo de cuentas se creará automáticamente."),

	onload: function (slide) {
		// Load fiscal years and set default to current year
		let current_year = new Date().getFullYear().toString();

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Anio Fiscal",
				fields: ["nombre"],
				order_by: "desde desc",
				limit_page_length: 20
			},
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					// Try to find and set current year
					let found = r.message.find(fy => fy.nombre === current_year);
					if (found) {
						slide.get_field("ano_fiscal").set_value(current_year);
					} else if (r.message.length > 0) {
						slide.get_field("ano_fiscal").set_value(r.message[0].nombre);
					}
				}
			}
		});
	}
});
