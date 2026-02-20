# Configuración PAC

## Descripción General

`Configuracion PAC` es un **SingleDocType** que almacena las credenciales y configuración necesaria para la integración con el Proveedor Autorizado de Certificación (PAC) para el timbrado de facturas electrónicas CFDI 4.0.

**SingleDocType**: Solo existe un único documento de este tipo en el sistema, funcionando como configuración global.

## Propósito

Este doctype centraliza la configuración del PAC (actualmente FacturaloPlus) que se utiliza para timbrar facturas electrónicas ante el SAT (Servicio de Administración Tributaria de México).

## Estructura de Campos

### Campos de Configuración

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `pac_provider` | Data | Sí | Nombre del proveedor PAC (ej: "FacturaloPlus") |
| `api_url` | Data | Sí | URL del endpoint API del PAC |
| `api_username` | Data | Sí | Usuario para autenticación con el PAC |
| `api_password` | Password | Sí | Contraseña para autenticación con el PAC |
| `entorno` | Select | Sí | Ambiente: "Producción" o "Pruebas" |
| `activo` | Check | No | Indica si la configuración está activa |

## Uso

### Configuración Inicial

1. Navegar a: **Ventas → Configuración PAC**
2. Llenar los campos con las credenciales proporcionadas por el PAC
3. Seleccionar el entorno apropiado (Pruebas/Producción)
4. Marcar como "Activo"

### Integración con Factura de Venta

El servicio `pac_service.py` utiliza esta configuración para:
- Autenticar las peticiones al PAC
- Determinar el endpoint correcto según el entorno
- Timbrar facturas electrónicas

### Ejemplo de Configuración

```python
# Obtener configuración del PAC
pac_config = frappe.get_single("Configuracion PAC")

if not pac_config.activo:
    frappe.throw("La configuración del PAC no está activa")

# Usar credenciales
api_url = pac_config.api_url
username = pac_config.api_username
password = pac_config.api_password
```

## Seguridad

- El campo `api_password` es de tipo **Password**, por lo que se almacena de forma cifrada
- Las credenciales nunca se exponen en logs o respuestas del cliente
- Solo usuarios con permisos específicos pueden acceder a este doctype

## Notas para Desarrolladores

### Validaciones Importantes

- Verificar que la configuración esté activa antes de intentar timbrar
- Validar que todos los campos obligatorios estén llenos
- Manejar errores de autenticación con el PAC apropiadamente

### Extensión Futura

Para agregar soporte a otros proveedores PAC:
1. Agregar el nombre del proveedor en el campo `pac_provider`
2. Modificar `pac_service.py` para detectar el proveedor
3. Implementar la lógica específica según la API del nuevo proveedor

## Referencias

- [Documentación FacturaloPlus](https://dev.facturaloplus.com)
- [Anexo 20 SAT - CFDI 4.0](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/anexo_20.htm)
- Servicio relacionado: `endersuite/ventas/services/pac_service.py`

## Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.0.0 | 2025-11 | Implementación inicial con soporte para FacturaloPlus |
