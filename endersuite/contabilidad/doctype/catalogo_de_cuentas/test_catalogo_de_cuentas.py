# Copyright (c) 2025, RenderCores.com and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


# On IntegrationTestCase, the doctype test records and all
# link-field test record dependencies are recursively loaded
# Use these module variables to add/remove to/from that list
EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]



class IntegrationTestCatalogodeCuentas(IntegrationTestCase):
	"""
	Integration tests for CatalogodeCuentas.
	"""

	def test_after_install_creates_default_groups(self):
		from endersuite.contabilidad.doctype.catalogo_de_cuentas.catalogo_de_cuentas import (
			create_default_groups,
			CatalogodeCuentas,
		)

		# Ensure default groups are created
		create_default_groups()

		for name in CatalogodeCuentas.DEFAULT_ROOTS:
			doc = frappe.get_doc("Catalogo de Cuentas", name)
			self.assertTrue(doc)
			self.assertEqual(doc.is_group, 1)
			self.assertEqual(doc.get("protected_root"), 1)

		# Check default children under Capital
		cap = frappe.get_doc("Catalogo de Cuentas", "Capital")
		for child in ("Capital Contable", "Capital Social"):
			cdoc = frappe.get_doc("Catalogo de Cuentas", child)
			self.assertEqual(cdoc.parent_catalogo_de_cuentas, cap.name)
			self.assertEqual(cdoc.is_group, 1)
			self.assertNotEqual(cdoc.get("protected_root"), 1)

	def test_default_groups_cannot_be_deleted(self):
		from endersuite.contabilidad.doctype.catalogo_de_cuentas.catalogo_de_cuentas import (
			create_default_groups,
			CatalogodeCuentas,
		)

		create_default_groups()

		name = CatalogodeCuentas.DEFAULT_ROOTS[0]
		doc = frappe.get_doc("Catalogo de Cuentas", name)

		with self.assertRaises(frappe.ValidationError):
			doc.delete()

	def test_protected_roots_only_allow_name_change(self):
		from endersuite.contabilidad.doctype.catalogo_de_cuentas.catalogo_de_cuentas import (
			create_default_groups,
			CatalogodeCuentas,
		)

		create_default_groups()

		name = CatalogodeCuentas.DEFAULT_ROOTS[1]
		doc = frappe.get_doc("Catalogo de Cuentas", name)

		# Try to change restricted fields
		doc.is_group = 0
		doc.parent_catalogo_de_cuentas = "Some Parent"
		if hasattr(doc, "disabled"):
			doc.disabled = 1
		doc.save()

		# Reload and assert restrictions enforced
		doc.reload()
		self.assertEqual(doc.is_group, 1)
		self.assertIn(doc.name, CatalogodeCuentas.DEFAULT_ROOTS)
		self.assertFalse(doc.get("parent_catalogo_de_cuentas"))
		if hasattr(doc, "disabled"):
			self.assertEqual(doc.disabled, 0)
