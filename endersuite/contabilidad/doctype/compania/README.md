# Compañía

## Descripción General

El DocType **Compañía** representa la entidad emisora de facturas electrónicas en el sistema EnderSuite. Además de los datos básicos de la empresa, este doctype almacena la información fiscal y los certificados CSD (Certificado de Sello Digital) necesarios para el timbrado de CFDI ante el SAT.

## Propósito

Este doctype permite:
- Gestionar datos generales de la empresa (nombre, dirección, contacto)
- Almacenar información fiscal requerida para CFDI (RFC, régimen, código postal)
- Administrar certificados CSD para firma digital de comprobantes
- Generar iniciales automáticas para nomenclaturas
- Servir como emisor en facturas electrónicas

---

## Estructura de Campos

### Información General
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre_de_la_empresa` | Data | Nombre completo o razón social |
| `iniciales_de_la_empresa` | Data (Read Only) | Iniciales generadas automáticamente |
| `direccion` | Text | Domicilio completo |
| `telefono` | Data | Número de contacto |
| `email` | Data | Correo electrónico |

### Información Fiscal (para CFDI)
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `rfc` | Data | Sí | RFC de la empresa (12-13 caracteres) |
| `regimen_fiscal` | Link/Select | Sí | Clave del régimen fiscal SAT (ej: 601, 612) |
| `codigo_postal_fiscal` | Data | Sí | CP del domicilio fiscal (5 dígitos) |

### Certificados CSD (Certificado de Sello Digital)
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `archivo_certificado_cer` | Attach | Sí | Archivo .cer del CSD |
| `archivo_llave_key` | Attach | Sí | Archivo .key (llave privada) del CSD |
| `password_llave_privada` | Password | Sí | Contraseña para descifrar la llave privada |

---

## Lógica Personalizada: `compania.py`

### Hook: `before_save`

Genera automáticamente las iniciales de la empresa basándose en el nombre.

**Propósito:** Crear un identificador corto y único para usar en nomenclaturas (series de documentos, códigos, etc.).

**Funcionamiento:**

1. Toma el valor del campo `nombre_de_la_empresa`
2. Divide el nombre en palabras
3. Extrae la primera letra de cada palabra
4. Une las letras y las convierte a mayúsculas
5. Asigna el resultado a `iniciales_de_la_empresa`

**Ejemplo:**
```
"Mi Empresa de Ejemplo" → "MEDE"
"RenderCores México" → "RM"
"Grupo Industrial SA de CV" → "GISAC"
```

**Código:**
```python
def before_save(self):
    """
    Genera las iniciales de la empresa a partir del nombre
    antes de guardar el documento.
    """
    if self.nombre_de_la_empresa:
        palabras = self.nombre_de_la_empresa.split()
        iniciales = "".join([palabra[0] for palabra in palabras if palabra])
        self.iniciales_de_la_empresa = iniciales.upper()
```

---

## Integración con Sistema de Timbrado CFDI

### Validaciones para Timbrado

Antes de poder timbrar una factura, la compañía debe cumplir:

✅ **Datos Fiscales Completos**
```python
# En factura_de_venta.py
def validar_datos_fiscales_compania(compania):
    if not compania.rfc:
        frappe.throw("La compañía debe tener RFC configurado")
    if not compania.regimen_fiscal:
        frappe.throw("La compañía debe tener régimen fiscal")
    if not compania.codigo_postal_fiscal:
        frappe.throw("La compañía debe tener código postal fiscal")
```

✅ **Certificados CSD**
```python
def validar_certificados_compania(compania):
    faltantes = []
    if not compania.archivo_certificado_cer:
        faltantes.append("Certificado (.cer)")
    if not compania.archivo_llave_key:
        faltantes.append("Llave privada (.key)")
    if not compania.password_llave_privada:
        faltantes.append("Contraseña de llave privada")
    
    if faltantes:
        frappe.throw(f"Faltan: {', '.join(faltantes)}")
```

### Uso en el Timbrado

Cuando se timbra una factura, el sistema:

1. **Obtiene los datos de la compañía:**
```python
compania = frappe.get_doc("Compania", factura.compania)
```

2. **Usa los datos como Emisor en el CFDI:**
```python
cfdi["Emisor"] = {
    "Rfc": compania.rfc,
    "Nombre": compania.nombre_de_la_empresa,
    "RegimenFiscal": compania.regimen_fiscal
}
```

3. **Lee los certificados para firmar:**
```python
# Leer contenido de archivos adjuntos
cer_content = _leer_archivo_adjunto(compania.archivo_certificado_cer)
key_content = _leer_archivo_adjunto(compania.archivo_llave_key)
password = compania.get_password("password_llave_privada")

# Enviar al PAC para timbrado
resultado = pac_service.timbrar_factura(
    factura, compania, cer_content, key_content, password
)
```

---

## Certificados CSD (Certificado de Sello Digital)

### ¿Qué son los CSD?

Los Certificados de Sello Digital (CSD) son archivos emitidos por el SAT que permiten:
- Firmar digitalmente comprobantes fiscales (CFDI)
- Garantizar la autenticidad e integridad del documento
- Identificar al emisor de manera única

### Componentes del CSD

**Archivo .cer (Certificado Público)**
- Contiene la clave pública
- Se envía al PAC junto con el CFDI
- Formato: X.509 en DER o PEM
- No requiere contraseña

**Archivo .key (Llave Privada)**
- Contiene la clave privada para firmar
- Protegido con contraseña
- Formato: PKCS#8 cifrado
- **¡Nunca compartir públicamente!**

**Contraseña**
- Requerida para descifrar el archivo .key
- Definida al generar los certificados en el portal del SAT
- Se almacena de forma segura en Frappe (campo Password)

### Obtención de Certificados CSD

1. Ingresar al portal del SAT: https://www.sat.gob.mx
2. Navegar a: **Certificados → Certificado de Sello Digital**
3. Generar o renovar CSD
4. Descargar archivos .cer y .key
5. Guardar la contraseña definida

### Carga en EnderSuite

1. Ir a: **Contabilidad → Compañía → [Tu Empresa]**
2. Scroll a la sección "Certificados CSD"
3. Adjuntar `archivo_certificado_cer` (.cer)
4. Adjuntar `archivo_llave_key` (.key)
5. Ingresar `password_llave_privada`
6. Guardar

### Vigencia

- Los CSD tienen vigencia de **4 años**
- El sistema validará la fecha de expiración antes de timbrar
- Renovar antes del vencimiento para evitar interrupciones

---

## Seguridad

### Protección de Datos Sensibles

**Contraseña de Llave Privada**
- Campo tipo `Password` en Frappe
- Se almacena cifrada en la base de datos
- Solo se descifra en memoria durante el timbrado
- No se expone en logs ni respuestas del cliente

**Archivos Adjuntos**
- Los archivos .cer y .key se almacenan en el sistema de archivos privado de Frappe
- Solo accesibles mediante permisos de usuario
- No se exponen vía URL pública

**Acceso Restringido**
```python
# Solo usuarios con rol "System Manager" o "Accounts Manager"
# pueden ver y editar certificados
```

### Buenas Prácticas

✅ **Hacer:**
- Renovar certificados antes del vencimiento
- Usar contraseñas robustas
- Limitar acceso a usuarios autorizados
- Hacer respaldo de certificados en lugar seguro

❌ **No hacer:**
- Compartir archivos .key por correo
- Usar la misma contraseña para todos los sistemas
- Almacenar certificados en repositorios Git
- Exponer contraseñas en logs o código

---

## Casos de Uso

### Caso 1: Configuración Inicial de Compañía

```
1. Crear nuevo documento Compañía
2. Llenar datos generales (nombre, dirección, contacto)
3. Ingresar datos fiscales:
   - RFC: AAA010101AAA
   - Régimen Fiscal: 601 (General de Ley Personas Morales)
   - Código Postal: 20000
4. Cargar certificados CSD:
   - Adjuntar .cer
   - Adjuntar .key
   - Ingresar contraseña
5. Guardar
6. Sistema genera iniciales automáticamente: "AAA"
```

### Caso 2: Renovación de Certificados Vencidos

```
1. Obtener nuevos CSD del portal SAT
2. Abrir documento Compañía existente
3. Reemplazar archivos adjuntos:
   - Eliminar .cer y .key antiguos
   - Adjuntar nuevos certificados
4. Actualizar contraseña si cambió
5. Guardar
6. Validar con factura de prueba
```

### Caso 3: Configurar Múltiples Compañías

```
# Para empresas con varias razones sociales
1. Crear documento Compañía por cada RFC
2. Cada una con sus propios certificados CSD
3. Al crear factura, seleccionar la compañía emisora correspondiente
```

---

## Validaciones y Errores Comunes

### Error: "Certificado inválido"
**Causa:** Archivo .cer corrupto o no corresponde al RFC
**Solución:** Descargar nuevamente del SAT y verificar RFC

### Error: "Contraseña incorrecta"
**Causa:** La contraseña no coincide con el archivo .key
**Solución:** Verificar contraseña definida al generar CSD

### Error: "Certificado vencido" (Error 301 del SAT)
**Causa:** CSD ha expirado
**Solución:** Renovar certificados en el portal del SAT

### Error: "RFC no válido"
**Causa:** Formato incorrecto del RFC (debe ser 12-13 caracteres)
**Solución:** Verificar formato: AAA010101AAA (personas morales) o AAAA010101ABC (personas físicas)

---

## Extensión y Personalización

### Agregar Campos Fiscales Adicionales

```python
# En compania.json, agregar campo:
{
    "fieldname": "curp",
    "label": "CURP",
    "fieldtype": "Data",
    "length": 18
}
```

### Validación Personalizada de RFC

```python
# En compania.py
import re

def validate(self):
    """Validar formato de RFC"""
    if self.rfc:
        patron = r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$'
        if not re.match(patron, self.rfc):
            frappe.throw("Formato de RFC inválido")
```

### Hook Personalizado para Certificados

```python
def validate(self):
    """Validar vigencia de certificados"""
    if self.archivo_certificado_cer:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        
        cert_content = self._leer_certificado()
        cert = x509.load_der_x509_certificate(cert_content, default_backend())
        
        if cert.not_valid_after < datetime.now():
            frappe.throw("El certificado CSD ha vencido. Renuévelo en el SAT.")
```

---

## Referencias

- [Certificados de Sello Digital - SAT](https://www.sat.gob.mx/aplicacion/16660/genera-y-descarga-tus-archivos-a-traves-del-certifica)
- [Régimen Fiscal - Catálogo SAT](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/catalogos_emision_cfdi_complemento_ce.htm)
- Doctype relacionado: `Factura de Venta`
- Servicio relacionado: `pac_service.py`

---

## Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.0.0 | Original | Implementación inicial con iniciales automáticas |
| 2.0.0 | 2025-11 | Agregados campos fiscales y soporte para certificados CSD |

---

## Autor

Implementado por: RenderCores  
Contacto: https://www.rendercores.com

### Hook: `before_save`

El archivo `compania.py` implementa el hook (gancho) `before_save`.

* **Propósito:** Generar automáticamente las iniciales de la empresa (`iniciales_de_la_empresa`) basándose en el nombre de la empresa (`nombre_de_la_empresa`).
* **Disparador:** Este método se ejecuta automáticamente cada vez que un documento "Compania" se crea o se guarda.

#### Funcionamiento:

1.  El método toma el valor del campo `nombre_de_la_empresa`.
2.  Divide el nombre en una lista de palabras (ej: "Mi Empresa de Ejemplo" -> `["Mi", "Empresa", "de", "Ejemplo"]`).
3.  Toma la primera letra de cada palabra (ej: `["M", "E", "d", "E"]`).
4.  Une estas letras y las convierte a mayúsculas (ej: "MEDE").
5.  Asigna este valor al campo `iniciales_de_la_empresa`, que está configurado como "Solo Lectura" (Read Only) en el DocType, para que el usuario no pueda modificarlo manualmente.

#### Fragmento de Código

```python
# apps/endersuite/endersuite/contabilidad/doctype/compania/compania.py

from frappe.model.document import Document

class Compania(Document):
    
    def before_save(self):
        """
        Genera las iniciales de la empresa a partir del nombre
        antes de guardar el documento.
        """
        # Verifica que el campo 'nombre_de_la_empresa' tenga datos
        if self.nombre_de_la_empresa:
            
            # Divide el nombre por espacios
            palabras = self.nombre_de_la_empresa.split()
            
            # Genera las iniciales (tomando la primera letra de cada palabra)
            iniciales = "".join([palabra[0] for palabra in palabras if palabra])
            
            # Asigna el resultado en mayúsculas al campo de iniciales
            self.iniciales_de_la_empresa = iniciales.upper()

```
