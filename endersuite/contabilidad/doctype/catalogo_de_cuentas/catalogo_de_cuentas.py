# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class CatalogodeCuentas(NestedSet):
	DEFAULT_ROOTS = ["Activo", "Pasivo", "Ingreso", "Gasto", "Capital"]

	def on_trash(self):
		"""Impide eliminar grupos raíz protegidos (protected_root=1)."""
		if self.get("protected_root"):
			frappe.throw(
				frappe._("No se puede eliminar el grupo por defecto: {0}").format(self.cuenta or self.name)
			)

	def validate(self):
		"""Enforce protection rules for default roots: only 'cuenta' can change.

		- Siempre mantener is_group = 1
		- Siempre mantener parent vacío (raíz)
		- Si existe el campo 'disabled', mantenerlo en 0
		"""
		if self.get("protected_root"):
			# force constraints regardless of attempted edits
			self.is_group = 1
			if hasattr(self, "disabled"):
				try:
					self.disabled = 0
				except Exception:
					pass
			# keep as root
			self.set("parent_catalogo_de_cuentas", "")


def create_default_groups(ignore_permissions=True):
	"""Create default root groups in the Chart of Accounts if they don't exist.

	This creates persistent `Catalogo de Cuentas` documents with `is_group=1`.
	It is safe to call multiple times.
	"""
	from frappe import _

	doctype = "Catalogo de Cuentas"
	parent_field = "parent_catalogo_de_cuentas"

	for name in CatalogodeCuentas.DEFAULT_ROOTS:
		if not frappe.db.exists(doctype, name):
			# Create new protected root
			doc = frappe.get_doc({
				"doctype": doctype,
				# Use 'cuenta' as title/name source per DocType autoname
				"cuenta": name,
				"is_group": 1,
				parent_field: "",
				"protected_root": 1,
			})
			doc.insert(ignore_permissions=ignore_permissions)
		else:
			# Ensure existing root has protection and constraints
			doc = frappe.get_doc(doctype, name)
			doc.is_group = 1
			doc.set(parent_field, "")
			if hasattr(doc, "disabled"):
				try:
					doc.disabled = 0
				except Exception:
					pass
			# set protection flag if missing
			if not doc.get("protected_root"):
				doc.set("protected_root", 1)
			doc.save(ignore_permissions=ignore_permissions)

	# Ensure default children for 'Capital'
	if frappe.db.exists(doctype, "Capital"):
		capital = frappe.get_doc(doctype, "Capital")
		for child_name in ("Capital Contable", "Capital Social"):
			if not frappe.db.exists(doctype, child_name):
				child = frappe.get_doc({
					"doctype": doctype,
					"cuenta": child_name,
					"is_group": 1,
					parent_field: capital.name,
					# explicitly ensure these are NOT protected
					"protected_root": 0,
				})
				child.insert(ignore_permissions=ignore_permissions)
			else:
				child = frappe.get_doc(doctype, child_name)
				# If exists, make sure it's under Capital and editable
				child.is_group = 1
				child.set(parent_field, capital.name)
				if child.get("protected_root"):
					child.set("protected_root", 0)
				child.save(ignore_permissions=ignore_permissions)


@frappe.whitelist()
def get_children(doctype, parent="", include_disabled=False, **filters):
	"""Devuelve hijos para la vista de árbol. Si no hay nodos raíz, devuelve subgrupos por defecto.

	Esta función refleja el comportamiento de `frappe.desk.treeview._get_children` pero
	inyecta cuatro subgrupos raíz por defecto cuando el árbol está vacío: "Activos",
	"Pasivos", "Ingresos" y "Egresos". Los nodos por defecto se devuelven como
	expandibles (no se crean registros en la base de datos).
	"""
	# normalize include_disabled
	if isinstance(include_disabled, str):
		include_disabled = frappe.sbool(include_disabled)

	parent_field = "parent_" + frappe.scrub(doctype)
	filters_list = [[f"ifnull(`{parent_field}`,'')", "=", parent], ["docstatus", "<", 2]]

	if frappe.db.has_column(doctype, "disabled") and not include_disabled:
		filters_list.append(["disabled", "=", False])

	meta = frappe.get_meta(doctype)

	children = frappe.get_list(
		doctype,
		fields=[
			"name as value",
			"{} as title".format(meta.get("title_field") or "name"),
			"is_group as expandable",
		],
		filters=filters_list,
		order_by="name",
		ignore_permissions=True,
	)

	# Si estamos en raíz y no hay registros persistentes, devolver subgrupos por defecto
	if (parent in (None, "")) and len(children) == 0:
		defaults = []
		for name in ["Activo", "Pasivo", "Ingreso", "Gasto", "Capital"]:
			defaults.append({
				"value": name,
				"title": name,
				"expandable": True,
			})
		return defaults

	# Si el padre es 'Capital' y no hay hijos persistentes, devolver sugeridos
	if parent == "Capital" and len(children) == 0:
		return [
			{"value": "Capital Contable", "title": "Capital Contable", "expandable": True},
			{"value": "Capital Social", "title": "Capital Social", "expandable": True},
		]

	return children
