# Catálogo de Cuentas — Guía para desarrolladores (ES)

Esta carpeta contiene la implementación del DocType `Catalogo de Cuentas` (vista en árbol) del módulo Contabilidad.

## Estructura por defecto del árbol

Raíces protegidas (siempre grupos, irremovibles, solo se puede cambiar el nombre):

- Activo
- Pasivo
- Ingreso
- Gasto
- Capital

Hijos por defecto bajo Capital (no protegidos; se pueden editar, mover y eliminar):

- Capital Contable
- Capital Social

La creación se realiza en `after_install` y es idempotente (puede ejecutarse múltiples veces sin duplicar).

## Archivos clave

- `catalogo_de_cuentas.json` (DocType):
  - `is_tree: 1`
  - `autoname: field:cuenta` y `title_field: cuenta` ⇒ el nombre del documento se basa en el campo Data `cuenta`.
  - Campo oculto `protected_root` (Check) para marcar raíces protegidas.
  - `tree_method`: `endersuite.contabilidad.doctype.catalogo_de_cuentas.catalogo_de_cuentas.get_children`.

- `catalogo_de_cuentas.py` (Controlador):
  - `DEFAULT_ROOTS = ["Activo", "Pasivo", "Ingreso", "Gasto", "Capital"]`.
  - `create_default_groups()` crea o normaliza las raíces protegidas y los dos hijos de Capital.
  - `validate()` aplica reglas de protección cuando `protected_root = 1`:
    - Fuerza `is_group = 1`.
    - Mantiene el registro en raíz (`parent_catalogo_de_cuentas = ""`).
    - Si existe `disabled`, lo fuerza a 0.
    - Nota: se permite cambiar el campo `cuenta` (el nombre visible). Si deseas que renombre el docname automáticamente, ver apartado “Renombrado”.
  - `on_trash()` prohíbe eliminar raíces protegidas (mensaje en español).
  - `get_children(...)` devuelve nodos para la vista de árbol; cuando no existen registros persistentes en raíz, retorna nodos virtuales por defecto. Para `Capital` sin hijos, sugiere “Capital Contable” y “Capital Social”.

- `catalogo_de_cuentas_tree.js` (Vista de árbol):
  - Formulario en español orientado a cuentas:
    - `cuenta` (Data) — “Nombre de la cuenta” (Ej.: Caja, Bancos, Ventas)
    - `is_group` (Check) — “¿Es un grupo (carpeta)?”
  - Botón: “Añadir subcuenta”.

- `install.py` (App):
  - `after_install()` llama a `create_default_groups()`.
  - Importa traducciones desde `translations/es.csv` usando `frappe.translate.import_translations('es', path)`.

- `translations/es.csv`:
  - Contiene etiquetas del UI y mensajes (“No se puede eliminar el grupo por defecto: {0}”, etc.).

- `test_catalogo_de_cuentas.py` (Tests de integración):
  - Verifica que raíces protegidas se crean (o normalizan) con `protected_root = 1`.
  - Confirma que no pueden eliminarse y que sus flags restringidos se fuerzan.
  - Verifica que “Capital Contable” y “Capital Social” existen, son grupos y no están protegidos.

## Cómo ejecutar instalación y pruebas

After install manual (idempotente):

```python
from endersuite.install import after_install
after_install()
```

Pruebas (desde tu bench):

```bash
bench --site <tu-sitio> run-tests endersuite.contabilidad.doctype.catalogo_de_cuentas.test_catalogo_de_cuentas
```

Limpiar caché (si cambiaste traducciones o metadatos):

```bash
bench --site <tu-sitio> clear-cache
bench --site <tu-sitio> clear-website-cache
```

## Renombrado del documento al cambiar “cuenta” (opcional)

Actualmente se permite cambiar el campo `cuenta` de las raíces protegidas, pero el docname puede permanecer con el valor original. Si deseas que al guardar se renombre automáticamente el documento cuando cambie `cuenta`, añade una lógica con `frappe.rename_doc` en un `before_save`/`on_update` condicional. Podemos implementarlo si lo requieres.

## Extensiones y personalización

- Añadir más raíces o plantillas de subgrupos: editar `DEFAULT_ROOTS` y/o extender `create_default_groups()`.
- Cambiar campos del formulario del árbol: editar `catalogo_de_cuentas_tree.js`.
- Ajustar naming: modificar `autoname` o el `title_field` en el JSON del DocType.
- Localización: añadir/editar entradas en `translations/es.csv` y volver a ejecutar `after_install()` o usar comandos de traducción de Frappe.
