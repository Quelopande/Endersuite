# Módulo de Operaciones Básicas (Contabilidad)

## 1. Descripción General

Este módulo extiende la funcionalidad estándar de contabilidad del **Frappe Framework** para permitir el registro ágil y simplificado de movimientos de tesorería.

Su objetivo principal es registrar **Gastos Menores** (caja chica, taxis, papelería) e **Ingresos Varios** sin la necesidad de generar flujos complejos de Facturas de Venta/Compra ni gestión de proveedores/clientes.

Al validar una operación, el sistema genera automáticamente los **Asientos Contables (GL Entries)** correspondientes en el Libro Mayor, respetando la partida doble.

---

## 2. Nuevos Documentos (DocTypes)

Se han implementado dos nuevos DocTypes para soportar este flujo:

### A. Categoría de Operación (Maestro)

Actúa como un catálogo de conceptos para estandarizar los registros y evitar errores contables manuales.

- **Función:** Define la naturaleza de la transacción (Gasto o Ingreso) y la cuenta contable por defecto.
- **Configuración:** Permite asociar un nombre amigable (ej: "Gastos de Limpieza") con una cuenta contable específica.
- **Automatización:** Determina automáticamente si la operación debe debitar o acreditar la cuenta de destino.

### B. Operación Básica (Transacción)

Es el documento donde el usuario final registra el movimiento de dinero.

- **Estado:** Documento enviable (_Submittable_). Afecta la contabilidad al ser validado.
- **Nomenclatura:** Serie automática `OP-YYYY-#####`.
- **Multi-empresa:** Vinculado obligatoriamente a una Compañía específica.

---

## 3. Lógica de Negocio y Automatizaciones

### Validación Contable (Partida Doble)

El sistema determina automáticamente el Debe y el Haber basándose en la configuración de la categoría seleccionada:

| Tipo de Operación | Cuenta de Destino (Gasto/Ingreso) | Cuenta de Pago (Banco/Caja) |
| :---------------- | :-------------------------------- | :-------------------------- |
| **Gasto**         | Se carga (Debe)                   | Se abona (Haber)            |
| **Ingreso**       | Se abona (Haber)                  | Se carga (Debe)             |

### Filtros Inteligentes (Interfaz de Usuario)

Para evitar errores de imputación por parte del usuario:

1.  **Cuentas de Liquidez:** El campo "Cuenta de Pago" solo permite seleccionar cuentas de tipo **Banco** o **Efectivo (Caja)** pertenecientes a la empresa actual.
2.  **Cuentas Transaccionales:** Se ocultan las cuentas de tipo "Grupo" (carpetas) para asegurar que se elijan cuentas imputables.

### Auto-rellenado de Datos

- **Moneda:** Se hereda automáticamente de la configuración de la Compañía.
- **Cuenta Destino:** Al elegir una categoría, el sistema busca y asigna la cuenta contable predeterminada automáticamente.

---

## 4. Flujo de Trabajo

1.  **Configuración:** El administrador crea las "Categorías de Operación" (ej: Viáticos, Combustible) y asigna las cuentas contables.
2.  **Registro:** El usuario crea una "Operación Básica", selecciona la empresa, la categoría y la cuenta de origen/destino de los fondos.
3.  **Validación:** Al hacer _Submit_, se generan los asientos contables instantáneamente.
4.  **Cancelación:** Si se cancela el documento, los asientos contables se revierten automáticamente.
