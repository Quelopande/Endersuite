# Reporte: Libro Diario

## Propósito

Este reporte genera la vista oficial y cronológica de todas las transacciones financieras de la empresa. Su objetivo es cumplir con el principio contable de registro diario, mostrando cada movimiento de débito y crédito de manera secuencial.

**Regla de Negocio Crítica:**
El reporte refleja la "verdad contable" en tiempo real. No depende de procesos de cierre batch; en el instante en que un `Asiento Contable` es enviado (Submitted), este reporte incluye la información inmediatamente.

## Tipo de Componente

* **Script Report (Query Report)**
* Fuente de Datos: SQL directo a la base de datos.

## Fuente de la Verdad

A diferencia de vistas simples, este reporte **NO** lee el DocType `Asiento Contable` (que es solo el formulario de entrada).

Este reporte lee directamente del DocType **`Movimiento Contable` (GL Entry)**. Esto garantiza:
1.  **Velocidad:** Lectura de una tabla plana optimizada.
2.  **Integridad:** Solo muestra movimientos que han sido validados y contabilizados.
3.  **Granularidad:** Permite ver el desglose exacto por cuenta.

## Estructura de Columnas (Formato Estricto)

El reporte procesa los datos para coincidir estrictamente con el formato visual requerido:

| Columna | Fuente de Datos | Lógica de Visualización |
| :--- | :--- | :--- |
| **Fecha** | `Movimiento Contable`.`fecha_contable` | Orden cronológico ascendente. |
| **Número** | `Movimiento Contable`.`asiento_origen` | Enlace dinámico al documento original (`Asiento Contable`). |
| **Cuenta y detalle** | Concatenación Python | Combina el ID de la `Cuenta` + la `Narración` específica de la línea para una lectura clara en una sola celda (Ej: "1105 - Caja Menor - Compra de papelería"). |
| **DEBE** | `Movimiento Contable`.`debe` | Muestra el monto si es débito. Incluye suma total al pie de página. |
| **HABER** | `Movimiento Contable`.`haber` | Muestra el monto si es crédito. Incluye suma total al pie de página. |

## Filtros Disponibles

1.  **Desde Fecha / Hasta Fecha:** Obligatorios. Definen el periodo fiscal a visualizar.
2.  **Cuenta:** Opcional. Permite auditar los movimientos de una cuenta específica (libro auxiliar) dentro del formato de diario.

## Lógica Técnica (`libro_diario.py`)

1.  **Query SQL:** Ejecuta una selección sobre `tabMovimiento Contable` filtrando por rango de fechas.
2.  **Ordenamiento:** `ORDER BY fecha_contable ASC, creation ASC`. Asegura que las transacciones del mismo día aparezcan en el orden exacto en que fueron creadas en el sistema.
3.  **Procesamiento de Datos:** Itera sobre los resultados crudos para formatear la columna combinada "Cuenta y detalle" antes de enviarla a la vista.
