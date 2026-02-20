# DocType: Centro de Costos

**Módulo:** Contabilidad  
**Framework:** Frappe  
**Estructura:** Árbol (Tree Structure)

## 1. Descripción General

El DocType **Centro de Costos** permite gestionar la estructura jerárquica de las áreas de negocio, departamentos o unidades operativas de la empresa. Su objetivo principal es permitir la imputación de gastos e ingresos a segmentos específicos para obtener reportes de rentabilidad detallados.

Este DocType utiliza la funcionalidad **Nested Set** (Árbol) de Frappe, permitiendo crear una estructura de padres e hijos (ej: _Operaciones > Planta Norte > Línea 1_).

## 2. Estructura de Campos (Fields)

| Etiqueta (Label)         | Nombre del Campo (Name) | Tipo (Type) | Obligatorio | Descripción                                                                                                                        |
| :----------------------- | :---------------------- | :---------- | :---------- | :--------------------------------------------------------------------------------------------------------------------------------- |
| **Nombre Centro Costos** | `nombre_centro_costos`  | Data        | Sí          | Nombre identificativo del área o departamento.                                                                                     |
| **Código**               | `codigo_centro`         | Data        | No          | Código interno para reportes (Ej: 100-01).                                                                                         |
| **Compañía**             | `compania`              | Link        | Sí          | Enlace al DocType `Compania`. Define la entidad legal propietaria.                                                                 |
| **Es Grupo**             | `es_grupo`              | Check       | No          | Si está marcado, indica que este nodo puede contener otros centros de costo dentro. No debe recibir asientos directos si es grupo. |
| **Centro Padre**         | `centro_costos_padre`   | Link        | No          | Enlace a `Centro de Costos`. Define el nodo superior en la jerarquía.                                                              |

## 3. Configuración del DocType

Para el correcto funcionamiento de la jerarquía, se han aplicado las siguientes configuraciones en el DocType:

- **Is Tree:** `Activado` (Habilita la vista de árbol y la lógica Nested Set).
- **Naming Rule:** By Field (`nombre_centro_costos`).

## 4. Lógica de Cliente (Client Script)

Se ha implementado un script de cliente (`Client Script`) para garantizar la integridad de los datos en el formulario:

1.  **Filtrado de Padres:** El campo `centro_costos_padre` solo muestra registros que cumplan dos condiciones:
    - `es_grupo` == 1
    - `compania` == Compañía seleccionada en el registro actual.
2.  **Herencia de Compañía:** Al crear un centro de costos hijo desde la vista de árbol, el campo `compania` se hereda automáticamente del padre seleccionado.

## 5. Validaciones de Servidor (Python)

_(Pendiente de implementación en controlador)_

Se recomienda validar en el método `validate` o `on_update` lo siguiente:

- Un centro de costos no puede ser padre de sí mismo.
- No se puede cambiar la compañía si el centro de costos tiene registros contables asociados.
- Validación de estructura de árbol (Nested Set update).

## 6. Relación con otros DocTypes

- **Compania:** Relación 1:N (Una compañía tiene muchos centros de costos).
- **Asiento Contable / Detalle de Asiento:** Se utiliza en las líneas de detalle para imputar el gasto/ingreso.
- **Presupuesto:** (Futuro) Se podrá asignar presupuesto a nivel de Centro de Costos.

---
