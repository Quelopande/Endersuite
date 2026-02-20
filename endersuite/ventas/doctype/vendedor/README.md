# 📂 Módulo de Gestión de Fuerza de Ventas y Territorios (Frappe/ERPNext)

Este documento detalla la configuración técnica para la implementación de la gestión de vendedores, jerarquías territoriales y automatización de documentos en **Frappe Framework**.

---

## 🚀 Resumen de Funcionalidades

1.  **Maestro de Vendedores:** Perfiles de venta vinculados a usuarios del sistema.
2.  **Jerarquía de Territorios:** Estructura de árbol (Tree) para regiones y zonas.
3.  **Automatización de Cotizaciones:** Asignación automática del vendedor basada en la sesión del usuario.

---

## 1️⃣ Configuración de DocTypes

### A. DocType: `Vendedor` (Master Data)

_Define a los individuos responsables de las ventas._

- **Module:** Selling (o Custom)
- **Is Submittable:** No
- **Autoname:** `field:nombre_vendedor`
- **Title Field:** `nombre_vendedor`

#### Campos (Fields):

| Label                   | Fieldname         | Type   | Mandatory | Options / Notes                         |
| :---------------------- | :---------------- | :----- | :-------- | :-------------------------------------- |
| **Nombre del Vendedor** | `nombre_vendedor` | Data   | **Yes**   | ID del documento.                       |
| **ID de Usuario**       | `user_id`         | Link   | No        | `User`. Vincula al login del sistema.   |
| **Estado**              | `estado`          | Select | **Yes**   | `Activo` (Default), `Inactivo`.         |
| **Reporta a**           | `reporta_a`       | Link   | No        | `Vendedor`. Para jerarquía de personal. |
| **Territorio**          | `territorio`      | Link   | No        | `Territorio`. Zona asignada.            |

> **Validación Sugerida (Server Script):** Validar que un `user_id` no esté asignado a más de un vendedor activo simultáneamente.

---

### B. DocType: `Territorio` (Tree Structure)

_Define la estructura geográfica o de mercado._

- **Module:** Selling (o Custom)
- **Is Tree:** **Yes** (Activado)
- **Autoname:** `field:territory_name`

#### Configuración de Árbol (Tree Settings):

- **Parent Field:** `parent_territory` (Debe configurarse en los ajustes del DocType).

#### Campos (Fields):

| Label                     | Fieldname          | Type  | Mandatory | Options / Notes                     |
| :------------------------ | :----------------- | :---- | :-------- | :---------------------------------- |
| **Nombre del Territorio** | `territory_name`   | Data  | **Yes**   | ID del nodo.                        |
| **Es Grupo**              | `is_group`         | Check | No        | Define si tiene hijos (carpetas).   |
| **Territorio Padre**      | `parent_territory` | Link  | No        | `Territorio`. Enlace al nodo padre. |

---

## 2️⃣ Personalizaciones (Customize Form)

### DocType: `Quotation` (Cotización)

_Se agrega el vínculo para asignar la venta._

1.  Ir a **Customize Form**.
2.  Seleccionar DocType: `Quotation`.
3.  Agregar el siguiente campo (sugerido después de `customer`):

| Label        | Fieldname  | Type | Options    |
| :----------- | :--------- | :--- | :--------- |
| **Vendedor** | `vendedor` | Link | `Vendedor` |

---

## 3️⃣ Automatización (Client Scripts)

### Script: Asignar Vendedor por Defecto

_Asigna automáticamente el vendedor en la Cotización basándose en el usuario logueado._

- **Name:** `Cotización - Asignar Vendedor`
- **DocType:** `Quotation`
- **Enabled:** Yes

```javascript
frappe.ui.form.on("Cotizacion", {
  onload: function (frm) {
    // 1. Solo ejecutar si el documento es NUEVO
    if (frm.is_new()) {
      // 2. Buscar si el usuario logueado es un Vendedor
      frappe.db.get_value(
        "Vendedor",
        {
          user_id: frappe.session.user,
          estado: "Activo",
        },
        "name",
        (r) => {
          // 3. Si existe, asignar al campo
          if (r && r.name) {
            frm.set_value("vendedor", r.name);
          }
        }
      );
    }
  },
});
```

# classDiagram

    class User {
        +email
    }
    class Vendedor {
        +nombre_vendedor
        +user_id
        +territorio
    }
    class Territorio {
        +territory_name
        +parent_territory
    }
    class Quotation {
        +customer
        +vendedor
    }

    User "1" -- "1" Vendedor : Link
    Vendedor "*" -- "1" Territorio : Asignado a
    Territorio "*" -- "1" Territorio : Jerarquía (Padre)
    Quotation "*" -- "1" Vendedor : Transacción de #
