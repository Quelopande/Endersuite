import frappe
from frappe.utils.nestedset import NestedSet


class Cuenta(NestedSet):
    DEFAULT_ROOTS = ["Activo", "Pasivo", "Capital", "Ingreso", "Gasto"]

    def on_trash(self, allow_root_deletion: bool = False):
        """Impide eliminar cuentas raíz protegidas."""
        if self.get("protected_root") and not allow_root_deletion:
            frappe.throw(frappe._("No se puede eliminar el grupo por defecto: {0}").format(self.get("cuenta") or self.name))

    def validate(self):
        """Enforce invariants para raíces protegidas."""
        if self.get("protected_root"):
            self.set("is_group", 1)
            self.set("parent_cuenta", "")  # mantener como raíz
            if hasattr(self, "disabled"):
                try:
                    self.disabled = 0
                except Exception:
                    pass


def ensure_roots_for_catalogo(catalogo_name: str, ignore_permissions: bool = True):
    """Asegura que existan las cuentas raíz por catálogo.

    Se crea una copia independiente de cada grupo raíz por cada catálogo.
    """
    doctype = "Cuenta"
    parent_field = "parent_cuenta"

    for root in Cuenta.DEFAULT_ROOTS:
        existing_name = frappe.db.get_value(doctype, {"cuenta": root, "catalogo": catalogo_name, parent_field: ""}, "name")
        if not existing_name:
            doc = frappe.get_doc({
                "doctype": doctype,
                "cuenta": root,
                "catalogo": catalogo_name,
                "is_group": 1,
                parent_field: "",
                "protected_root": 1,
            })
            doc.insert(ignore_permissions=ignore_permissions)
        else:
            existing_name_str = existing_name if isinstance(existing_name, str) else str(existing_name)
            d = frappe.get_doc(doctype, existing_name_str)
            d.set("is_group", 1)
            d.set(parent_field, "")
            if not d.get("protected_root"):
                d.set("protected_root", 1)
            d.save(ignore_permissions=ignore_permissions)

    # Hijos sugeridos para Capital
    capital_name = frappe.db.get_value(doctype, {"cuenta": "Capital", "catalogo": catalogo_name, parent_field: ""}, "name")
    if capital_name:
        for child in ("Capital Contable", "Capital Social"):
            existing_child_name = frappe.db.get_value(doctype, {"cuenta": child, "catalogo": catalogo_name}, "name")
            if not existing_child_name:
                child_doc = frappe.get_doc({
                    "doctype": doctype,
                    "cuenta": child,
                    "catalogo": catalogo_name,
                    "is_group": 1,
                    parent_field: capital_name,
                    "protected_root": 0,
                })
                child_doc.insert(ignore_permissions=ignore_permissions)
            else:
                existing_child_name_str = existing_child_name if isinstance(existing_child_name, str) else str(existing_child_name)
                c = frappe.get_doc(doctype, existing_child_name_str)
                c.set("is_group", 1)
                c.set(parent_field, capital_name)
                if c.get("protected_root"):
                    c.set("protected_root", 0)
                c.save(ignore_permissions=ignore_permissions)


@frappe.whitelist()
def get_children(doctype, parent="", include_disabled=False, catalogo=None, **filters):
    """Tree fetch adaptado para Cuenta por catálogo.

    Si no hay nodos y estamos en raíz, devuelve valores por defecto.
    """
    if doctype != "Cuenta":
        return []

    if isinstance(include_disabled, str):
        include_disabled = frappe.sbool(include_disabled)

    # Si no se especifica catálogo, obtener el de la compañía por defecto
    if not catalogo:
        default_company = frappe.defaults.get_user_default("Company")
        if default_company:
            catalogo = frappe.db.get_value("Catalogo", {"compania": default_company}, "name")
        
        if not catalogo:
            # Si aún no hay catálogo, obtener el primero disponible
            catalogo = frappe.db.get_value("Catalogo", {}, "name")
        
        if not catalogo:
            return []

    parent_field = "parent_cuenta"
    filters_list = [[f"ifnull(`{parent_field}`,'')", "=", parent], ["docstatus", "<", 2]]
    filters_list.append(["catalogo", "=", catalogo])

    if frappe.db.has_column(doctype, "disabled") and not include_disabled:
        filters_list.append(["disabled", "=", False])

    meta = frappe.get_meta(doctype)
    children = frappe.get_list(
        doctype,
        fields=[
            "name as value",
            "cuenta as title",
            "is_group as expandable",
        ],
        filters=filters_list,
        order_by="cuenta",
        ignore_permissions=True,
    )

    return children
