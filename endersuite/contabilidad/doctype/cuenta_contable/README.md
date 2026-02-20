# 📘 Módulo de Contabilidad en Frappe: Cuentas T y Asientos

Este proyecto implementa un sistema contable básico dentro de Frappe Framework. Sus principales características son la visualización gráfica de **Cuentas T** (Debe/Haber) y la **Validación Estricta** de la ecuación contable (Partida Doble).

---

## 1. Estructura de Base de Datos (DocTypes)

Para que el código funcione, se deben crear los siguientes DocTypes con los **Nombres de Campo (Field Name)** exactos que se listan a continuación.

### A. DocType: `Cuenta Contable`

_Es el maestro de cuentas (Plan de Cuentas)._

- **Module:** Contabilidad
- **Is Tree:** ✅ (Activado)
- **Campos:**
  - `nombre_de_cuenta` (Data, Mandatory)
  - `parent_account` (Link -> _Cuenta Contable_)
  - `is_group` (Check)
  - `visualizacion_t` (HTML) -> _Aquí se dibujará la tabla._

### B. DocType: `Detalle Asiento`

_Es la tabla hija que contiene las líneas del asiento._

- **Module:** Contabilidad
- **Is Child Table:** ✅ (Activado)
- **Campos:**
  - `cuenta` (Link -> _Cuenta Contable_)
  - `debito` (Currency, Default: 0)
  - `credito` (Currency, Default: 0)

### C. DocType: `Asiento Contable`

_Es el documento transaccional (Comprobante)._

- **Module:** Contabilidad
- **Is Submittable:** ✅ (Activado)
- **Naming Series:** `ASI-.YYYY.-`
- **Campos:**
  - `posting_date` (Date, Mandatory)
  - `detalle` (Table -> _Detalle Asiento_) -> _Nota: El nombre del campo debe ser "detalle"._

---

## 2. Implementación del Backend (Python)

### A. Validación de Integridad (`asiento_contable.py`)

**Ubicación:** `tu_app/contabilidad/doctype/asiento_contable/asiento_contable.py`

Este script asegura que no se guarden asientos descuadrados y evita imputaciones a cuentas "Grupo".

```python
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class AsientoContable(Document):
    def validate(self):
        self.validar_filas()
        self.validar_cuentas_detalle()
        self.validar_cuadre_ecuacion()

    def validar_filas(self):
        if not self.detalle:
            frappe.throw(_("No se puede guardar un asiento sin movimientos."))

    def validar_cuadre_ecuacion(self):
        total_debe = 0.0
        total_haber = 0.0

        # Sumariza la tabla 'detalle'
        for row in self.detalle:
            total_debe += flt(row.debito)
            total_haber += flt(row.credito)

        diferencia = total_debe - total_haber

        # Tolerancia de 0.009 para redondeo
        if abs(diferencia) > 0.009:
            msg = f"""
            <b>¡Error de Ecuación Contable!</b><br>
            El asiento no cuadra.<br>
            Total Debe: {total_debe:,.2f}<br>
            Total Haber: {total_haber:,.2f}<br>
            <b>Diferencia: {diferencia:,.2f}</b>
            """
            frappe.throw(_(msg))

    def validar_cuentas_detalle(self):
        # Valida que no se use una cuenta "Carpeta" (Grupo)
        for row in self.detalle:
            if not row.cuenta: continue

            es_grupo = frappe.db.get_value("Cuenta Contable", row.cuenta, "is_group")
            if es_grupo == 1:
                frappe.throw(_(f"Error en fila {row.idx}: La cuenta <b>{row.cuenta}</b> es un Grupo. Solo usa cuentas finales."))
```
