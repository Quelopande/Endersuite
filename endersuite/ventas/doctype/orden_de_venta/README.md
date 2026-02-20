# Documentación del Módulo de Ventas Personalizado

Este documento describe la arquitectura y el propósito de los nuevos DocTypes creados para gestionar el ciclo de vida de las ventas.

El flujo principal se centra en el DocType `Orden de Venta`, que actúa como el documento transaccional central una vez que un cliente ha confirmado un pedido.

---

## 1. DocType: `Vendedor`

* **Tipo:** `Master` (Maestro)
* **Propósito:** Almacena la información centralizada de los agentes de ventas o empleados responsables de las ventas. No es una transacción, sino una lista de personas.

### Campos Clave

| Label (Etiqueta) | Fieldname | Tipo | Notas |
| :--- | :--- | :--- | :--- |
| Nombre del Vendedor | `nombre_vendedor` | Data | (Mandatory, Unique) |
| Estado | `estado` | Select | Opciones: `Activo`, `Inactivo`. (Default: `Activo`) |
| Email | `email` | Data (Email) | |
| Teléfono | `telefono` | Data (Phone) | |

### Relaciones

* Es utilizado por el DocType `Orden de Venta` en el campo `vendedor_responsable`.
* Se recomienda filtrar el Link en `Orden de Venta` para mostrar solo Vendedores con `estado == 'Activo'`.

---

## 2. DocType: `Producto de Orden de Venta`

* **Tipo:** `Child Table` (Tabla Hija)
* **Propósito:** Define la estructura de la **tabla de items** que se utiliza *dentro* del DocType `Orden de Venta`.
* **Nota:** Este DocType es la plantilla para el campo que visualmente se llama "Items confirmados" en el formulario de la Orden de Venta.

### Campos Clave

| Label (Etiqueta) | Fieldname | Tipo | Notas |
| :--- | :--- | :--- | :--- |
| Producto | `producto` | Link (Item) | Referencia al maestro de productos/items. |
| Cantidad | `cantidad` | Float | |
| Precio Unitario | `precio_unitario` | Currency | |
| Importe Total | `importe_total` | Currency | (Read Only) Calculado por Client Script. |

### Lógica Adicional

* Los `fieldnames` (`producto`, `cantidad`, `precio_unitario`, etc.) en este DocType deben coincidir **exactamente** con los `fieldnames` de la tabla hija de `Cotizacion` (ej. `Producto de Cotizacion`) para permitir el mapeo automático.
* Un **Client Script** adjunto a `Orden de Venta` se encarga de calcular `importe_total` (`cantidad * precio_unitario`) automáticamente.

---

## 3. DocType: `Orden de Venta`

* **Tipo:** `Submittable` (Transaccional)
* **Propósito:** Es el pilar del ciclo de venta. Sirve como la confirmación oficial de un pedido por parte del cliente. Es el documento base para la facturación y la gestión de entregas.

### Campos Clave

| Label (Etiqueta) | Fieldname | Tipo | Notas |
| :--- | :--- | :--- | :--- |
| Cliente | `cliente` | Link (Cliente) | Cliente que realiza el pedido. |
| Fecha del pedido | `fecha_pedido` | Date | Fecha de confirmación. |
| Vendedor responsable| `vendedor_responsable` | Link (Vendedor) | Vendedor asociado a la venta. |
| Referencia Cotización| `referencia_cotizacion`| Link (Cotizacion)| (Read Only) Se llena automáticamente al crear desde una `Cotizacion`. |
| Estado | `estado` | Select | (Read Only) Controlado por el Workflow. |
| Items confirmados | `items` | Table | **Options:** `Producto de Orden de Venta`. |

### Funcionalidad Clave (Workflow y Enlaces)

1.  **Enlace con `Cotizacion`:**
    * En el DocType `Cotizacion`, se ha configurado un **"Document Link"**.
    * Esto crea el botón "Crear" -> "Orden de venta" en las cotizaciones confirmadas.
    * Al usarse, mapea automáticamente los campos (`cliente`, etc.) y la tabla de items (`articulos` -> `items`) gracias a la coincidencia de `fieldnames`.

2.  **Ciclo de Vida (Workflow):**
    * Este DocType es "Submittable" (`docstatus` 0, 1, 2).
    * Un **Workflow** dedicado (`Workflow de Orden de Venta`) gestiona el campo `estado` (que es Read Only).
    * **Estados del Workflow:**
        * `Borrador` (DocStatus 0)
        * `Confirmada` (DocStatus 1)
        * `En entrega` (DocStatus 1)
        * `Cerrada` (DocStatus 1)
        * `Cancelada` (DocStatus 2)
    * **Botones (Transiciones):** El workflow crea botones (`Confirmar`, `Iniciar Entrega`, `Cerrar Orden`) que mueven el documento entre estos estados.

3.  **Scripts de Cliente:**
    * Se utiliza un **Client Script** para calcular el `importe_total` en la tabla `items` (como se describe en `Producto de Orden de Venta`).
