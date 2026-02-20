import frappe
from datetime import date


def ensure_fiscal_year(year: int, company: str | None = None, make_default: bool = True) -> str:
    """Ensure an "Anio Fiscal" document exists for the given year.

    Args:
        year: Gregorian year (e.g. 2025)
        company: Optional name of "Compania" to link.
        make_default: If True, set flags es_por_defecto=1 and estado="Abierto".
    Returns:
        Name ("nombre") of the fiscal year document.
    """
    nombre = str(year)

    existing = frappe.get_all("Anio Fiscal", filters={"nombre": nombre}, pluck="name")
    if existing:
        return existing[0]

    fy_doc = frappe.get_doc({
        "doctype": "Anio Fiscal",
        "nombre": nombre,
        "desde": f"{year}-01-01",
        "hasta": f"{year}-12-31",
        "empresa": company or "",
        "es_por_defecto": 1 if make_default else 0,
        "estado": "Abierto" if make_default else "Borrador",
    })
    fy_doc.insert(ignore_permissions=True)
    return fy_doc.name


def ensure_current_fiscal_year_for_company(company: str) -> str:
    """Ensure current year fiscal year exists and is linked to given company."""
    current_year = date.today().year
    return ensure_fiscal_year(current_year, company=company, make_default=True)


def ensure_current_fiscal_year_daily():
    """Daily task: ensure current fiscal year exists for every company."""
    companies = frappe.get_all("Compania", pluck="name")
    for comp in companies:
        ensure_current_fiscal_year_for_company(comp)


def ensure_catalogo_for_company(company: str | None = None, nombre_catalogo: str | None = None, initials: str | None = None) -> str:
    """Create or get a Catalogo record.

    Args:
        company: Optional Compania name to link later; creation does not require it.
        nombre_catalogo: Optional explicit name for catalog; defaults to a readable pattern
        initials: Company initials for pattern [Iniciales] - Catalogo de Cuentas
    Returns:
        Name of Catalogo document
    """
    if not nombre_catalogo:
        if initials:
            nombre_catalogo = f"{initials} - Catalogo de Cuentas"
        elif company:
            nombre_catalogo = f"Catálogo {company}"
        else:
            nombre_catalogo = "Catálogo Principal"

    existing = frappe.get_all("Catalogo", filters={"nombre_del_catalogo": nombre_catalogo}, pluck="name")
    if existing:
        return existing[0]

    # Don't set link field 'compañia' here unless it truly exists; we'll attach after creating Compania
    cat = frappe.get_doc({
        "doctype": "Catalogo",
        "nombre_del_catalogo": nombre_catalogo,
    })
    cat.insert(ignore_permissions=True)
    return cat.name


def bootstrap_chart_of_accounts_if_empty():
    """Bootstrap de cuentas raíz por catálogo si no existe ninguna cuenta."""
    count = frappe.db.count("Cuenta")
    if count == 0:
        from endersuite.contabilidad.doctype.cuenta.cuenta import ensure_roots_for_catalogo
        catalogs = frappe.get_all("Catalogo", pluck="name")
        for c in catalogs:
            ensure_roots_for_catalogo(c)


def setup_company_defaults(company_name: str, initials: str) -> str:
    """Create Compania + related Fiscal Year + Catalogo records if missing.

    Returns name of Compania document.
    """
    # Try existing by initials (autoname rule)
    existing = frappe.db.exists("Compania", initials)
    if existing:
        comp = frappe.get_doc("Compania", initials)
    else:
        # Ensure fiscal year first (no company link yet to avoid link validation)
        fiscal_year_name = ensure_fiscal_year(date.today().year, company=None, make_default=True)
        catalogo_name = ensure_catalogo_for_company(None, initials=initials)

        comp = frappe.get_doc({
            "doctype": "Compania",
            "nombre_de_la_empresa": company_name,
            "iniciales_de_la_empresa": initials,
            # Field names with accent must be dict-style
            "año_fiscal": fiscal_year_name,
            "catalogo": catalogo_name,
        })
        comp.insert(ignore_permissions=True)

        # Attach catalogo to company now that Compania exists
        try:
            cat_doc = frappe.get_doc("Catalogo", catalogo_name)
            cat_doc.set("compañia", comp.name)
            cat_doc.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(title="No se pudo asignar Catalogo a la Compania")

        # Attach fiscal year's 'empresa' link now that Compania exists
        try:
            fy_doc = frappe.get_doc("Anio Fiscal", fiscal_year_name)
            fy_doc.set("empresa", comp.name)
            fy_doc.save(ignore_permissions=True)
        except Exception:
            frappe.log_error(title="No se pudo asignar Año Fiscal a la Compania")

    # Ensure chart of accounts bootstrap (global)
    bootstrap_chart_of_accounts_if_empty()

    return comp.name
