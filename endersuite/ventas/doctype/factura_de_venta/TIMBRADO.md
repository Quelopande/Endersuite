# Sistema de Timbrado de Facturas - Mejoras Implementadas

## Descripción General

Se ha mejorado significativamente el sistema de timbrado de facturas de venta con el SAT para proporcionar mayor flexibilidad en el manejo de credenciales PAC y un mejor manejo de errores.

## Características Principales

### 1. Modal de Opciones de Credenciales

El sistema ahora detecta automáticamente si hay credenciales PAC configuradas y presenta las opciones correspondientes:

- **Con credenciales configuradas**: Muestra un diálogo que permite:
  - Usar las credenciales ya guardadas
  - Usar credenciales temporales diferentes

- **Sin credenciales configuradas**: Muestra directamente el formulario para cargar certificados

### 2. Carga Temporal de Credenciales

Los usuarios pueden cargar certificados (.cer) y llaves privadas (.key) de forma temporal para timbrar una factura específica sin guardar las credenciales en el sistema:

- Archivo de Certificado (.cer)
- Archivo de Llave Privada (.key)
- Contraseña de la llave privada
- Opción para guardar las credenciales para uso futuro

### 3. Manejo Mejorado de Errores

El sistema ahora clasifica los errores en categorías específicas:

#### Tipos de Error

- **Error de Credenciales** (`credentials`):
  - Certificados inválidos
  - Contraseña incorrecta
  - Certificados vencidos
  - Ofrece reintentar con otras credenciales

- **Error del Proveedor PAC** (`pac`):
  - Problemas de conexión con el PAC
  - API no disponible
  - Errores en la respuesta del servicio

- **Error de Validación** (`validation`):
  - Datos faltantes en la factura
  - Campos requeridos no completados
  - Formato incorrecto de datos

- **Error Desconocido** (`unknown`):
  - Cualquier otro tipo de error no clasificado

### 4. Diálogos Contextuales

Cada tipo de error presenta un diálogo específico con:
- Título descriptivo
- Mensaje de error detallado
- Acciones recomendadas
- Botones de acción apropiados (ej: "Reintentar con Otras Credenciales")

## Estructura del Código

### Frontend (`factura_de_venta.js`)

#### Funciones Principales

1. **`mostrar_modal_timbrado(frm)`**
   - Punto de entrada principal
   - Verifica si hay credenciales configuradas
   - Redirige al diálogo apropiado

2. **`mostrar_dialogo_opciones_credenciales(frm)`**
   - Muestra opciones cuando hay credenciales guardadas
   - Permite elegir entre credenciales guardadas o nuevas

3. **`mostrar_dialogo_subir_credenciales(frm, es_primera_vez)`**
   - Formula de carga de certificados
   - Incluye checkbox para guardar credenciales
   - Valida campos requeridos

4. **`confirmar_y_timbrar(frm, archivo_cer, archivo_key, password_key, guardar)`**
   - Confirmación final antes de timbrar
   - Envía datos al backend
   - Maneja respuesta del servidor

5. **`manejar_respuesta_timbrado(frm, r)`**
   - Procesa la respuesta del timbrado
   - Clasifica errores por tipo
   - Muestra mensajes apropiados

6. **`mostrar_error_timbrado(mensaje, tipo_error, frm)`**
   - Presenta diálogos de error contextuales
   - Ofrece acciones de recuperación

### Backend (`factura_de_venta.py`)

#### Métodos Whitelisted

1. **`check_pac_credentials()`**
   ```python
   Returns: {
       "configurado": bool,
       "tiene_certificados": bool,
       "faltantes": [str]
   }
   ```
   - Verifica si existe configuración PAC
   - Valida presencia de certificados
   - Lista elementos faltantes

2. **`timbrar_con_credenciales(factura_name, usar_configuradas, guardar, key_file, cer_file, key_pem, cer_pem)`**
   ```python
   Returns: {
       "success": bool,
       "uuid": str,           # Si success=True
       "error": str,          # Si success=False
       "error_type": str      # Si success=False
   }
   ```
   - Soporta timbrado con credenciales guardadas o temporales
   - Opción para persistir credenciales nuevas
   - Clasificación de errores por tipo

3. **`timbrar_en_sat(factura_name)`** (método legacy)
   - Mantiene compatibilidad con código existente
   - Usa siempre credenciales configuradas
   - Incluye clasificación de errores

#### Funciones Helper

- **`_leer_contenido_archivo(file_url_or_name)`**
  - Lee contenido de archivos adjuntos de Frappe
  - Maneja URLs y nombres de archivo
  - Retorna contenido como string o None

## Flujo de Trabajo

### Escenario 1: Primera vez (sin credenciales)
1. Usuario hace clic en "Timbrar en SAT"
2. Sistema detecta que no hay credenciales
3. Muestra formulario de carga de certificados
4. Usuario carga .cer, .key y contraseña
5. Usuario marca "Guardar para futuras facturas"
6. Sistema timbra y guarda credenciales

### Escenario 2: Con credenciales configuradas
1. Usuario hace clic en "Timbrar en SAT"
2. Sistema detecta credenciales existentes
3. Muestra opciones: "Usar Configuradas" o "Usar Otras"
4. Si elige "Configuradas": timbra directamente
5. Si elige "Otras": muestra formulario de carga

### Escenario 3: Error de credenciales
1. Timbrado falla por credenciales inválidas
2. Sistema detecta error tipo "credentials"
3. Muestra diálogo específico con opción de reintentar
4. Usuario puede cargar nuevas credenciales
5. Sistema reintenta el timbrado

## Seguridad

- Las credenciales temporales solo se usan durante el timbrado actual
- Si no se marca "guardar", los certificados no se persisten
- Las contraseñas no se almacenan en memoria más de lo necesario
- Todos los errores se registran en el log de Frappe

## Compatibilidad

El sistema mantiene compatibilidad con:
- Método legacy `timbrar_en_sat()`
- Estructura existente del doctype Configuración PAC
- Servicio PAC existente (`pac_service.py`)

## Mejoras Futuras Sugeridas

1. Validación de certificados antes de timbrar
2. Verificación de fecha de expiración de certificados
3. Cache de credenciales en sesión para múltiples facturas
4. Soporte para múltiples proveedores PAC
5. Historial de intentos de timbrado

## Testing

Para probar el sistema:

1. **Sin credenciales configuradas**:
   - Ir a una Factura de Venta submitted sin UUID
   - Hacer clic en "Timbrar en SAT"
   - Verificar que muestre el formulario de carga
   - Cargar certificados y probar timbrado

2. **Con credenciales configuradas**:
   - Configurar Configuración PAC con certificados
   - Ir a una factura y hacer clic en "Timbrar en SAT"
   - Verificar que muestre opciones
   - Probar ambas opciones

3. **Errores**:
   - Probar con certificados inválidos
   - Probar con contraseña incorrecta
   - Verificar que los diálogos de error sean apropiados
   - Verificar opción de reintentar

## Autor

Implementado por: RenderCores.com  
Fecha: Noviembre 2025  
Versión: 1.0
