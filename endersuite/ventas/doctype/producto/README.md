# Producto

## Descripción General

El DocType **Producto** representa los bienes y servicios que la empresa comercializa. Además de la información comercial estándar (precio, descripción, inventario), incluye los campos fiscales requeridos por el SAT para la emisión de CFDI 4.0.

## Propósito

Este doctype permite:
- Gestionar catálogo de productos y servicios
- Almacenar información comercial (precios, costos, inventario)
- Incluir datos fiscales del SAT (clave producto, unidad de medida)
- Calcular impuestos automáticamente
- Validar requisitos para facturación electrónica

## Estructura de Campos

### Información General
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `nombre_del_producto` | Data | Nombre comercial del producto/servicio |
| `codigo` | Data | SKU o código interno único |
| `descripcion` | Text | Descripción detallada del producto |
| `activo` | Check | Indica si el producto está disponible |

### Información Comercial
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `precio_de_venta` | Currency | Precio unitario de venta |
| `costo` | Currency | Costo de adquisición |
| `unidad_de_medida` | Link/Select | Unidad de medida comercial (pza, kg, lt) |
| `categoria` | Link | Categoría del producto |

### Información Fiscal (para CFDI)
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `clave_producto_servicio_sat` | Data | Sí | Clave del catálogo de productos/servicios SAT (8 dígitos) |
| `clave_unidad_sat` | Data | Sí | Clave de unidad de medida del catálogo SAT (ej: H87, E48) |
| `objeto_impuesto` | Select | Sí | 01=No objeto, 02=Sí objeto, 03=Sí objeto pero no obligado |
| `tasa_impuesto` | Percent | Condicional | Tasa de IVA u otro impuesto (0%, 8%, 16%) |

### Inventario (Opcional)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo_producto` | Select | Bien / Servicio |
| `mantener_stock` | Check | Controlar inventario |
| `cantidad_disponible` | Float | Existencia actual |

---

## Campos Fiscales SAT

### Clave Producto/Servicio SAT

La clave de producto/servicio es un código de **8 dígitos** del catálogo del SAT que clasifica el bien o servicio.

**Formato:** `########` (8 dígitos numéricos)

**Ejemplos Comunes:**

| Clave | Descripción |
|-------|-------------|
| 01010101 | Animal vivo para reproducción |
| 10101500 | Computadoras personales |
| 43211500 | Equipos de cómputo |
| 50202300 | Servicios de consultoría |
| 78101800 | Servicios de publicidad |
| 84111506 | Servicios de consultoría financiera |
| 90101501 | Servicios de comida y bebida |

**Búsqueda de Claves:**
1. Descargar catálogo completo: [Catálogo SAT](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/catalogos_emision_cfdi_complemento_ce.htm)
2. Buscar por palabra clave (ej: "computadora")
3. Seleccionar la clave más específica que describa el producto

**Validación:**
```python
def validate(self):
    if self.clave_producto_servicio_sat:
        if not re.match(r'^\d{8}$', self.clave_producto_servicio_sat):
            frappe.throw("La clave debe tener exactamente 8 dígitos")
```

### Clave Unidad SAT

Código que identifica la unidad de medida según el catálogo del SAT.

**Formato:** Código alfanumérico (ej: `H87`, `E48`, `KGM`)

**Unidades Comunes:**

| Clave | Descripción |
|-------|-------------|
| H87 | Pieza |
| E48 | Unidad de servicio |
| KGM | Kilogramo |
| LTR | Litro |
| MTR | Metro |
| E51 | Trabajo (para servicios por hora) |
| XBX | Caja |
| XPK | Paquete |
| SET | Conjunto |
| ACT | Actividad |

**Mapeo con Unidades Comerciales:**
```python
MAPEO_UNIDADES = {
    "Pieza": "H87",
    "Kilogramo": "KGM",
    "Litro": "LTR",
    "Metro": "MTR",
    "Servicio": "E48",
    "Hora": "E51"
}
```

**Importante:** La clave SAT puede no coincidir con la unidad de medida comercial. Por ejemplo:
- Comercialmente: "pza"
- SAT: "H87"

### Objeto de Impuesto

Indica cómo se gravan los impuestos para este producto.

**Valores:**

| Código | Descripción | Cuándo usar |
|--------|-------------|-------------|
| 01 | No objeto de impuesto | Productos exentos (libros, medicinas, alimentos básicos) |
| 02 | Sí objeto de impuesto | Productos gravados con IVA (mayoría de casos) |
| 03 | Sí objeto del impuesto y no obligado al desglose | Casos especiales |

**Uso Típico:**
- Productos con IVA 16% → `02`
- Productos con IVA 0% (tasa 0) → `02`
- Productos completamente exentos → `01`

### Tasa de Impuesto

Porcentaje de IVA u otro impuesto aplicable al producto.

**Tasas Comunes en México:**

| Tasa | Descripción | Productos |
|------|-------------|-----------|
| 16% | IVA General | Mayoría de productos y servicios |
| 8% | IVA Frontera | Productos vendidos en zona fronteriza |
| 0% | Tasa 0 | Alimentos básicos, medicinas, libros |
| 0% | Exento | Completamente exento (usar objeto_impuesto = 01) |

**Cálculo de Impuesto:**
```python
subtotal = cantidad * precio_unitario
impuesto = subtotal * (tasa_impuesto / 100)
total = subtotal + impuesto

# Ejemplo: 10 piezas × $100 c/u con IVA 16%
# Subtotal: $1,000
# IVA: $160
# Total: $1,160
```

---

## Integración con Sistema de Timbrado

### Validaciones Pre-Timbrado

Antes de incluir un producto en una factura, el sistema valida:

```python
def validar_producto_para_cfdi(producto):
    """Validar que el producto tenga datos SAT completos"""
    
    if not producto.clave_producto_servicio_sat:
        frappe.throw(f"El producto {producto.nombre_del_producto} no tiene clave SAT")
    
    if not producto.clave_unidad_sat:
        frappe.throw(f"El producto {producto.nombre_del_producto} no tiene clave de unidad SAT")
    
    if not producto.objeto_impuesto:
        frappe.throw(f"El producto {producto.nombre_del_producto} no tiene objeto de impuesto definido")
    
    # Si es objeto de impuesto, validar tasa
    if producto.objeto_impuesto == "02" and producto.tasa_impuesto is None:
        frappe.throw(f"El producto {producto.nombre_del_producto} requiere tasa de impuesto")
```

### Uso en el CFDI

Los datos del producto se mapean al nodo `<Conceptos>` del XML:

```python
# En pac_service.py
concepto = {
    "ClaveProdServ": producto.clave_producto_servicio_sat,
    "Cantidad": str(cantidad),
    "ClaveUnidad": producto.clave_unidad_sat,
    "Descripcion": producto.nombre_del_producto,
    "ValorUnitario": f"{precio_unitario:.2f}",
    "Importe": f"{importe:.2f}",
    "ObjetoImp": producto.objeto_impuesto
}

# Si es objeto de impuesto, agregar impuestos
if producto.objeto_impuesto == "02":
    concepto["Impuestos"] = {
        "Traslados": [{
            "Base": f"{importe:.2f}",
            "Impuesto": "002",  # IVA
            "TipoFactor": "Tasa",
            "TasaOCuota": f"{(producto.tasa_impuesto / 100):.6f}",
            "Importe": f"{impuesto_calculado:.2f}"
        }]
    }
```

**Ejemplo de XML Generado:**
```xml
<cfdi:Concepto 
    ClaveProdServ="43211500"
    Cantidad="10"
    ClaveUnidad="H87"
    Descripcion="Laptop Dell XPS 13"
    ValorUnitario="25000.00"
    Importe="250000.00"
    ObjetoImp="02">
    <cfdi:Impuestos>
        <cfdi:Traslados>
            <cfdi:Traslado
                Base="250000.00"
                Impuesto="002"
                TipoFactor="Tasa"
                TasaOCuota="0.160000"
                Importe="40000.00"/>
        </cfdi:Traslados>
    </cfdi:Impuestos>
</cfdi:Concepto>
```

---

## Casos de Uso

### Caso 1: Producto Físico con IVA 16%

```
Crear Producto:
  - Nombre: Laptop Dell XPS 13
  - Código: DELL-XPS13
  - Precio: $25,000.00
  - Clave SAT: 43211500 (Computadoras portátiles)
  - Unidad SAT: H87 (Pieza)
  - Objeto Impuesto: 02 (Sí objeto)
  - Tasa Impuesto: 16%

Al facturar:
  - Subtotal: $25,000
  - IVA 16%: $4,000
  - Total: $29,000
```

### Caso 2: Servicio de Consultoría

```
Crear Producto:
  - Nombre: Consultoría en Sistemas
  - Código: SRV-CONSULT
  - Precio: $5,000.00
  - Clave SAT: 84111506 (Servicios de consultoría)
  - Unidad SAT: E48 (Unidad de servicio)
  - Objeto Impuesto: 02
  - Tasa Impuesto: 16%

Al facturar:
  - Sistema usa unidad "E48" en lugar de horas
  - CFDI válido para servicios profesionales
```

### Caso 3: Producto con IVA 0% (Tasa 0)

```
Crear Producto:
  - Nombre: Pan Blanco
  - Código: ALM-PAN01
  - Precio: $30.00
  - Clave SAT: 50181602 (Pan)
  - Unidad SAT: KGM (Kilogramo)
  - Objeto Impuesto: 02 (Sí objeto)
  - Tasa Impuesto: 0%

Al facturar:
  - Subtotal: $30.00
  - IVA 0%: $0.00
  - Total: $30.00
  - XML incluye IVA con tasa 0.000000
```

### Caso 4: Producto Exento

```
Crear Producto:
  - Nombre: Libro de Texto
  - Código: LIB-TXT01
  - Precio: $200.00
  - Clave SAT: 55101500 (Libros)
  - Unidad SAT: H87 (Pieza)
  - Objeto Impuesto: 01 (No objeto)
  - Tasa Impuesto: (vacío)

Al facturar:
  - Total: $200.00
  - Sin nodo de impuestos en el concepto
```

---

## Validaciones y Errores Comunes

### Error: "Clave SAT inválida"
**Causa:** Clave no tiene 8 dígitos o no existe en el catálogo
**Solución:** 
- Verificar formato: `########` (8 dígitos)
- Buscar en catálogo oficial del SAT
- Usar clave genérica si es necesario: `01010101`

### Error: "Unidad SAT no válida"
**Causa:** Código de unidad no existe en catálogo SAT
**Solución:**
- Consultar catálogo de unidades del SAT
- Usar equivalencia correcta (ej: "Pieza" → "H87")
- No confundir con unidad de medida comercial

### Error: "Producto sin tasa de impuesto"
**Causa:** Objeto impuesto es "02" pero no hay tasa definida
**Solución:**
- Definir tasa de impuesto (0%, 8%, 16%)
- O cambiar objeto impuesto a "01" si es exento

### Error: "Descripción muy larga"
**Causa:** SAT limita la descripción del concepto
**Solución:**
- Mantener descripción concisa (máx 1000 caracteres)
- Usar campo descripción del producto para detalles

---

## Mejores Prácticas

### ✅ Hacer:

1. **Mantener catálogo actualizado:**
```python
# Revisar anualmente el catálogo del SAT
# Actualizar claves obsoletas
```

2. **Usar claves específicas:**
```python
# Preferir: 43211500 (Computadoras portátiles)
# Evitar: 01010101 (Genérico)
```

3. **Validar al guardar:**
```python
def validate(self):
    self.validar_clave_sat()
    self.validar_unidad_sat()
    self.validar_tasa_impuesto()
```

4. **Documentar claves:**
```python
# Agregar campo para descripción de la clave SAT
descripcion_clave_sat = fields.Text(
    label="Descripción Clave SAT",
    read_only=True
)
```

### ❌ No hacer:

1. **No omitir claves SAT:**
```python
# Mal: Facturar sin clave SAT
# Bien: Siempre incluir clave, usar genérica si es necesario
```

2. **No usar claves incorrectas:**
```python
# Mal: Usar 43211500 (computadoras) para servicios
# Bien: Buscar clave correcta para cada tipo
```

3. **No ignorar actualizaciones:**
```python
# El SAT actualiza catálogos periódicamente
# Revisar y actualizar productos regularmente
```

---

## Extensión y Personalización

### Búsqueda Automática de Clave SAT

```javascript
// En producto.js
frappe.ui.form.on('Producto', {
    nombre_del_producto: function(frm) {
        // Buscar sugerencias de claves SAT
        frappe.call({
            method: 'endersuite.ventas.doctype.producto.producto.buscar_clave_sat',
            args: {
                texto: frm.doc.nombre_del_producto
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('clave_producto_servicio_sat', r.message.clave);
                    frappe.msgprint(`Sugerencia: ${r.message.descripcion}`);
                }
            }
        });
    }
});
```

### Validación de Claves contra Catálogo

```python
def validate(self):
    """Validar que la clave exista en el catálogo SAT"""
    if self.clave_producto_servicio_sat:
        if not self.existe_en_catalogo_sat(self.clave_producto_servicio_sat):
            frappe.throw(f"Clave {self.clave_producto_servicio_sat} no válida")

def existe_en_catalogo_sat(self, clave):
    """Consultar tabla de catálogo SAT"""
    return frappe.db.exists("Catalogo SAT Productos", {"clave": clave})
```

### Mapeo Automático de Unidades

```python
def before_save(self):
    """Autocompletar clave unidad SAT desde unidad de medida"""
    if self.unidad_de_medida and not self.clave_unidad_sat:
        mapeo = {
            "Pieza": "H87",
            "Kilogramo": "KGM",
            "Litro": "LTR",
            "Metro": "MTR",
            "Servicio": "E48"
        }
        self.clave_unidad_sat = mapeo.get(self.unidad_de_medida)
```

---

## Integración con Otros Módulos

### Cotización → Orden → Factura

Los productos se propagan con sus datos fiscales:

```
Cotización (agregar producto)
    ↓ (incluye datos comerciales)
Orden de Venta (hereda producto)
    ↓ (mantiene datos fiscales)
Factura de Venta (hereda producto + datos SAT)
    ↓
Timbrado CFDI (usa claves SAT del producto)
```

### Inventario

Si se controla inventario:
```python
# Al crear factura
for item in factura.productos:
    producto = frappe.get_doc("Producto", item.producto)
    if producto.mantener_stock:
        # Reducir cantidad_disponible
        producto.cantidad_disponible -= item.cantidad
        producto.save()
```

---

## Referencias

- [Catálogo de Productos y Servicios SAT](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/catalogos_emision_cfdi_complemento_ce.htm)
- [Catálogo de Unidades de Medida SAT](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/catUnidad.xls)
- [Guía de Llenado CFDI 4.0](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/Instructivo_de_llenado_CFDI.pdf)
- Doctype relacionado: `Factura de Venta`, `Producto Factura de Ventas`
- Servicio relacionado: `pac_service.py`

---

## Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.0.0 | Original | Implementación inicial con datos comerciales |
| 2.0.0 | 2025-11 | Agregados campos fiscales SAT (clave producto, unidad, objeto impuesto, tasa) |

---

## Autor

Implementado por: RenderCores  
Contacto: https://www.rendercores.com
