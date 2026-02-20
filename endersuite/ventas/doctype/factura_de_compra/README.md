# 📦 Módulo de Gestión Financiera (Endersuite)

Este documento detalla la estructura, lógica y funcionamiento de los nuevos DocTypes implementados para la gestión de **Compras, Pagos y Términos de Pago** en el framework Frappe.

---

## 🚀 1. Plantillas de Términos de Pago

**Objetivo:** Estandarizar las reglas de pago (ej. 50% anticipo, 50% entrega) para su reutilización en documentos comerciales.

### Estructura de Datos

- **DocType Padre:** `Termino de Pago Plantilla`
  - _Naming:_ Basado en el nombre de la plantilla.
- **DocType Hijo:** `Termino de Pago Detalle`
  - Contiene: Porción de factura (%), Días de crédito y Descripción.

### Lógica de Negocio (Python)

- **Validación de Totales:** Se implementó un script que valida que la suma de la columna `porcion_de_factura` sea estrictamente igual al **100%**. Si no cumple, se impide el guardado.

---

## 🛒 2. Factura de Compra

**Objetivo:** Registro espejo de la "Factura de Venta" para gestionar obligaciones con proveedores, calculando automáticamente impuestos trasladados y retenidos por línea.

### Estructura de Datos

- **DocType Padre:** `Factura de Compra`
  - _Naming Series:_ `FC-{YYYY}-{MM}-{#####}`
  - _Estado:_ Submittable (Se permite enviar/validar).
- **DocType Hijo:** `Producto Factura de Compra`
  - Campos Clave: `valor` (Precio), `cantidad`, `descuento`, `porcentaje_iva`, `porcentaje_retencion`.

### Automatización (Script Python)

El controlador `factura_de_compra.py` ejecuta la función `calculate_totales` antes de guardar (`validate`), realizando las siguientes operaciones:

1.  **Cálculo por Línea:**
    - `(Cantidad * Valor) - Descuento = Total Línea`
    - Cálculo individual de IVA y Retención basado en los porcentajes de la fila.
2.  **Acumulación:** Suma los subtotales e impuestos de todas las filas.
3.  **Cálculo Final:**
    - `Total = (Subtotal + Imp. Trasladados) - Imp. Retenidos - Descuento Global`

---

## 💸 3. Gestión de Pagos

**Objetivo:** Unificar el registro de entradas (Cobros) y salidas (Pagos) de dinero en un solo formulario dinámico.

### Estructura de Datos

- **DocType:** `Pago`
  - _Tipo:_ Transaccional.

### Lógica de Interfaz (UI Dynamics)

Se utiliza la propiedad **Depends On** para mostrar/ocultar campos según el tipo de operación:

| Selección (Tipo de Pago) | Campo Visible       | Condición (`Depends On`)           |
| :----------------------- | :------------------ | :--------------------------------- |
| **Cobro**                | `Factura de Venta`  | `eval:doc.tipo_de_pago == 'Cobro'` |
| **Pago**                 | `Factura de Compra` | `eval:doc.tipo_de_pago == 'Pago'`  |

---

## 🛠 Instalación y Despliegue

Para reflejar estos cambios en un entorno de producción o desarrollo nuevo:

1. **Migración de Base de Datos:**
   ```bash
   bench migrate
   ```
