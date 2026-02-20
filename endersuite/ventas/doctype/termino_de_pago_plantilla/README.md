# Funcionalidad: Plantillas de Términos de Pago

**Referencia de Tarea:** ISS-2025-00001
**Desarrollado en:** Frappe Framework

## 📄 Descripción General

Este desarrollo implementa la gestión de **Plantillas de Términos de Pago** dentro del sistema. Su objetivo es permitir la creación de esquemas de pago reutilizables (ej. "50% Anticipo - 50% Entrega") para agilizar la facturación y evitar errores manuales en el cálculo de fechas de vencimiento.

La estructura se basa en una relación Maestro-Detalle (Parent-Child) utilizando dos DocTypes personalizados.

---

## 🛠 Estructura de Datos (DocTypes)

Se han creado dos nuevos DocTypes para manejar esta lógica:

### 1. DocType Padre: `Termino de Pago Plantilla`

Define el contenedor principal de la plantilla.

- **Módulo:** Desarrollo (Custom)
- **Naming:** Autoname basado en el campo `nombre_de_plantilla`.

| Etiqueta (Label)        | Nombre del Campo (Fieldname) | Tipo (Type) | Obligatorio | Descripción                                                  |
| :---------------------- | :--------------------------- | :---------- | :---------- | :----------------------------------------------------------- |
| **Nombre de Plantilla** | `nombre_de_plantilla`        | Data        | Sí          | Identificador único de la plantilla (ej. "Crédito 30 Días"). |
| **Términos**            | `terminos`                   | Table       | No          | Tabla hija que conecta con los detalles de plazos.           |

### 2. DocType Hijo: `Termino de Pago Detalle`

Define las líneas individuales de cada plazo dentro de una plantilla.

- **Módulo:** Desarrollo (Custom)
- **Tipo:** Child Table (Is Table ✅)

| Etiqueta (Label)       | Nombre del Campo (Fieldname) | Tipo (Type) | Obligatorio | Descripción                                               |
| :--------------------- | :--------------------------- | :---------- | :---------- | :-------------------------------------------------------- |
| **Porción de Factura** | `porcion_de_factura`         | Percent     | Sí          | Porcentaje del monto total a pagar en este plazo.         |
| **Días de Crédito**    | `dias_de_credito`            | Int         | Sí          | Días transcurridos desde la factura hasta el vencimiento. |
| **Descripción**        | `descripcion`                | Data        | No          | Nota breve (ej. "Anticipo").                              |

---

## ⚙️ Lógica de Negocio y Validaciones

### Validación de Totales (Python)

Se ha implementado una validación en el evento `validate` del controlador `termino_de_pago_plantilla.py`.
**Regla:** La suma de todas las filas en el campo `porcion_de_factura` debe ser estrictamente igual al **100%**. Si no cumple, el sistema impide guardar y arroja un error.

```python
# Ejemplo de la lógica implementada
def validate(self):
    total = sum([d.porcion_de_factura for d in self.terminos])
    if total != 100:
        frappe.throw("La suma de las porciones de factura debe ser exactamente 100%.")
```
