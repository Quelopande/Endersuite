# Cliente

## Descripción General

El DocType **Cliente** representa a los compradores o receptores de facturas electrónicas en el sistema EnderSuite. Almacena tanto datos comerciales como la información fiscal requerida para el CFDI 4.0, incluyendo RFC, régimen fiscal, código postal y uso del comprobante.

## Propósito

Este doctype permite:
- Gestionar información de clientes para ventas
- Almacenar datos fiscales requeridos para CFDI
- Validar requisitos del SAT antes de facturar
- Servir como receptor en facturas electrónicas
- Manejar casos especiales como "Público General"

## Estructura de Campos

### Información General
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre_del_cliente` | Data | Nombre completo o razón social |
| `email` | Data | Correo electrónico |
| `telefono` | Data | Número de contacto |
| `direccion` | Text | Domicilio completo |

### Información Fiscal (para CFDI)
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `rfc` | Data | Sí | RFC del cliente (12-13 caracteres o XAXX010101000 para público general) |
| `codigo_postal_fiscal` | Data | Sí | Código postal del domicilio fiscal (5 dígitos) |
| `regimen_fiscal` | Link/Select | Sí | Régimen fiscal del catálogo SAT (ej: 601, 612, 616) |
| `uso_cfdi` | Select | Sí | Uso que el cliente dará al CFDI (G01, G03, P01, S01, etc.) |

### Campos Comerciales
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `condiciones_de_pago` | Link | Condición de pago predefinida |
| `vendedor_asignado` | Link | Vendedor responsable de la cuenta |
| `limite_de_credito` | Currency | Límite máximo de crédito |

---

## Información Fiscal para CFDI 4.0

### RFC (Registro Federal de Contribuyentes)

**Formato:**
- **Personas Morales:** 12 caracteres alfanuméricos (ej: `AAA010101AAA`)
- **Personas Físicas:** 13 caracteres alfanuméricos (ej: `AAAA010101ABC`)
- **Público General:** `XAXX010101000` (RFC genérico)

**Validación en Sistema:**
```python
def validar_rfc(rfc):
    if len(rfc) not in [12, 13]:
        frappe.throw("RFC debe tener 12 o 13 caracteres")
    if not rfc.isalnum():
        frappe.throw("RFC solo debe contener letras y números")
```

### Código Postal Fiscal

El código postal del domicilio fiscal del cliente es **obligatorio** para CFDI 4.0.

**Características:**
- Formato: 5 dígitos (ej: `20000`, `06600`)
- Debe corresponder a un CP válido del catálogo SAT
- Se incluye en el nodo `<Receptor>` del XML

**Uso en CFDI:**
```python
cfdi["Receptor"]["DomicilioFiscalReceptor"] = cliente.codigo_postal_fiscal
```

### Régimen Fiscal

Clave del régimen fiscal del cliente según el catálogo del SAT.

**Regímenes Comunes:**
| Clave | Descripción |
|-------|-------------|
| 601 | General de Ley Personas Morales |
| 603 | Personas Morales con Fines no Lucrativos |
| 605 | Sueldos y Salarios e Ingresos Asimilados a Salarios |
| 606 | Arrendamiento |
| 612 | Personas Físicas con Actividades Empresariales y Profesionales |
| 616 | Sin obligaciones fiscales |
| 621 | Incorporación Fiscal |
| 625 | Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas |
| 626 | Régimen Simplificado de Confianza |

**Público General:** Usar régimen `616` (Sin obligaciones fiscales)

### Uso del CFDI

Define el propósito fiscal que el cliente dará al comprobante.

**Usos Comunes:**
| Clave | Descripción | Típicamente usado por |
|-------|-------------|----------------------|
| G01 | Adquisición de mercancías | Empresas |
| G02 | Devoluciones, descuentos o bonificaciones | Empresas |
| G03 | Gastos en general | Empresas |
| I01 | Construcciones | Constructoras |
| I02 | Mobiliario y equipo de oficina por inversiones | Empresas |
| P01 | Por definir | Genérico |
| S01 | Sin efectos fiscales | Público general |
| CP01 | Pagos | Para complementos de pago |

**Selección Correcta:**
```
Cliente empresarial comprando productos → G01 (Adquisición de mercancías)
Cliente empresarial con gastos operativos → G03 (Gastos en general)
Público general → S01 (Sin efectos fiscales)
```

---

## Caso Especial: Público General

Para ventas al público general donde no se requieren datos fiscales específicos:

**Configuración:**
```
RFC: XAXX010101000
Nombre: PUBLICO EN GENERAL
Código Postal: (del establecimiento, ej: 20000)
Régimen Fiscal: 616 (Sin obligaciones fiscales)
Uso CFDI: S01 (Sin efectos fiscales)
```

**Impacto en el CFDI:**
Cuando el receptor es público general (`XAXX010101000`), el sistema agrega automáticamente el nodo `InformacionGlobal`:

```xml
<cfdi:InformacionGlobal 
    Periodicidad="01" 
    Meses="11" 
    Año="2025"/>
```

Este nodo es obligatorio desde CFDI 4.0 para operaciones con el público general.

---

## Integración con Sistema de Timbrado

### Validaciones Pre-Timbrado

Antes de timbrar una factura, el sistema valida que el cliente tenga:

```python
def validar_datos_fiscales_cliente(cliente):
    """Validar que el cliente tenga datos fiscales completos"""
    
    if not cliente.rfc:
        frappe.throw("El cliente debe tener RFC configurado")
    
    if not cliente.codigo_postal_fiscal:
        frappe.throw("El cliente debe tener código postal fiscal")
    
    if not cliente.regimen_fiscal:
        frappe.throw("El cliente debe tener régimen fiscal configurado")
    
    if not cliente.uso_cfdi:
        frappe.throw("El cliente debe tener uso del CFDI definido")
```

### Uso en el CFDI

Los datos del cliente se mapean al nodo `<Receptor>` del XML:

```python
# En pac_service.py
cfdi["Receptor"] = {
    "Rfc": cliente.rfc,
    "Nombre": cliente.nombre_del_cliente,
    "DomicilioFiscalReceptor": cliente.codigo_postal_fiscal,
    "RegimenFiscalReceptor": cliente.regimen_fiscal,
    "UsoCFDI": cliente.uso_cfdi
}
```

**Ejemplo de XML Generado:**
```xml
<cfdi:Receptor 
    Rfc="AAA010101AAA"
    Nombre="Empresa Cliente SA de CV"
    DomicilioFiscalReceptor="20000"
    RegimenFiscalReceptor="601"
    UsoCFDI="G01"/>
```

---

## Casos de Uso

### Caso 1: Cliente Empresarial

```
Crear Cliente:
  - Nombre: Corporativo Ejemplo SA de CV
  - RFC: COR010101ABC
  - Código Postal: 06600
  - Régimen Fiscal: 601 (General de Ley PM)
  - Uso CFDI: G01 (Adquisición de mercancías)

Al facturar:
  - Sistema valida datos fiscales ✅
  - Timbrado exitoso
  - Cliente puede deducir fiscalmente
```

### Caso 2: Persona Física con Actividad Empresarial

```
Crear Cliente:
  - Nombre: Juan Pérez López
  - RFC: PELJ800101ABC
  - Código Postal: 44100
  - Régimen Fiscal: 612 (Actividades Empresariales)
  - Uso CFDI: G03 (Gastos en general)

Al facturar:
  - Sistema incluye régimen 612
  - CFDI válido para deducción
```

### Caso 3: Público General

```
Crear Cliente:
  - Nombre: PUBLICO EN GENERAL
  - RFC: XAXX010101000
  - Código Postal: 20000 (del establecimiento)
  - Régimen Fiscal: 616 (Sin obligaciones)
  - Uso CFDI: S01 (Sin efectos fiscales)

Al facturar:
  - Sistema detecta RFC público general
  - Agrega nodo InformacionGlobal automáticamente
  - CFDI válido para ventas al público
```

---

## Validaciones y Errores Comunes

### Error: "RFC no válido"
**Causa:** Formato incorrecto o RFC no registrado en SAT
**Solución:** 
- Verificar longitud (12-13 caracteres)
- Validar en el portal del SAT
- Para público general usar: `XAXX010101000`

### Error: "Código postal inválido"
**Causa:** CP no existe en el catálogo SAT o formato incorrecto
**Solución:**
- Verificar que sea de 5 dígitos
- Consultar catálogo oficial del SAT
- Usar CP del domicilio fiscal registrado

### Error: "Uso de CFDI no compatible con régimen"
**Causa:** Combinación inválida de régimen fiscal y uso de CFDI
**Solución:**
- Público general (616) → Usar S01
- Empresas (601, 603) → Usar G01, G02, G03
- Asalariados (605) → Usar P01

### Error: "Cliente no encontrado"
**Causa:** Cliente eliminado o nombre incorrecto
**Solución:** Verificar que el cliente exista y esté activo

---

## Mejores Prácticas

### ✅ Hacer:

1. **Validar RFC antes de guardar:**
```python
def validate(self):
    if self.rfc and self.rfc != "XAXX010101000":
        self.validar_formato_rfc()
```

2. **Establecer valores predeterminados para público general:**
```python
def before_save(self):
    if self.rfc == "XAXX010101000":
        self.regimen_fiscal = "616"
        self.uso_cfdi = "S01"
```

3. **Solicitar datos fiscales en el onboarding:**
- Pedir RFC en el primer contacto
- Confirmar régimen fiscal
- Documentar uso típico del CFDI

4. **Mantener catálogos actualizados:**
- Revisar actualizaciones del SAT
- Actualizar opciones de régimen fiscal
- Validar nuevos usos de CFDI

### ❌ No hacer:

1. **No inventar RFC:**
- Siempre solicitar RFC oficial
- Para público general usar el RFC genérico: `XAXX010101000`

2. **No omitir validaciones:**
- Siempre validar datos fiscales antes de facturar
- No permitir facturas sin RFC válido

3. **No usar datos incorrectos:**
- RFC debe coincidir con el cliente real
- CP debe ser del domicilio fiscal, no de entrega

---

## Extensión y Personalización

### Agregar Validación de RFC con API del SAT

```python
def validate(self):
    """Validar RFC contra servicios del SAT"""
    if self.rfc and self.rfc != "XAXX010101000":
        if not self.validar_rfc_en_sat():
            frappe.throw(f"El RFC {self.rfc} no está registrado en el SAT")

def validar_rfc_en_sat(self):
    """Consultar API del SAT para validar RFC"""
    # Implementar integración con servicio de validación
    pass
```

### Autocompletar Datos Fiscales

```python
def on_update(self):
    """Autocompletar régimen según RFC"""
    if self.rfc and not self.regimen_fiscal:
        # Si RFC tiene 12 caracteres → Persona Moral
        if len(self.rfc) == 12:
            self.regimen_fiscal = "601"  # Default PM
        # Si RFC tiene 13 caracteres → Persona Física
        elif len(self.rfc) == 13:
            self.regimen_fiscal = "612"  # Default PF
```

### Validación de Código Postal

```python
def validate(self):
    """Validar formato de código postal"""
    if self.codigo_postal_fiscal:
        if not re.match(r'^\d{5}$', self.codigo_postal_fiscal):
            frappe.throw("El código postal debe tener 5 dígitos")
```

---

## Integración con Otros Módulos

### Cotización → Orden de Venta → Factura

El cliente se propaga automáticamente:

```
Cotización (seleccionar cliente)
    ↓
Orden de Venta (hereda cliente)
    ↓
Factura de Venta (hereda cliente + datos fiscales)
    ↓
Timbrado CFDI (usa datos fiscales del cliente)
```

### CRM → Cliente

Convertir Lead a Cliente:
```python
# Al convertir Lead
lead = frappe.get_doc("Lead", lead_name)
cliente = frappe.new_doc("Cliente")
cliente.nombre_del_cliente = lead.company_name
cliente.email = lead.email_id
cliente.telefono = lead.phone

# Solicitar datos fiscales adicionales
frappe.msgprint("Por favor complete los datos fiscales del cliente")
```

---

## Referencias

- [RFC - Validación SAT](https://www.sat.gob.mx/aplicacion/operacion/31274/consulta-tu-clave-en-el-rfc)
- [Catálogo de Regímenes Fiscales](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/catalogos_emision_cfdi_complemento_ce.htm)
- [Catálogo de Uso del CFDI](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/catCFDI.xls)
- [Códigos Postales - SEPOMEX](https://www.correosdemexico.gob.mx/SSLServicios/ConsultaCP/Descarga.aspx)
- Doctype relacionado: `Factura de Venta`
- Servicio relacionado: `pac_service.py`

---

## Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.0.0 | Original | Implementación inicial con datos comerciales |
| 2.0.0 | 2025-11 | Agregados campos fiscales para CFDI 4.0 (RFC, régimen, CP, uso CFDI) |

---

## Autor

Implementado por: RenderCores  
Contacto: https://www.rendercores.com
