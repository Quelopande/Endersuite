# DocType: Movimiento Contable

## Propósito

Este DocType es el **Libro Mayor General (GL)**. Es la "fuente de la verdad" de toda la contabilidad y la base para todos los reportes financieros.

**Importante:** El usuario NUNCA interactúa con este DocType directamente. Es un registro de "solo escritura" creado exclusivamente por la lógica del sistema (backend).

## Tipo de DocType

* **Registro de Sistema / Transacción** (Backend)

## Estructura y Campos Clave

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `fecha_contable` | Date | Fecha de contabilización (copiada del `Asiento Contable`). |
| `cuenta` | Link | La `Cuenta Contable` específica afectada. |
| `debe` | Currency | Monto del débito. |
| `haber` | Currency | Monto del crédito. |
| `asiento_origen` | Link | Enlace al `Asiento Contable` que generó este movimiento. |
| `tipo_asiento` | Link | (Opcional, pero útil) El tipo de asiento que lo generó. |

## Lógica de Negocio y Validaciones

* Este DocType **intencionalmente no tiene lógica de negocio** (ni `.py` ni `.js`).
* Es un almacén de datos plano y "tonto". Esta simplicidad es lo que garantiza su **escalabilidad y velocidad** en la lectura.
* Los registros son creados por `Asiento Contable.on_submit` y borrados por `Asiento Contable.on_cancel`.

## Interacciones

* **Escrito por:**
    * `Asiento Contable` (método `crear_movimientos_contables`).
* **Leído por:**
    * `Query Report: Libro Diario` (es su fuente de datos principal).
    * (Futuro) Reporte de Balance General.
    * (Futuro) Reporte de Estado de Resultados.
