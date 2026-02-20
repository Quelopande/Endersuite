# Factura de Venta

## Descripción General

El doctype **Factura de Venta** es el componente central del sistema de facturación electrónica CFDI 4.0 de EnderSuite. Gestiona el ciclo completo de una factura: desde su creación, validación de datos fiscales, timbrado ante el SAT mediante un PAC (Proveedor Autorizado de Certificación), hasta la descarga de XML y PDF timbrados.

## Propósito

Este doctype permite:
- Crear facturas de venta con datos fiscales para el SAT mexicano
- Validar información requerida por CFDI 4.0
- Timbrar facturas electrónicas mediante integración con PAC
- Almacenar UUID, XML y PDF timbrados
- Descargar documentos fiscales (XML/PDF)
- Gestionar credenciales CSD (Certificado de Sello Digital)

## Estructura Principal de Campos

### Información Básica
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `cliente` | Link | Cliente (con datos fiscales: RFC, código postal, régimen) |
| `compania` | Link | Compañía emisora (con certificados CSD) |
| `fecha` | Date | Fecha de emisión de la factura |
| `fecha_vencimiento` | Date | Fecha límite de pago |

### Líneas de Productos
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `productos` | Table | Tabla de productos (Producto Factura de Ventas) |

### Totales
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `subtotal` | Currency | Suma de importes antes de impuestos |
| `total_impuestos` | Currency | Total de IVA y otros impuestos |
| `total` | Currency | Importe total de la factura |

### Información de Pago
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `metodo_de_pago` | Select | PUE (Pago en una sola exhibición) o PPD (Pago en parcialidades) |
| `forma_de_pago` | Select | Catálogo SAT: 01-Efectivo, 03-Transferencia, 04-Tarjeta, etc. |
| `uso_cfdi` | Select | Uso que el cliente dará al comprobante (G03, P01, etc.) |

### Datos de Timbrado (read-only después del timbrado)
| Campo | Tipo | Allow on Submit | Descripción |
|-------|------|-----------------|-------------|
| `uuid` | Data | ✅ | Folio fiscal asignado por el SAT |
| `xml_timbrado` | Long Text | ✅ | JSON con XML y PDF timbrados: `{"XML": "...", "PDF": "..."}` |
| `fecha_timbrado` | Datetime | ✅ | Timestamp del timbrado exitoso |
| `estado_timbrado` | Select | ❌ | Sin Timbrar / Timbrado / Error |

## Funcionalidades Implementadas

### 1. Sistema de Timbrado CFDI 4.0

#### Validaciones Pre-Timbrado
Antes de permitir el timbrado, el sistema verifica:

✅ **Compañía (Emisor)**
- RFC válido (12-13 caracteres)
- Nombre fiscal completo
- Régimen fiscal configurado
- Código postal del domicilio fiscal
- Certificados CSD cargados (.cer y .key con contraseña)

✅ **Cliente (Receptor)**
- RFC válido
- Nombre/Razón social
- Código postal
- Régimen fiscal
- Uso del CFDI seleccionado

✅ **Productos**
- Al menos un producto en la tabla
- Clave de producto/servicio SAT (8 dígitos)
- Clave de unidad de medida SAT (ej: H87, E48)
- Cantidad, precio y tasa de impuesto válidos

✅ **Datos Fiscales**
- Método de pago (PUE/PPD)
- Forma de pago del catálogo SAT
- Moneda (MXN por defecto)
- Tipo de comprobante (I - Ingreso)

#### Proceso de Timbrado

**Escenario 1: Sin Credenciales PAC Configuradas**
```
Usuario → Clic "Timbrar en SAT" 
       → Sistema detecta ausencia de credenciales
       → Muestra formulario de carga:
          • Archivo .cer (certificado)
          • Archivo .key (llave privada)
          • Contraseña de la llave
          • Checkbox: "Guardar para futuras facturas"
       → Usuario carga archivos y confirma
       → Sistema timbra con PAC
       → (Opcional) Guarda credenciales si checkbox marcado
```

**Escenario 2: Con Credenciales Configuradas**
```
Usuario → Clic "Timbrar en SAT"
       → Sistema detecta credenciales guardadas
       → Muestra opciones:
          [Usar Credenciales Configuradas] [Usar Otras Credenciales]
       → Si "Configuradas": timbra directamente
       → Si "Otras": muestra formulario de carga temporal
```

**Escenario 3: Error de Timbrado**
```
Timbrado → Falla por credenciales inválidas
         → Sistema clasifica error (credentials/pac/validation/unknown)
         → Muestra diálogo contextual con:
            • Mensaje descriptivo del error
            • Botón "Reintentar con Otras Credenciales" (si aplica)
            • Sugerencias de solución
```

### 2. Descarga de Documentos Fiscales

Una vez timbrada la factura, se habilitan botones en el diálogo de éxito:

**Descargar XML**
- Extrae el XML del campo `xml_timbrado` (JSON)
- Genera archivo con nombre: `{nombre_factura}_{uuid_limpio}.xml`
- Descarga automática al navegador

**Descargar PDF**
- Extrae el PDF del campo `xml_timbrado` (JSON)
- Decodifica desde base64
- Genera archivo con nombre: `{nombre_factura}_{uuid_limpio}.pdf`
- Descarga automática al navegador

### 3. Gestión de Información Global (Público General)

Para ventas al público general (RFC: XAXX010101000):
- Se agrega nodo `<cfdi:InformacionGlobal>` al XML
- Periodicidad: "01" (Diaria)
- Meses: "01" a "12" según fecha de factura
- Año: Año de emisión

## Arquitectura del Código

### Backend (`factura_de_venta.py`)

#### Métodos Whitelisted (API)

**`@frappe.whitelist()`**

1. **`check_pac_credentials()`**
   ```python
   Returns: {
       "configurado": bool,        # Existe Configuracion PAC
       "tiene_certificados": bool, # Compañía tiene .cer y .key
       "faltantes": [str]          # Lista de elementos faltantes
   }
   ```
   Verifica si el sistema tiene credenciales PAC configuradas.

2. **`timbrar_con_credenciales(factura_name, usar_configuradas, guardar, ...)`**
   ```python
   Args:
       factura_name: Nombre del documento
       usar_configuradas: True/False
       guardar: True para persistir credenciales nuevas
       key_file: Nombre archivo .key (si usar_configuradas=False)
       cer_file: Nombre archivo .cer (si usar_configuradas=False)
       key_pem: Contenido archivo .key
       cer_pem: Contenido archivo .cer
   
   Returns: {
       "success": bool,
       "uuid": str,            # Si success=True
       "xml": str,             # Si success=True
       "pdf": str,             # Si success=True (base64)
       "error": str,           # Si success=False
       "error_type": str       # credentials|pac|validation|unknown
   }
   ```
   Método principal de timbrado con soporte para credenciales temporales o guardadas.

3. **`descargar_xml(factura_name)`**
   ```python
   Returns: {
       "xml": str,             # Contenido del XML timbrado
       "filename": str         # Nombre sugerido del archivo
   }
   ```
   Extrae el XML del campo `xml_timbrado` para descarga.

4. **`descargar_pdf(factura_name)`**
   ```python
   Returns: {
       "pdf": str,             # PDF en base64
       "filename": str         # Nombre sugerido del archivo
   }
   ```
   Extrae el PDF del campo `xml_timbrado` para descarga.

#### Validaciones

**`validar_datos_fiscales_completos(doc)`**
- Verifica completitud de datos fiscales antes del timbrado
- Lanza excepciones descriptivas si faltan campos
- Validaciones por sección: Compañía, Cliente, Productos, Pago

**`validar_certificados_compania(compania)`**
- Verifica existencia de certificado y llave privada
- Valida que la contraseña esté configurada
- Retorna lista de elementos faltantes

#### Clasificación de Errores

**`_clasificar_error(error_msg)`**
```python
Returns: str  # "credentials" | "pac" | "validation" | "unknown"
```
Analiza el mensaje de error para clasificarlo:
- **credentials**: Certificado inválido, contraseña incorrecta, CSD vencido
- **pac**: Error de conexión, API no disponible, timeout
- **validation**: Datos faltantes, formato incorrecto
- **unknown**: Cualquier otro error

### Frontend (`factura_de_venta.js`)

#### Funciones Principales

**`mostrar_modal_timbrado(frm)`**
```javascript
// Punto de entrada
// 1. Valida estado del documento (submitted)
// 2. Verifica si ya está timbrado
// 3. Consulta check_pac_credentials()
// 4. Redirige al diálogo apropiado
```

**`mostrar_dialogo_opciones_credenciales(frm)`**
```javascript
// Diálogo con opciones cuando hay credenciales
// [Usar Configuradas] → confirmar_y_timbrar(frm, null, null, null, false)
// [Usar Otras] → mostrar_dialogo_subir_credenciales(frm, false)
```

**`mostrar_dialogo_subir_credenciales(frm, es_primera_vez)`**
```javascript
// Formulario de carga de certificados
// Campos:
//   - archivo_cer (File Upload)
//   - archivo_key (File Upload)
//   - password_key (Password)
//   - guardar_credenciales (Check - solo si !es_primera_vez)
// Botón Timbrar → Valida y llama confirmar_y_timbrar()
```

**`confirmar_y_timbrar(frm, archivo_cer, archivo_key, password_key, guardar)`**
```javascript
// Confirmación final y llamada RPC
frappe.call({
    method: 'endersuite.ventas.doctype.factura_de_venta.factura_de_venta.timbrar_con_credenciales',
    args: { /* ... */ },
    callback: manejar_respuesta_timbrado
});
```

**`manejar_respuesta_timbrado(frm, r)`**
```javascript
// Procesa respuesta del backend
if (success) {
    // Actualiza campos: uuid, xml_timbrado, fecha_timbrado
    frm.reload_doc();
    // Muestra diálogo de éxito con botones de descarga
    mostrar_dialogo_exito(frm, uuid);
} else {
    // Clasifica error y muestra diálogo apropiado
    mostrar_error_timbrado(error, error_type, frm);
}
```

**`mostrar_dialogo_exito(frm, uuid)`**
```javascript
// Diálogo de éxito con botones:
// [Descargar XML] → descargar_xml_timbrado(frm)
// [Descargar PDF] → descargar_pdf_timbrado(frm)
// Usa event listeners de jQuery para capturar clicks
```

**`descargar_xml_timbrado(frm)` / `descargar_pdf_timbrado(frm)`**
```javascript
// Llaman a métodos backend descargar_xml/descargar_pdf
// Crean Blob con el contenido
// Generan link de descarga temporal
// Simulan click para descarga automática
// Limpian el DOM
```

**`mostrar_error_timbrado(mensaje, tipo_error, frm)`**
```javascript
// Muestra diálogos contextuales según tipo:
switch(tipo_error) {
    case 'credentials':
        // Ofrece "Reintentar con Otras Credenciales"
        break;
    case 'pac':
        // Error de proveedor, mensaje genérico
        break;
    case 'validation':
        // Error de validación, revisar datos
        break;
    default:
        // Error desconocido
}
```

## Flujo de Datos

### Timbrado Exitoso
```
1. Frontend: Valida estado documento
2. Frontend: Verifica credenciales disponibles
3. Frontend: Usuario carga/confirma credenciales
4. Backend: validar_datos_fiscales_completos()
5. Backend: Construye JSON para PAC
6. Backend: Llama pac_service.timbrar_factura()
7. PAC Service: Envía petición a FacturaloPlus
8. PAC Service: Recibe UUID, XML, PDF
9. Backend: Almacena JSON {"XML": "...", "PDF": "..."}
10. Backend: Actualiza uuid, fecha_timbrado, estado_timbrado
11. Frontend: Recarga documento
12. Frontend: Muestra diálogo de éxito con botones descarga
```

### Descarga de Documentos
```
1. Usuario: Click en "Descargar XML" o "Descargar PDF"
2. Frontend: frappe.call() a descargar_xml/descargar_pdf
3. Backend: Extrae contenido de xml_timbrado (JSON)
4. Backend: Retorna {xml/pdf, filename}
5. Frontend: Crea Blob con el contenido
6. Frontend: Genera URL temporal
7. Frontend: Simula click para descarga
8. Navegador: Descarga archivo
```

## Manejo de Errores

### Tipos de Error y Respuesta

| Tipo | Causa Común | Respuesta del Sistema |
|------|-------------|----------------------|
| **credentials** | Certificado inválido, contraseña incorrecta | Ofrece reintentar con otras credenciales |
| **pac** | Conexión fallida, API caída | Mensaje genérico, reintentar más tarde |
| **validation** | RFC inválido, campos faltantes | Indica qué campo revisar |
| **unknown** | Error inesperado | Muestra mensaje de error técnico |

### Logging
Todos los errores se registran en el log de Frappe:
```python
frappe.log_error(message=str(e), title="Error en Timbrado CFDI")
```

## Seguridad

- Credenciales temporales no se persisten a menos que usuario marque checkbox
- Campo `password_key` en frontend es tipo Password (oculto)
- Certificados se almacenan en archivos privados de Frappe
- Métodos whitelisted validan permisos del usuario
- Datos sensibles no se exponen en logs del cliente

## Dependencias

### Backend
- `frappe`: Framework base
- `json`: Parseo de xml_timbrado
- `base64`: Decodificación de PDF
- `endersuite.ventas.services.pac_service`: Integración con PAC

### Frontend
- `frappe.ui.Dialog`: Diálogos modales
- `jQuery`: Event listeners para botones
- `Blob`, `URL.createObjectURL`: Descarga de archivos

## Integraciones

### Doctypes Relacionados
- **Configuracion PAC**: Credenciales del proveedor de timbrado
- **Compania**: Datos fiscales del emisor y certificados CSD
- **Cliente**: Datos fiscales del receptor
- **Producto**: Claves SAT y unidades de medida
- **Producto Factura de Ventas**: Líneas de detalle de la factura

### Servicios
- **pac_service.py**: Comunicación con FacturaloPlus para timbrado

## Casos de Uso

### Caso 1: Primera Factura del Sistema
```
1. Ir a: Ventas → Factura de Venta → Nueva
2. Seleccionar Cliente con datos fiscales completos
3. Seleccionar Compañía con certificados CSD
4. Agregar productos con claves SAT
5. Completar método y forma de pago
6. Submit
7. Click "Timbrar en SAT"
8. Sistema detecta primera vez
9. Cargar .cer, .key y contraseña
10. Marcar "Guardar para futuras facturas"
11. Confirmar timbrado
12. Descargar XML/PDF
```

### Caso 2: Factura con Credenciales Guardadas
```
1. Crear factura normal
2. Submit
3. Click "Timbrar en SAT"
4. Seleccionar "Usar Credenciales Configuradas"
5. Confirmar
6. Descargar documentos
```

### Caso 3: Error de Certificados Vencidos
```
1. Intentar timbrar
2. PAC rechaza por certificado vencido
3. Sistema clasifica como error "credentials"
4. Muestra diálogo: "Error de Credenciales"
5. Usuario hace click "Reintentar con Otras Credenciales"
6. Carga certificados nuevos
7. Timbrado exitoso
```

## Notas para Desarrolladores

### Extender Validaciones
Agregar nuevas validaciones en `validar_datos_fiscales_completos()`:
```python
def validar_datos_fiscales_completos(doc):
    # ... validaciones existentes ...
    
    # Nueva validación
    if not doc.mi_campo_requerido:
        frappe.throw("El campo X es requerido para timbrar")
```

### Agregar Nuevos Tipos de Error
Modificar `_clasificar_error()`:
```python
def _clasificar_error(error_msg):
    msg_lower = error_msg.lower()
    
    # Nuevo tipo
    if 'mi_error_especifico' in msg_lower:
        return 'mi_tipo_error'
    
    # ... clasificaciones existentes ...
```

Actualizar frontend `mostrar_error_timbrado()`:
```javascript
case 'mi_tipo_error':
    titulo = '⚠️ Mi Tipo de Error';
    primary_action_label = 'Acción Específica';
    // ...
```

### Cambiar Proveedor PAC
1. Actualizar `Configuracion PAC` con nuevas credenciales
2. Modificar `pac_service.py` para nueva API
3. Mantener interfaz de retorno consistente:
   ```python
   {"success": True, "uuid": "...", "xml": "...", "pdf": "..."}
   ```

## Testing

### Checklist de Pruebas

**Timbrado**
- [ ] Timbrar sin credenciales configuradas (primera vez)
- [ ] Timbrar con credenciales guardadas
- [ ] Timbrar con credenciales temporales
- [ ] Guardar credenciales desde formulario temporal
- [ ] Error por certificado inválido
- [ ] Error por contraseña incorrecta
- [ ] Error por RFC inválido
- [ ] Error por producto sin clave SAT

**Descarga**
- [ ] Descargar XML de factura timbrada
- [ ] Descargar PDF de factura timbrada
- [ ] Validar contenido del XML (UUID, RFC, totales)
- [ ] Validar que PDF se descargue correctamente

**Validaciones**
- [ ] Intentar timbrar sin RFC en compañía
- [ ] Intentar timbrar sin RFC en cliente
- [ ] Intentar timbrar sin productos
- [ ] Intentar timbrar sin certificados CSD

## Documentación Adicional

- Ver `TIMBRADO.md` para detalles técnicos del proceso de timbrado
- [Anexo 20 SAT](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/anexo_20.htm)
- [Guía CFDI 4.0](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/Instructivo_de_llenado_CFDI.pdf)

## Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.0.0 | 2025-11 | Implementación completa sistema CFDI 4.0 con timbrado y descarga |

## Autor

Implementado por: RenderCores  
Contacto: https://www.rendercores.com
