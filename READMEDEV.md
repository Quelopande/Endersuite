## Automatización Contable y Setup Wizard Personalizado

Este módulo extiende Frappe para automatizar la creación de la Compañía, Año Fiscal y Catálogo de Cuentas durante la instalación y el Setup Wizard. Además, agrega un paso personalizado al Setup Wizard para seleccionar la compañía y el año fiscal, y nombra el catálogo como "[Iniciales] - Catalogo de Cuentas".

### Componentes Clave

- **Hooks (`endersuite/hooks.py`)**: after_install, setup_wizard_complete, setup_wizard_requires, scheduler_events (diario).
- **Lógica de instalación (`endersuite/install.py`)**: helpers para crear y vincular Compañía, Año Fiscal y Catálogo.
- **Utilidades contables (`endersuite/contabilidad/fiscal_utils.py`)**: helpers reutilizables y lógica centralizada.
- **Personalización del Setup Wizard (`endersuite/public/js/setup_wizard.js`)**: slide personalizado para selección de Compañía y Año Fiscal.

### Flujo de Trabajo
1. Al instalar la app y crear un nuevo sitio, se ejecuta el Setup Wizard con el slide personalizado.
2. Al finalizar el Setup Wizard, se crean y vinculan automáticamente la Compañía, Año Fiscal y Catálogo.
3. Un scheduler diario revisa y crea nuevos años fiscales y catálogos si es necesario.

### Consideraciones para Desarrolladores
- Todos los cambios están contenidos en `apps/endersuite`.
- Tras clonar el repo y agregar la app, ejecutar `bench build --app endersuite` para compilar los assets JS.
- El slide del Setup Wizard debe aparecer en la primera carga del sitio.
- La lógica de helpers está centralizada en `contabilidad/fiscal_utils.py` para facilitar el mantenimiento.
- Si se agregan nuevos requerimientos contables, extender los helpers y hooks existentes.

#### Archivos Clave
- `endersuite/hooks.py`
- `endersuite/install.py`
- `endersuite/contabilidad/fiscal_utils.py`
- `endersuite/public/js/setup_wizard.js`
