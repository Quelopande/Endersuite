# Producto Factura de Ventas

## Descripción General

**Producto Factura de Ventas** es un **Child DocType** (Tabla Hijo) que representa las líneas de detalle de una factura de venta. Cada fila de esta tabla contiene la información de un producto o servicio incluido en la factura, junto con su cantidad, precio, descuento e impuestos calculados.

**Tipo:** Child Table (no existe como documento independiente)  
**Doctype Padre:** Factura de Venta

## Propósito

Este doctype permite:
- Listar múltiples productos/servicios en una sola factura
- Calcular subtotales, descuentos e impuestos por línea
- Heredar datos fiscales del producto maestro
- Estructurar los conceptos del CFDI 4.0
- Mantener trazabilidad de cada item facturado

## Estructura de Campos

### Información del Producto
| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `producto` | Link | Sí | Link al doctype "Producto" |
| `descripcion` | Text | Sí | Descripción del producto (heredada o personalizada) |
| `cantidad` | Float | Sí | Cantidad vendida |
| `unidad` | Data | No | Unidad de medida comercial (pza, kg, lt) |

### Precios e Importes
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `precio_unitario` | Currency | Precio por unidad antes de descuento |
| `descuento_porcentaje` | Percent | Porcentaje de descuento (ej: 10%) |
| `descuento_monto` | Currency | Monto de descuento en pesos |
| `subtotal` | Currency | Cantidad × Precio - Descuento |

### Impuestos
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tasa_impuesto` | Percent | Tasa de IVA u otro impuesto (heredada del producto) |
| `monto_impuesto` | Currency | Impuesto calculado (subtotal × tasa) |
| `total` | Currency | Subtotal + Impuestos |

### Datos Fiscales SAT (heredados del Producto)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `clave_producto_sat` | Data | Clave de 8 dígitos del catálogo SAT |
| `clave_unidad_sat` | Data | Clave de unidad SAT (H87, KGM, etc.) |
| `objeto_impuesto` | Select | 01=No objeto, 02=Sí objeto, 03=No obligado |

---

## Funcionamiento

### Flujo de Datos

```
1. Usuario selecciona Producto
   ↓
2. Sistema carga automáticamente:
   - Descripción
   - Precio unitario
   - Tasa de impuesto
   - Clave producto SAT
   - Clave unidad SAT
   - Objeto de impuesto
   ↓
3. Usuario ingresa:
   - Cantidad
   - (Opcional) Descuento
   ↓
4. Sistema calcula:
   - Subtotal = Cantidad × Precio - Descuento
   - Impuesto = Subtotal × Tasa
   - Total = Subtotal + Impuesto
   ↓
5. Al guardar factura:
   - Se acumulan totales de todas las líneas
   - Factura.subtotal = Σ líneas.subtotal
   - Factura.total_impuestos = Σ líneas.monto_impuesto
   - Factura.total = Σ líneas.total
```

### Cálculos Automáticos

**Subtotal sin Descuento:**
```python
subtotal_sin_descuento = cantidad * precio_unitario
```

**Descuento:**
```python
if descuento_porcentaje:
    descuento_monto = subtotal_sin_descuento * (descuento_porcentaje / 100)
else:
    descuento_monto = 0
```

**Subtotal (Base Gravable):**
```python
subtotal = subtotal_sin_descuento - descuento_monto
```

**Impuesto:**
```python
if objeto_impuesto == "02":  # Sí objeto de impuesto
    monto_impuesto = subtotal * (tasa_impuesto / 100)
else:
    monto_impuesto = 0
```

**Total de la Línea:**
```python
total = subtotal + monto_impuesto
```

### Ejemplo de Cálculo

```
Producto: Laptop Dell XPS 13
Cantidad: 5
Precio Unitario: $20,000.00
Descuento: 10%
Tasa IVA: 16%

Cálculo:
1. Subtotal sin descuento: 5 × $20,000 = $100,000.00
2. Descuento 10%: $100,000 × 0.10 = $10,000.00
3. Subtotal: $100,000 - $10,000 = $90,000.00
4. IVA 16%: $90,000 × 0.16 = $14,400.00
5. Total línea: $90,000 + $14,400 = $104,400.00
```

---

## Integración con CFDI

Cada línea de `Producto Factura de Ventas` se convierte en un nodo `<Concepto>` en el XML del CFDI.

### Mapeo a XML

```python
# En pac_service.py
concepto = {
    "ClaveProdServ": linea.clave_producto_sat,           # 43211500
    "Cantidad": str(linea.cantidad),                      # "5"
    "ClaveUnidad": linea.clave_unidad_sat,               # "H87"
    "Descripcion": linea.descripcion,                     # "Laptop Dell XPS 13"
    "ValorUnitario": f"{linea.precio_unitario:.2f}",     # "20000.00"
    "Importe": f"{linea.subtotal:.2f}",                  # "90000.00"
    "Descuento": f"{linea.descuento_monto:.2f}",         # "10000.00"
    "ObjetoImp": linea.objeto_impuesto                   # "02"
}

# Si tiene impuestos
if linea.objeto_impuesto == "02":
    concepto["Impuestos"] = {
        "Traslados": [{
            "Base": f"{linea.subtotal:.2f}",              # "90000.00"
            "Impuesto": "002",                            # IVA
            "TipoFactor": "Tasa",
            "TasaOCuota": f"{(linea.tasa_impuesto/100):.6f}",  # "0.160000"
            "Importe": f"{linea.monto_impuesto:.2f}"      # "14400.00"
        }]
    }
```

### XML Generado

```xml
<cfdi:Concepto
    ClaveProdServ="43211500"
    Cantidad="5"
    ClaveUnidad="H87"
    Descripcion="Laptop Dell XPS 13"
    ValorUnitario="20000.00"
    Importe="90000.00"
    Descuento="10000.00"
    ObjetoImp="02">
    <cfdi:Impuestos>
        <cfdi:Traslados>
            <cfdi:Traslado
                Base="90000.00"
                Impuesto="002"
                TipoFactor="Tasa"
                TasaOCuota="0.160000"
                Importe="14400.00"/>
        </cfdi:Traslados>
    </cfdi:Impuestos>
</cfdi:Concepto>
```

---

## Validaciones

### Validaciones Automáticas

El sistema valida cada línea antes de permitir el timbrado:

```python
def validar_linea_factura(linea):
    """Validar que la línea tenga datos completos"""
    
    # Producto requerido
    if not linea.producto:
        frappe.throw("Todas las líneas deben tener un producto")
    
    # Cantidad positiva
    if linea.cantidad <= 0:
        frappe.throw(f"La cantidad debe ser mayor a 0 (línea {linea.idx})")
    
    # Precio positivo
    if linea.precio_unitario <= 0:
        frappe.throw(f"El precio debe ser mayor a 0 (línea {linea.idx})")
    
    # Datos SAT completos
    if not linea.clave_producto_sat:
        frappe.throw(f"Falta clave SAT en producto: {linea.producto}")
    
    if not linea.clave_unidad_sat:
        frappe.throw(f"Falta clave unidad SAT en producto: {linea.producto}")
    
    # Si es objeto de impuesto, debe tener tasa
    if linea.objeto_impuesto == "02" and linea.tasa_impuesto is None:
        frappe.throw(f"Falta tasa de impuesto en línea {linea.idx}")
```

### Validación de Totales

Al guardar la factura, se valida la suma de las líneas:

```python
def validate(self):
    """Validar totales de la factura"""
    
    # Calcular totales de las líneas
    subtotal_calculado = sum([linea.subtotal for linea in self.productos])
    impuestos_calculados = sum([linea.monto_impuesto for linea in self.productos])
    total_calculado = subtotal_calculado + impuestos_calculados
    
    # Comparar con totales de la factura
    if abs(self.subtotal - subtotal_calculado) > 0.01:
        frappe.throw("Discrepancia en subtotal")
    
    if abs(self.total - total_calculado) > 0.01:
        frappe.throw("Discrepancia en total")
```

---

## Uso en el Frontend

### JavaScript del Doctype Padre

```javascript
// En factura_de_venta.js

frappe.ui.form.on('Producto Factura de Ventas', {
    // Al seleccionar producto
    producto: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        if (row.producto) {
            // Cargar datos del producto
            frappe.db.get_doc('Producto', row.producto).then(producto => {
                frappe.model.set_value(cdt, cdn, 'descripcion', producto.nombre_del_producto);
                frappe.model.set_value(cdt, cdn, 'precio_unitario', producto.precio_de_venta);
                frappe.model.set_value(cdt, cdn, 'tasa_impuesto', producto.tasa_impuesto);
                frappe.model.set_value(cdt, cdn, 'clave_producto_sat', producto.clave_producto_servicio_sat);
                frappe.model.set_value(cdt, cdn, 'clave_unidad_sat', producto.clave_unidad_sat);
                frappe.model.set_value(cdt, cdn, 'objeto_impuesto', producto.objeto_impuesto);
            });
        }
    },
    
    // Al cambiar cantidad o precio, recalcular
    cantidad: function(frm, cdt, cdn) {
        calcular_totales_linea(frm, cdt, cdn);
    },
    
    precio_unitario: function(frm, cdt, cdn) {
        calcular_totales_linea(frm, cdt, cdn);
    },
    
    descuento_porcentaje: function(frm, cdt, cdn) {
        calcular_totales_linea(frm, cdt, cdn);
    }
});

function calcular_totales_linea(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    
    // Subtotal sin descuento
    let subtotal_sin_desc = row.cantidad * row.precio_unitario;
    
    // Descuento
    let descuento = subtotal_sin_desc * (row.descuento_porcentaje / 100);
    frappe.model.set_value(cdt, cdn, 'descuento_monto', descuento);
    
    // Subtotal
    let subtotal = subtotal_sin_desc - descuento;
    frappe.model.set_value(cdt, cdn, 'subtotal', subtotal);
    
    // Impuesto
    let impuesto = subtotal * (row.tasa_impuesto / 100);
    frappe.model.set_value(cdt, cdn, 'monto_impuesto', impuesto);
    
    // Total
    let total = subtotal + impuesto;
    frappe.model.set_value(cdt, cdn, 'total', total);
    
    // Recalcular totales de la factura
    calcular_totales_factura(frm);
}
```

---

## Casos de Uso

### Caso 1: Factura con Múltiples Productos

```
Factura de Venta: FAC-2025-001
  Línea 1:
    - Producto: Laptop Dell XPS 13
    - Cantidad: 5
    - Precio: $20,000
    - IVA: 16%
    - Total: $116,000
  
  Línea 2:
    - Producto: Mouse Logitech
    - Cantidad: 10
    - Precio: $500
    - IVA: 16%
    - Total: $5,800
  
  Línea 3:
    - Producto: Consultoría
    - Cantidad: 20 hrs
    - Precio: $1,000/hr
    - IVA: 16%
    - Total: $23,200

Totales Factura:
  - Subtotal: $125,000
  - IVA: $20,000
  - Total: $145,000
```

### Caso 2: Línea con Descuento

```
Línea:
  - Producto: Monitor LG 27"
  - Cantidad: 3
  - Precio: $5,000
  - Descuento: 15%
  - IVA: 16%

Cálculo:
  - Subtotal sin desc: 3 × $5,000 = $15,000
  - Descuento 15%: $2,250
  - Subtotal: $12,750
  - IVA 16%: $2,040
  - Total: $14,790
```

### Caso 3: Producto Exento

```
Línea:
  - Producto: Libro Técnico
  - Cantidad: 5
  - Precio: $300
  - Objeto Impuesto: 01 (No objeto)
  - IVA: 0%

Cálculo:
  - Subtotal: 5 × $300 = $1,500
  - IVA: $0
  - Total: $1,500
```

---

## Mejores Prácticas

### ✅ Hacer:

1. **Heredar datos del producto maestro:**
```python
# Siempre cargar desde el producto
linea.clave_producto_sat = producto.clave_producto_servicio_sat
linea.tasa_impuesto = producto.tasa_impuesto
```

2. **Validar antes de agregar líneas:**
```python
if not producto.clave_producto_servicio_sat:
    frappe.msgprint("Este producto no puede facturarse sin clave SAT")
    return False
```

3. **Recalcular automáticamente:**
```javascript
// Recalcular cuando cambien campos relevantes
cantidad: function() { calcular(); },
precio_unitario: function() { calcular(); },
descuento_porcentaje: function() { calcular(); }
```

4. **Mantener precisión:**
```python
# Usar 2 decimales para montos
subtotal = round(cantidad * precio, 2)
```

### ❌ No hacer:

1. **No permitir líneas sin producto:**
```python
# Mal: Permitir descripción manual sin link a producto
# Bien: Requerir siempre un producto maestro
```

2. **No modificar datos SAT en la línea:**
```python
# Mal: Permitir cambiar clave_producto_sat en la tabla
# Bien: Solo heredar del producto maestro
```

3. **No ignorar validaciones:**
```python
# Mal: Permitir cantidad = 0 o precio = 0
# Bien: Validar valores positivos
```

---

## Extensión y Personalización

### Agregar Campo de Lote o Serie

```python
# En producto_factura_de_ventas.json
{
    "fieldname": "lote",
    "label": "Lote",
    "fieldtype": "Data"
}
```

### Calcular Comisión del Vendedor

```python
# En factura_de_venta.py
def calcular_comisiones(self):
    for linea in self.productos:
        comision = linea.total * 0.05  # 5% de comisión
        # Guardar en tabla de comisiones
```

### Validación Personalizada de Stock

```python
def validate_linea_stock(linea):
    producto = frappe.get_doc("Producto", linea.producto)
    if producto.mantener_stock:
        if linea.cantidad > producto.cantidad_disponible:
            frappe.throw(f"Stock insuficiente: {linea.producto}")
```

---

## Referencias

- Doctype Padre: `Factura de Venta`
- Doctype Maestro: `Producto`
- Servicio relacionado: `pac_service.py`
- [Guía CFDI 4.0 - Nodo Conceptos](http://omawww.sat.gob.mx/tramitesyservicios/Paginas/documentos/Instructivo_de_llenado_CFDI.pdf)

---

## Historial de Cambios

| Versión | Fecha | Descripción |
|---------|-------|-------------|
| 1.0.0 | Original | Implementación inicial como tabla hijo |
| 2.0.0 | 2025-11 | Agregados campos fiscales SAT para CFDI 4.0 |

---

## Autor

Implementado por: RenderCores  
Contacto: https://www.rendercores.com
