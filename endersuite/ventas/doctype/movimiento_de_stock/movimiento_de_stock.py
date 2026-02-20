# -*- coding: utf-8 -*-
# Copyright (c) 2024, EnderSuite and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class MovimientodeStock(Document):
	def before_save(self):
		"""Validar antes de guardar"""
		if not self.usuario:
			self.usuario = frappe.session.user
	
	def validate(self):
		"""Validaciones del documento"""
		self.validar_cantidades()
		self.validar_stock_disponible()
	
	def validar_cantidades(self):
		"""Validar que las cantidades sean positivas"""
		for detalle in self.detalles:
			if detalle.cantidad <= 0:
				frappe.throw(_("La cantidad debe ser mayor a cero para el producto {0}").format(detalle.producto))
	
	def validar_stock_disponible(self):
		"""Validar stock disponible para salidas y ajustes negativos"""
		if self.tipo_movimiento in ["Salida", "Ajuste Negativo"]:
			for detalle in self.detalles:
				producto = frappe.get_doc("Producto", detalle.producto)
				
				if not producto.mantener_stock:
					continue
				
				if producto.cantidad_disponible < detalle.cantidad:
					frappe.throw(_("Stock insuficiente para {0}. Disponible: {1}, Requerido: {2}").format(
						producto.nombre_del_producto,
						producto.cantidad_disponible,
						detalle.cantidad
					))
	
	def on_submit(self):
		"""Actualizar stock al enviar el documento"""
		self.actualizar_stock()
		# Actualizar estado sin disparar validaciones
		frappe.db.set_value(self.doctype, self.name, "estado", "Completado")
	
	def on_cancel(self):
		"""Revertir stock al cancelar"""
		self.revertir_stock()
		# Actualizar estado sin disparar validaciones
		frappe.db.set_value(self.doctype, self.name, "estado", "Cancelado")
	
	def actualizar_stock(self):
		"""Actualizar el stock de los productos según el tipo de movimiento"""
		for detalle in self.detalles:
			producto = frappe.get_doc("Producto", detalle.producto)
			
			if not producto.mantener_stock:
				continue
			
			cantidad_anterior = producto.cantidad_disponible
			
			if self.tipo_movimiento in ["Entrada", "Ajuste Positivo"]:
				producto.cantidad_disponible += detalle.cantidad
			elif self.tipo_movimiento in ["Salida", "Ajuste Negativo"]:
				producto.cantidad_disponible -= detalle.cantidad
			
			producto.save(ignore_permissions=True)

			# Emitir evento de actualización de stock en tiempo real
			frappe.publish_realtime(
				event='stock_updated',
				message={
					'producto': detalle.producto,
					'almacen': self.almacen,
					'cantidad_disponible': producto.cantidad_disponible,
					'tipo_movimiento': self.tipo_movimiento
				},
				doctype='Producto',
				docname=detalle.producto
			)

			# Registrar log del cambio
			frappe.logger().info(
				f"Movimiento de Stock: {self.name} | "
				f"Producto: {producto.nombre_del_producto} | "
				f"Tipo: {self.tipo_movimiento} | "
				f"Cantidad: {detalle.cantidad} | "
				f"Stock Anterior: {cantidad_anterior} | "
				f"Stock Nuevo: {producto.cantidad_disponible}"
			)
			
			# Actualizar lotes si aplica
			if detalle.lote:
				self.actualizar_lote(detalle)
			
			# Actualizar series si aplica
			if detalle.serie:
				self.actualizar_serie(detalle)
	
	def revertir_stock(self):
		"""Revertir los cambios en el stock"""
		for detalle in self.detalles:
			producto = frappe.get_doc("Producto", detalle.producto)
			
			if not producto.mantener_stock:
				continue
			
			# Invertir el movimiento
			if self.tipo_movimiento in ["Entrada", "Ajuste Positivo"]:
				producto.cantidad_disponible -= detalle.cantidad
			elif self.tipo_movimiento in ["Salida", "Ajuste Negativo"]:
				producto.cantidad_disponible += detalle.cantidad
			
			producto.save(ignore_permissions=True)
			
			# Revertir lotes
			if detalle.lote:
				self.revertir_lote(detalle)
			
			# Revertir series
			if detalle.serie:
				self.revertir_serie(detalle)
	
	def actualizar_lote(self, detalle):
		"""Actualizar cantidad en lote"""
		if not frappe.db.exists("Lote", detalle.lote):
			return
		
		lote = frappe.get_doc("Lote", detalle.lote)
		
		if self.tipo_movimiento in ["Entrada", "Ajuste Positivo"]:
			lote.cantidad_disponible += detalle.cantidad
		elif self.tipo_movimiento in ["Salida", "Ajuste Negativo"]:
			lote.cantidad_disponible -= detalle.cantidad
		
		lote.save(ignore_permissions=True)
	
	def revertir_lote(self, detalle):
		"""Revertir cambios en lote"""
		if not frappe.db.exists("Lote", detalle.lote):
			return
		
		lote = frappe.get_doc("Lote", detalle.lote)
		
		if self.tipo_movimiento in ["Entrada", "Ajuste Positivo"]:
			lote.cantidad_disponible -= detalle.cantidad
		elif self.tipo_movimiento in ["Salida", "Ajuste Negativo"]:
			lote.cantidad_disponible += detalle.cantidad
		
		lote.save(ignore_permissions=True)
	
	def actualizar_serie(self, detalle):
		"""Actualizar estado de serie"""
		if not frappe.db.exists("Serie", detalle.serie):
			return
		
		serie = frappe.get_doc("Serie", detalle.serie)
		
		if self.tipo_movimiento == "Entrada":
			serie.estado = "Disponible"
		elif self.tipo_movimiento == "Salida":
			serie.estado = "Vendido"
		
		serie.save(ignore_permissions=True)
	
	def revertir_serie(self, detalle):
		"""Revertir estado de serie"""
		if not frappe.db.exists("Serie", detalle.serie):
			return
		
		serie = frappe.get_doc("Serie", detalle.serie)
		
		if self.tipo_movimiento == "Entrada":
			serie.estado = "Dañado"  # O el estado anterior
		elif self.tipo_movimiento == "Salida":
			serie.estado = "Disponible"
		
		serie.save(ignore_permissions=True)
