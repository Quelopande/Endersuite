# Módulo de Cotizaciones (Quotation)

Este documento describe la implementación del DocType `Cotizacion` en Frappe, diseñado para crear ofertas de precios formales y "submittable" (confirmables) para clientes.

## 📝 Descripción General

El objetivo de esta implementación es crear un flujo de ventas donde un usuario pueda generar una **Cotización**, agregarle artículos con precios, y que el sistema calcule automáticamente los importes de fila y los totales generales del documento.

## 🏗️ Componentes del Sistema

Para lograr esto, se crearon los siguientes componentes:

### 1. DocType: `Cotizacion`
Es el documento principal y "Submittable". Contiene la información de cabecera.

* **Naturaleza:** Submittable (Maneja `docstatus` 0, 1, 2).
* **Campos Clave:**
    * `cliente` (Link a Cliente)
    * `fecha_de_cotizacion` (Date)
    * `valido_hasta` (Date)
    * `estado` (Select)
    * `items` (Tipo `Table` enlazado a `Producto de Cotizacion`)
* **Campos de Totales (Solo Lectura, Calculados):**
    * `subtotal` (Currency)
    * `total_de_impuestos` (Currency)
    * `total_general` (Currency)

### 2. DocType: `Producto de Cotizacion`
Es la tabla hija que define las columnas de los artículos dentro de la cotización.

* **Naturaleza:** Is Child Table.
* **Campos Clave:**
    * `articulo` (Link a Item)
    * `cantidad` (Float)
    * `precio_unitario` (Currency)
    * `tasa_impuesto` (Percent)
* **Campos Calculados (Solo Lectura):**
    * `importe` (Currency)
    * `monto_impuesto` (Currency)

### 3. DocType: `Plantilla de Terminos de Pago`
Un DocType simple para almacenar y enlazar bloques de texto reutilizables para las condiciones de pago.

---

## ⚙️ Implementación del Código (Client Script)

La lógica de cálculo reside en el archivo `cotizacion.js`, un script del lado del cliente que se adjunta al DocType `Cotizacion`.

### Archivo: `cotizacion.js`

Este script realiza dos tareas principales:
1.  **Cálculo de Fila:** Calcula el total (`importe`) y el impuesto (`monto_impuesto`) de cada línea de producto.
2.  **Cálculo de Totales Generales:** Suma todos los totales de las filas para calcular el `subtotal`, `total_de_impuestos` y `total_general` del documento.

### Lógica de Disparadores (Triggers)

El script se activa en los siguientes eventos:

**1. `frappe.ui.form.on("Producto de Cotizacion", ...)` (Eventos de la Tabla Hija):**

Estos eventos se disparan cuando el usuario modifica datos *dentro* de la tabla de artículos:

* **`cantidad`**:
    * Recalcula `importe` y `monto_impuesto` para esa fila.
    * Llama a la función `calcular_totales_generales` para actualizar los totales.
* **`precio_unitario`**:
    * Recalcula `importe` y `monto_impuesto` para esa fila.
    * Llama a la función `calcular_totales_generales`.
* **`tasa_impuesto`**:
    * Recalcula `monto_impuesto` para esa fila.
    * Llama a la función `calcular_totales_generales`.
* **`items_remove`**:
    * Se dispara si se elimina una fila.
    * Llama a `calcular_totales_generales` para restar el monto eliminado de los totales.

**2. `frappe.ui.form.on("Cotizacion", ...)` (Eventos del DocType Principal):**

* **`refresh`**:
    * Se dispara cada vez que se carga el formulario.
    * Llama a `calcular_totales_generales` para asegurar que los totales mostrados sean siempre correctos al abrir el documento.
