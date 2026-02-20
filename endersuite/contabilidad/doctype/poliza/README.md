# Póliza Contable

## Descripción
DocType principal para registro de asientos contables (pólizas) en el sistema. Implementa el principio de **partida doble** donde cada movimiento debe estar cuadrado (Debe = Haber).

## Propósito
- Registrar operaciones contables diarias
- Mantener el libro diario de la empresa
- Clasificar movimientos por tipo (Diario, Ingreso, Egreso, Cheque)
- Validar el cuadre contable automáticamente

## Campos

### Información General
| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `fecha` | Datetime | Fecha y hora del movimiento | Sí |
| `tipo_de_poliza` | Select | Diario, Ingreso, Egreso, Cheque | Sí |
| `compañia` | Link | Compañía que registra la póliza | Sí |
| `año_fiscal` | Link | Año fiscal al que pertenece | Sí |
| `periodo` | Select | Mes (calculado automáticamente) | Sí |
| `concepto` | Small Text | Descripción del movimiento contable | Sí |

### Movimientos Contables (Child Table)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `table_qbss` | Table | Tabla hija con movimientos individuales |

### Totales (Calculados automáticamente)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total_debe` | Currency | Suma de todos los debe |
| `total_haber` | Currency | Suma de todos los haber |
| `diferencia` | Currency | Debe - Haber (debe ser 0) |
| `cuadra` | Check | Indicador si está cuadrada |

### Referencias
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `documento_origen` | Data | Factura, recibo, etc. |
| `observaciones` | Text | Notas adicionales |

## Configuración
- **Is Submittable**: Sí - Requiere aprobación (Submit) antes de ser oficial
- **Workflow States**: Draft → Submitted → Cancelled

## Validaciones automáticas

### 1. Cálculo de período
```python
def calcular_periodo(self):
    """Extrae el mes de la fecha y lo asigna automáticamente"""
    # Fecha: 2025-03-15 → Periodo: "Marzo"
```

### 2. Cálculo de totales
```python
def calcular_totales(self):
    """Suma todos los debe y haber de los movimientos"""
    # Actualiza: total_debe, total_haber, diferencia, cuadra
```

### 3. Validación de cuadre
```python
def validar_cuadre(self):
    """Valida que debe = haber (tolerancia: 0.01)"""
    # Si diferencia != 0 → frappe.throw (error)
```

### 4. Validación de movimientos
- Mínimo 2 movimientos contables
- Cada movimiento debe tener cuenta seleccionada
- Debe tener monto en Debe O Haber (no ambos)
- No puede tener debe = 0 y haber = 0

### 5. Validación de año fiscal
- La fecha debe estar dentro del rango del año fiscal
- El año fiscal debe estar en estado "Abierto"
- No permite pólizas en años fiscales "Cerrados"

## Funciones JavaScript

### Evento: `setup(frm)`
Configura el filtro de cuentas según el catálogo de la compañía:
```javascript
frm.set_query("cuenta", "table_qbss", function() {
    // Filtra solo cuentas del catálogo de la compañía
    // Llama a: get_cuentas_by_compania()
});
```

### Evento: `fecha(frm)`
Calcula automáticamente el período (mes) cuando se cambia la fecha.

### Evento: `compañia(frm)`
Auto-selecciona el año fiscal por defecto de la compañía.

### Indicadores visuales
- ✅ **Verde**: Póliza cuadrada (debe = haber)
- ⚠️ **Naranja**: Diferencia detectada (muestra monto)

## Funciones Python

### `get_cuentas_by_compania()`
Función whitelisted que filtra cuentas disponibles:
```python
@frappe.whitelist()
def get_cuentas_by_compania(doctype, txt, searchfield, start, page_len, filters):
    """
    Obtiene el catálogo de la compañía
    Retorna solo cuentas NO grupo del catálogo
    """
```

## Flujo de trabajo

### Crear una póliza
1. **Contabilidad > Poliza > New**
2. Seleccionar fecha (calcula periodo automáticamente)
3. Elegir tipo de póliza
4. Seleccionar compañía
5. Elegir año fiscal
6. Escribir concepto
7. Agregar movimientos en tabla:
   - Seleccionar cuenta (filtradas por catálogo)
   - Capturar debe O haber
8. Verificar que totales cuadren
9. Save (borrador)
10. Submit (oficial)

### Ejemplo práctico
```
Fecha: 15/01/2025
Tipo: Egreso
Concepto: Pago de renta de oficina

Movimientos:
| Cuenta              | Debe    | Haber   |
|---------------------|---------|---------|
| 5101 Gastos Renta   | 10,000  |         |
| 1182 IVA Acreditable|  1,600  |         |
| 1001 Bancos         |         | 11,600  |
|---------------------|---------|---------|
| TOTALES             | 11,600  | 11,600  | ✅ Cuadra
```

## Relaciones
```
Poliza (n)
    ├──> Compania (1)
    ├──> Anio Fiscal (1)
    └──> poliza_movimiento (n)
            └──> Catalogo de Cuentas (1)
```

## API / Integraciones

### Crear póliza vía código
```python
import frappe

poliza = frappe.get_doc({
    "doctype": "Poliza",
    "fecha": "2025-01-15 10:00:00",
    "tipo_de_poliza": "Diario",
    "compañia": "ACME",
    "año_fiscal": "2025",
    "concepto": "Ajuste de inventario",
    "table_qbss": [
        {
            "cuenta": "1001",
            "debe": 5000,
            "haber": 0
        },
        {
            "cuenta": "5001",
            "debe": 0,
            "haber": 5000
        }
    ]
})
poliza.insert()
poliza.submit()
```

## Reportes relacionados
- **Libro Diario**: Vista cronológica de todas las pólizas
- **Balance de Comprobación**: Sumas de debe y haber por cuenta
- **Estado de Resultados**: Ingresos vs Egresos

## Notas para desarrolladores

### Hooks importantes
- `before_validate`: Calcula período
- `validate`: Ejecuta todas las validaciones
- `on_submit`: Actualizar saldos de cuentas (pendiente implementar)
- `on_cancel`: Revertir saldos (pendiente implementar)

### Mejoras pendientes
- [ ] Actualizar saldos en Catalogo de Cuentas
- [ ] Generar número de póliza automático (P-D-00001)
- [ ] Integración con Facturación
- [ ] Conciliación bancaria
- [ ] Cierre de período

### Performance
- Usar índices en: `fecha`, `compañia`, `año_fiscal`
- Evitar cargar todas las cuentas, usar query optimizado
- Batch operations para múltiples pólizas

## Troubleshooting

### Error: "La póliza no está cuadrada"
- Verificar que suma de debe = suma de haber
- Revisar decimales (tolerancia: 0.01)

### Error: "Debe haber al menos 2 movimientos"
- Una póliza necesita mínimo 2 líneas (cargo y abono)

### Error: "No se pueden crear pólizas en el año fiscal cerrado"
- Cambiar estado del año fiscal a "Abierto"
- O seleccionar un año fiscal vigente

### Las cuentas no aparecen en el dropdown
- Verificar que la compañía tenga un catálogo asignado
- Verificar que las cuentas pertenezcan al catálogo correcto
- Verificar que las cuentas NO sean grupo (is_group = 0)
