import frappe
from datetime import date
from frappe.utils.password import set_encrypted_password


def after_install():
	"""Hook que corre después de instalar la app.

	Acciones:
	- Crear grupos raíz del Catálogo de Cuentas (solo si no existen)
	- Crear año fiscal del año actual (para que esté disponible en el wizard)
	- Importar traducciones ES
	"""
	from endersuite.contabilidad.fiscal_utils import bootstrap_chart_of_accounts_if_empty, ensure_fiscal_year

	bootstrap_chart_of_accounts_if_empty()
	
	# Crear año fiscal actual para que esté disponible en el Setup Wizard
	current_year = date.today().year
	ensure_fiscal_year(current_year, company=None, make_default=True)

	# Importar traducciones ES si existe archivo (import dinámico para evitar warnings de análisis)
	try:
		import importlib, os
		mod = importlib.import_module("frappe.translate")
		import_translations = getattr(mod, "import_translations", None)
		path = frappe.get_app_path("endersuite", "translations", "es.csv")
		if import_translations and os.path.exists(path):
			import_translations("es", path)
	except Exception:
		frappe.log_error(title="Error importing translations for endersuite")
	
	# Configurar PAC con credenciales pre-configuradas
	setup_pac_configuration()

	frappe.db.commit()


def setup_wizard_complete(args):
	"""Se ejecuta al finalizar el Setup Wizard del sitio.

	Aquí creamos automáticamente:
	- Registro de Compania
	- Año Fiscal del año actual (si no existe) y lo marcamos como por defecto
	- Catalogo (catálogo contable) ligado a la compañía
	- Grupos raíz del catálogo (Activo, Pasivo, Capital, Ingreso, Gasto) dentro del catálogo creado

	`args` contiene los valores ingresados en el wizard estándar de Frappe. Si se añade
	un paso personalizado se pueden mapear campos propios.
	"""
	print("\n=== INICIO setup_wizard_complete ===")
	print(f"Args recibidos: {args}")
	
	company_name = args.get("nombre_de_la_empresa") or args.get("company_name")
	company_abbr = args.get("iniciales_de_la_empresa") or args.get("company_abbr")

	print(f"Company Name: {company_name}")
	print(f"Company Abbr: {company_abbr}")

	if not company_name or not company_abbr:
		# Si el wizard no proporcionó datos (p.ej. instalación headless), no hacemos nada.
		print("No hay datos de compañía, saliendo...")
		return

	# Obtener campos obligatorios de Compania
	rfc = args.get("rfc")
	tipo_de_persona = args.get("tipo_de_persona")
	regimen_fiscal = args.get("regimen_fiscal")

	print(f"RFC: {rfc}")
	print(f"Tipo de Persona: {tipo_de_persona}")
	print(f"Régimen Fiscal: {regimen_fiscal}")

	# Validar que los campos obligatorios estén presentes
	if not rfc:
		frappe.throw("El RFC es obligatorio para crear la compañía")
	if not tipo_de_persona:
		frappe.throw("El Tipo de Persona es obligatorio para crear la compañía")
	if not regimen_fiscal:
		frappe.throw("El Régimen Fiscal es obligatorio para crear la compañía")

	from endersuite.contabilidad.fiscal_utils import (
		ensure_fiscal_year,
		ensure_catalogo_for_company,
		bootstrap_chart_of_accounts_if_empty,
	)

	# Obtener año fiscal desde args (viene del wizard personalizado)
	fiscal_year_name = args.get("ano_fiscal") or str(date.today().year)
	print(f"Año Fiscal: {fiscal_year_name}")
	

	# Crear catálogo con formato "Nombre de compañía - Catalogo de Cuentas"
	catalogo_nombre = f"{company_name} - Catalogo de Cuentas"
	catalogo_name = None
	print(f"\nCreando Catálogo: {catalogo_nombre}")
	
	existing_catalogo = frappe.get_all("Catalogo", filters={"nombre_del_catalogo": catalogo_nombre}, pluck="name")
	if existing_catalogo:
		catalogo_name = existing_catalogo[0]
		print(f"Catálogo ya existe: {catalogo_name}")
	else:
		cat_doc = frappe.get_doc({
			"doctype": "Catalogo",
			"nombre_del_catalogo": catalogo_nombre,
		})
		cat_doc.insert(ignore_permissions=True)
		catalogo_name = cat_doc.name
		print(f"Catálogo creado: {catalogo_name}")
		# Hacer commit para que el Catalogo esté disponible antes de crear la Compania
		frappe.db.commit()
		print("Commit realizado para Catálogo")

	# Crear / asegurar compañía (autoname usa iniciales)
	print(f"\nCreando Compañía: {company_name}")
	existing = frappe.db.exists("Compania", company_abbr)
	if existing:
		comp = frappe.get_doc("Compania", company_abbr)
		print(f"Compañía ya existe: {comp.name}")
	else:
		comp = frappe.get_doc({
			"doctype": "Compania",
			"nombre_de_la_empresa": company_name,
			"iniciales_de_la_empresa": company_abbr,
			"anio_fiscal": fiscal_year_name,
			"catalogo": catalogo_name,	
			"rfc": rfc,
			"tipo_de_persona": tipo_de_persona,
			"regimen_fiscal": regimen_fiscal,
		})
		comp.insert(ignore_permissions=True)
		print(f"Compañía creada: {comp.name}")

	# Asociar el Año Fiscal a la compañía creada
	print(f"\nAsociando Año Fiscal {fiscal_year_name} a la compañía...")
	try:
		fy_doc = frappe.get_doc("Anio Fiscal", fiscal_year_name)
		fy_doc.set("empresa", comp.name)
		fy_doc.save(ignore_permissions=True)
		print(f"Año Fiscal actualizado correctamente")
	except Exception as e:
		print(f"Error al asignar Año Fiscal: {str(e)}")
		frappe.log_error(title="No se pudo asignar Año Fiscal a la Compania en setup_wizard_complete")

	# Vincular catálogo a la compañía ahora que existe
	print(f"\nVinculando Catálogo a la compañía...")
	try:
		cat_doc = frappe.get_doc("Catalogo", catalogo_name)
		cat_doc.set("compañia", comp.name)
		cat_doc.save(ignore_permissions=True)
		print(f"Catálogo vinculado correctamente")
	except Exception as e:
		print(f"Error al vincular Catálogo: {str(e)}")
		frappe.log_error(title="No se pudo asignar Catalogo a la Compania en setup_wizard_complete")

	# Inicializar cuentas raíz usando nuevo DocType Cuenta
	print(f"\nInicializando cuentas raíz para el catálogo...")
	from endersuite.contabilidad.doctype.cuenta.cuenta import ensure_roots_for_catalogo
	ensure_roots_for_catalogo(catalogo_name)
	print(f"Cuentas raíz creadas")
	
	frappe.db.commit()
	print("Commit final realizado")

	# Opcional: devolver información de lo creado (para logs)
	result = {
		"compania": comp.name,
		"año_fiscal": fiscal_year_name,
		"catalogo": catalogo_name,
	}
	print(f"\nResultado final: {result}")
	print("=== FIN setup_wizard_complete ===\n")
	return result


def setup_pac_configuration():
	"""Configura automáticamente las credenciales del PAC en la instalación"""
	import base64
	
	try:
		# Verifica si ya existe la configuración
		if frappe.db.exists("Configuracion PAC", "Configuracion PAC"):
			return
		
		# Credenciales originales (para referencia interna)
		cuenta_original = "rendercores"
		api_key_original = "994362ed2e7a44a79a689f6e433894c0"
		
		# Codifica en base64 para almacenamiento visible pero ofuscado
		cuenta_encoded = base64.b64encode(cuenta_original.encode()).decode()
		api_key_encoded = base64.b64encode(api_key_original.encode()).decode()
		
		# Crea la configuración con credenciales encriptadas en base64
		config = frappe.get_doc({
			"doctype": "Configuracion PAC",
			"nombre_pac": "FacturAPI",
			"modo": "Pruebas",
			"activo": 1,
			"cuenta": cuenta_encoded,  # "cmVuZGVyY29yZXM="
			"api_key": api_key_encoded,  # "OTk0MzYyZWQyZTdhNDRhNzlhNjg5ZjZlNDMzODk0YzA="
			"url_timbrado_json": "https://dev.facturaloplus.com/api/rest/servicio/timbrarJSON2",
			"url_timbrado_xml": "https://dev.facturaloplus.com/api/rest/servicio/timbrar",
			"rfc_pruebas": "EKU9003173C9",
			"regimen_fiscal_pruebas": "601",
			"nombre_pruebas": "ESCUELA KEMPER URGATE",
			"certificado_numero_pruebas": "30001000000500003416"
		})
		config.insert(ignore_permissions=True)
		
		frappe.db.commit()
		
		frappe.logger().info("Configuración PAC creada exitosamente con credenciales encriptadas")
	except Exception as e:
		frappe.log_error(f"Error al configurar PAC: {str(e)}", "Setup PAC Error")
