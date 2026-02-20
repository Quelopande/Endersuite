# PAC Service - Servicio de Integración con Proveedor de Certificación

## Descripción General

El módulo `pac_service.py` es el servicio de integración con el Proveedor Autorizado de Certificación (PAC) para el timbrado de Comprobantes Fiscales Digitales por Internet (CFDI) versión 4.0 ante el SAT mexicano.

Actualmente integrado con **FacturaloPlus** (https://dev.facturaloplus.com).

## Propósito

Este servicio:
- Construye el JSON con la estructura CFDI 4.0 requerida por el PAC
- Firma digitalmente el comprobante usando los certificados CSD
- Envía la petición al API REST del PAC
- Procesa la respuesta (UUID, XML timbrado, PDF)
- Maneja errores de comunicación y validación

## Arquitectura

```
Factura de Venta (factura_de_venta.py)
           ↓
    pac_service.timbrar_factura()
           ↓
    [Construir JSON CFDI 4.0]
           ↓
    [Firmar con Certificados CSD]
           ↓
    [HTTP POST a FacturaloPlus]
           ↓
    [Procesar Respuesta]
           ↓
    {success, uuid, xml, pdf} → Backend
```

## Funciones Principales

### `timbrar_factura(factura, compania, certificado_contenido, llave_contenido, password_llave)`

Función principal que orquesta el proceso de timbrado.

**Parámetros:**
```python
factura: frappe.Document
    # Documento Factura de Venta con todos los datos fiscales
    
compania: frappe.Document
    # Documento Compañía con datos del emisor
    
certificado_contenido: str
    # Contenido del archivo .cer en formato PEM o DER
    
llave_contenido: str
    # Contenido del archivo .key en formato PEM o DER
    
password_llave: str
    # Contraseña para descifrar la llave privada
```

**Retorno:**
```python
{
    "success": True,
    "uuid": "12345678-1234-1234-1234-123456789012",  # Folio fiscal SAT
    "xml": "<cfdi:Comprobante ...>...</cfdi:Comprobante>",  # XML timbrado
    "pdf": "JVBERi0xLjQKJeLjz9MKMy..."  # PDF en base64
}

# O en caso de error:
{
    "success": False,
    "error": "Descripción del error"
}
```

**Flujo Interno:**
1. Obtener configuración del PAC (`Configuracion PAC`)
2. Construir JSON CFDI 4.0 con `_construir_json_cfdi()`
3. Preparar certificados con `_preparar_certificados()`
4. Enviar petición HTTP POST al PAC
5. Parsear respuesta y extraer UUID, XML, PDF
6. Retornar resultado estructurado

## Funciones Helper

### `_construir_json_cfdi(factura, compania)`

Construye el diccionario JSON con la estructura completa del CFDI 4.0.

**Estructura del JSON Generado:**

```json
{
  "Version": "4.0",
  "Serie": "A",
  "Folio": "123",
  "Fecha": "2025-11-19T12:30:00",
  "FormaPago": "03",
  "CondicionesDePago": "Contado",
  "SubTotal": "1000.00",
  "Moneda": "MXN",
  "Total": "1160.00",
  "TipoDeComprobante": "I",
  "MetodoPago": "PUE",
  "LugarExpedicion": "20000",
  
  "Emisor": {
    "Rfc": "AAA010101AAA",
    "Nombre": "Empresa Ejemplo SA de CV",
    "RegimenFiscal": "601"
  },
  
  "Receptor": {
    "Rfc": "XAXX010101000",
    "Nombre": "PUBLICO EN GENERAL",
    "DomicilioFiscalReceptor": "20000",
    "RegimenFiscalReceptor": "616",
    "UsoCFDI": "S01"
  },
  
  "Conceptos": [
    {
      "ClaveProdServ": "01010101",
      "Cantidad": "1",
      "ClaveUnidad": "H87",
      "Descripcion": "Producto de prueba",
      "ValorUnitario": "1000.00",
      "Importe": "1000.00",
      "ObjetoImp": "02",
      "Impuestos": {
        "Traslados": [
          {
            "Base": "1000.00",
            "Impuesto": "002",
            "TipoFactor": "Tasa",
            "TasaOCuota": "0.160000",
            "Importe": "160.00"
          }
        ]
      }
    }
  ],
  
  "Impuestos": {
    "TotalImpuestosTrasladados": "160.00",
    "Traslados": [
      {
        "Base": "1000.00",
        "Impuesto": "002",
        "TipoFactor": "Tasa",
        "TasaOCuota": "0.160000",
        "Importe": "160.00"
      }
    ]
  },
  
  "InformacionGlobal": {
    "Periodicidad": "01",
    "Meses": "11",
    "Año": "2025"
  }
}
```

**Consideraciones Especiales:**

#### Información Global (Público General)
Si el RFC del receptor es `XAXX010101000` (público general), se incluye el nodo `InformacionGlobal`:
```python
if receptor_rfc == "XAXX010101000":
    cfdi["InformacionGlobal"] = {
        "Periodicidad": "01",  # Diaria
        "Meses": mes_factura,  # 01-12
        "Año": anio_factura    # 2025
    }
```

#### Validaciones de Campos
- RFC: Validación de formato (12-13 caracteres alfanuméricos)
- Códigos Postales: 5 dígitos
- Claves SAT: Formatos específicos (ClaveProdServ: 8 dígitos)
- Importes: Dos decimales, formato string

### `_preparar_certificados(certificado_contenido, llave_contenido, password_llave)`

Procesa y prepara los certificados CSD para el timbrado.

**Proceso:**
1. Detectar formato del certificado (PEM o DER)
2. Si es DER, convertir a PEM usando `cryptography`
3. Decodificar llave privada con contraseña
4. Extraer número de serie del certificado
5. Retornar diccionarios con certificado y llave en base64

**Retorno:**
```python
{
    "certificado": {
        "content": "LS0tLS1CRUdJTi...",  # .cer en base64
        "filename": "certificado.cer"
    },
    "llave": {
        "content": "LS0tLS1CRUdJTi...",  # .key en base64
        "filename": "llave_privada.key"
    }
}
```

**Manejo de Errores:**
- Certificado inválido: Detecta formato incorrecto
- Contraseña incorrecta: Captura error de descifrado
- Llave corrupta: Valida integridad

## Integración con FacturaloPlus

### Endpoint API
```
POST https://dev.facturaloplus.com/api/rest/servicio/timbrarJSON2
```

### Autenticación
Mediante credenciales en el payload:
```python
payload = {
    "datosUsuario": {
        "usuario": pac_config.api_username,
        "password": pac_config.api_password
    },
    "certificado": { ... },
    "llave": { ... },
    "comprobante": { ... }  # JSON CFDI 4.0
}
```

### Headers
```python
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
```

### Timeout
- Timeout de lectura: 30 segundos
- Timeout de conexión: 10 segundos

```python
response = requests.post(url, json=payload, headers=headers, timeout=30)
```

## Procesamiento de Respuesta

### Respuesta Exitosa del PAC
```json
{
  "success": true,
  "comprobante": {
    "UUID": "12345678-1234-1234-1234-123456789012",
    "XML": "<cfdi:Comprobante ...>...</cfdi:Comprobante>",
    "PDF": "JVBERi0xLjQKJeLjz9MKMy..."
  }
}
```

### Extracción de Datos
```python
uuid = respuesta_json.get("comprobante", {}).get("UUID", "")
xml = respuesta_json.get("comprobante", {}).get("XML", "")
pdf = respuesta_json.get("comprobante", {}).get("PDF", "")

return {
    "success": True,
    "uuid": uuid,
    "xml": xml,
    "pdf": pdf
}
```

### Respuesta con Error del PAC
```json
{
  "success": false,
  "error": {
    "codigo": "301",
    "mensaje": "El certificado ha expirado"
  }
}
```

Procesamiento:
```python
if not respuesta_json.get("success"):
    error_data = respuesta_json.get("error", {})
    error_msg = error_data.get("mensaje", "Error desconocido del PAC")
    return {
        "success": False,
        "error": f"Error del PAC: {error_msg}"
    }
```

## Manejo de Errores

### Tipos de Error Capturados

#### 1. Errores de Certificados
```python
except ValueError as e:
    if "incorrect password" in str(e).lower():
        return {"success": False, "error": "Contraseña incorrecta"}
    elif "invalid certificate" in str(e).lower():
        return {"success": False, "error": "Certificado inválido"}
```

#### 2. Errores de Conexión
```python
except requests.exceptions.ConnectionError:
    return {
        "success": False,
        "error": "No se pudo conectar con el PAC. Verifique su conexión."
    }
except requests.exceptions.Timeout:
    return {
        "success": False,
        "error": "Tiempo de espera agotado. El PAC no respondió."
    }
```

#### 3. Errores HTTP
```python
if response.status_code != 200:
    return {
        "success": False,
        "error": f"Error HTTP {response.status_code}: {response.text}"
    }
```

#### 4. Errores de Validación SAT
```python
# El PAC retorna errores específicos del SAT
{
    "success": False,
    "error": "Error 301: Certificado revocado o caduco"
}
```

### Logging de Errores
Todos los errores se registran en el log de Frappe:
```python
frappe.log_error(
    message=f"Error timbrado: {str(e)}\nFactura: {factura.name}",
    title="Error PAC Service"
)
```

## Validaciones Pre-Timbrado

Antes de enviar al PAC, se validan:

### Datos del Emisor
- ✅ RFC válido (12-13 caracteres)
- ✅ Nombre fiscal no vacío
- ✅ Régimen fiscal del catálogo SAT
- ✅ Código postal válido (5 dígitos)

### Datos del Receptor
- ✅ RFC válido
- ✅ Nombre/Razón social
- ✅ Domicilio fiscal (código postal)
- ✅ Régimen fiscal
- ✅ Uso del CFDI

### Productos/Conceptos
- ✅ Al menos un concepto
- ✅ Clave de producto SAT (8 dígitos)
- ✅ Clave de unidad SAT (ej: H87, E48)
- ✅ Descripción no vacía
- ✅ Cantidad > 0
- ✅ Valor unitario > 0
- ✅ Importe calculado correctamente

### Impuestos
- ✅ Tasa de IVA válida (0.16, 0.08, 0.00)
- ✅ Base gravable correcta
- ✅ Importe de impuesto calculado
- ✅ Suma de traslados coincide con total

### Datos de Pago
- ✅ Forma de pago del catálogo SAT
- ✅ Método de pago (PUE/PPD)
- ✅ Moneda (MXN, USD, EUR)

## Seguridad

### Manejo de Credenciales
- Contraseñas nunca se almacenan en logs
- Certificados se transmiten en base64
- Comunicación HTTPS con el PAC
- Validación de certificados SSL

### Encriptación
- Llave privada protegida con contraseña
- Uso de `cryptography` para operaciones criptográficas
- Validación de firma digital

### Datos Sensibles
```python
# NO hacer esto:
frappe.log_error(f"Password: {password}")  # ❌

# Hacer esto:
frappe.log_error("Error de autenticación con PAC")  # ✅
```

## Dependencias

### Python Packages
```python
import frappe
import requests  # Peticiones HTTP
import base64    # Codificación de certificados
import json      # Serialización de datos
from cryptography import x509  # Procesamiento de certificados X.509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
```

### Instalación
```bash
pip install requests cryptography
```

## Configuración del Entorno

### Variables de Configuración PAC
Definidas en `Configuracion PAC` (SingleDocType):
```python
pac_config = frappe.get_single("Configuracion PAC")
api_url = pac_config.api_url
username = pac_config.api_username
password = pac_config.api_password
entorno = pac_config.entorno  # "Producción" o "Pruebas"
```

### URL de Pruebas vs Producción
```python
# Pruebas
api_url = "https://dev.facturaloplus.com/api/rest/servicio/timbrarJSON2"

# Producción
api_url = "https://www.facturaloplus.com/api/rest/servicio/timbrarJSON2"
```

## Extensión y Personalización

### Agregar Soporte para Otro PAC

1. **Crear adapter para nuevo PAC:**
```python
def timbrar_con_otro_pac(factura, compania, certificados):
    # Adaptar formato según API del PAC
    payload = _construir_payload_otro_pac(factura, compania)
    
    # Llamar API del nuevo PAC
    response = requests.post(otro_pac_url, json=payload)
    
    # Parsear respuesta según formato del PAC
    return _parsear_respuesta_otro_pac(response)
```

2. **Modificar `timbrar_factura()` para detectar PAC:**
```python
def timbrar_factura(...):
    pac_config = frappe.get_single("Configuracion PAC")
    
    if pac_config.pac_provider == "FacturaloPlus":
        return _timbrar_factoraloplus(...)
    elif pac_config.pac_provider == "OtroPAC":
        return timbrar_con_otro_pac(...)
```

### Agregar Validaciones Personalizadas

```python
def _validar_regla_negocio_custom(factura):
    """Validación específica del negocio"""
    if factura.total > 100000 and not factura.orden_compra:
        raise ValueError("Facturas mayores a $100k requieren orden de compra")

# Agregar al flujo:
def timbrar_factura(...):
    _validar_regla_negocio_custom(factura)
    # ... continuar timbrado
```

## Testing

### Datos de Prueba

**RFC de Prueba del SAT:**
```
Emisor: EKU9003173C9
Receptor: XAXX010101000 (Público General)
```

**Certificados de Prueba:**
Disponibles en: https://www.sat.gob.mx/aplicacion/operacion/31274/consulta-y-recupera-certificados-de-prueba

### Casos de Prueba

1. **Timbrado Exitoso**
```python
factura = frappe.get_doc("Factura de Venta", "FAC-001")
compania = frappe.get_doc("Compania", factura.compania)
resultado = timbrar_factura(factura, compania, cert, key, pwd)
assert resultado["success"] == True
assert "uuid" in resultado
```

2. **Error de Certificados**
```python
resultado = timbrar_factura(factura, compania, cert_invalido, key, pwd)
assert resultado["success"] == False
assert "certificado" in resultado["error"].lower()
```

3. **Error de Conexión**
```python
# Simular PAC caído
with patch('requests.post', side_effect=ConnectionError):
    resultado = timbrar_factura(...)
    assert "conexión" in resultado["error"].lower()
```

## Troubleshooting

### Problema: "Certificado inválido"
**Solución:**
- Verificar que el archivo .cer sea válido
- Confirmar que corresponde al RFC del emisor
- Revisar fecha de vigencia del certificado

### Problema: "Contraseña incorrecta"
**Solución:**
- Validar contraseña de la llave privada
- Verificar que .key corresponda al .cer

### Problema: "Error 301 - Certificado vencido"
**Solución:**
- Renovar certificados CSD en el portal del SAT
- Cargar nuevos certificados en la compañía

### Problema: "Timeout de conexión"
**Solución:**
- Verificar conectividad a internet
- Revisar que la URL del PAC sea correcta
- Confirmar que el firewall permita conexiones HTTPS

## Mejoras Futuras

- [ ] Cache de respuestas del PAC para reintentos
- [ ] Validación de certificados antes de enviar
- [ ] Soporte para cancelación de CFDI
- [ ] Integración con múltiples PACs
- [ ] Rate limiting para evitar saturar el PAC
- [ ] Modo offline con cola de timbrado
- [ ] Webhooks para notificaciones asíncronas

## Referencias

- [API FacturaloPlus](https://dev.facturaloplus.com/api-docs)
- [CFDI 4.0 - Anexo 20 SAT](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/anexo_20.htm)
- [Catálogos CFDI 4.0](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/catalogos_emision_cfdi_complemento_ce.htm)
- [Certificados de Sello Digital](https://www.sat.gob.mx/aplicacion/16660/genera-y-descarga-tus-archivos-a-traves-del-certifica)

## Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.0.0 | 2025-11 | Implementación inicial con FacturaloPlus |
| 1.0.1 | 2025-11 | Agregado soporte para InformacionGlobal (público general) |

## Autor

Implementado por: RenderCores  
Contacto: https://www.rendercores.com
