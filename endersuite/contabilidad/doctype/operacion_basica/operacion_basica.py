# Copyright (c) 2025, RenderCores.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class OperacionBasica(Document):
	def validate(self):
		# Validar monto positivo
		if self.monto <= 0:
			frappe.throw(_("El monto debe ser mayor a cero"))

	def on_submit(self):
		# Al enviar (Submit), se crean los asientos
		self.crear_asientos_contables()

	def on_cancel(self):
		# Al cancelar, se revierten los asientos
		self.ignore_linked_doctypes = ('GL Entry', 'Stock Ledger Entry')
		make_gl_entries(self.name, cancel=True)

	def crear_asientos_contables(self):
		gl_entries = []
		
		# CORRECCIÓN: Usamos 'self.compania' en lugar de self.company
		moneda_empresa = frappe.get_cached_value('Company',  self.compania,  'default_currency')

		# CORRECCIÓN: Nombre del DocType actualizado a "Categoria de Operacion"
		tipo_operacion = frappe.db.get_value("Categoria de Operacion", self.categoria, "tipo")

		# Lógica de Partida Doble
		if tipo_operacion == "Gasto":
			# GASTO: Debe (+) Cuenta Destino / Haber (-) Cuenta Pago
			cuenta_debe = self.cuenta_destino
			cuenta_haber = self.cuenta_pago
		else:
			# INGRESO: Debe (+) Cuenta Pago / Haber (-) Cuenta Destino
			cuenta_debe = self.cuenta_pago
			cuenta_haber = self.cuenta_destino

		# 1. Crear linea del DEBE
		gl_entries.append(
			self.get_gl_dict({
				"account": cuenta_debe,
				"debit": self.monto,
				"credit": 0,
				"debit_in_account_currency": self.monto,
				"credit_in_account_currency": 0,
				"against": cuenta_haber
			}, moneda_empresa)
		)

		# 2. Crear linea del HABER
		gl_entries.append(
			self.get_gl_dict({
				"account": cuenta_haber,
				"debit": 0,
				"credit": self.monto,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": self.monto,
				"against": cuenta_debe,
			}, moneda_empresa)
		)

		make_gl_entries(gl_entries, cancel=(self.docstatus == 2))

	def get_gl_dict(self, args, moneda_empresa):
		return frappe._dict({
			"account": args.get("account"),
			"party_type": "",
			"party": "",
			# CORRECCIÓN: Mapeamos tu campo 'compania' al campo interno 'company' que exige Frappe
			"company": self.compania, 
			"posting_date": self.posting_date,
			"currency": moneda_empresa,
			"debit": args.get("debit"),
			"credit": args.get("credit"),
			"debit_in_account_currency": args.get("debit_in_account_currency"),
			"credit_in_account_currency": args.get("credit_in_account_currency"),
			"against": args.get("against"),
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"remarks": self.observaciones or "Operación Básica"
		})
