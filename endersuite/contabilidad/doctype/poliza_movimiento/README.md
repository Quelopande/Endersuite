# Poliza Movimiento (Child Table)

## Descripción
DocType de tabla hija (Child Table) que contiene los movimientos contables individuales de una póliza. Cada fila representa un cargo (debe) o un abono (haber) a una cuenta específica.

## Propósito
- Detallar cada línea de un asiento contable
- Aplicar el principio de partida doble
- Vincular cuentas del catálogo con montos específicos

## Campos

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `cuenta` | Link | Cuenta del Catálogo de Cuentas | Sí |
| `nombre_cuenta` | Data | Nombre descriptivo (auto-llenado) | No |
| `debe` | Currency | Monto en Debe (cargo) | No* |
| `haber` | Currency | Monto en Haber (abono) | No* |
| `referencia` | Data | Referencia adicional | No |

\* Al menos uno debe tener valor (debe O haber, no ambos)

## Configuración
- **istable**: 1 (Es tabla hija)
- **editable_grid**: 1 (Edición en línea habilitada)
- **Parent DocType**: Poliza

## Validaciones automáticas

### 1. Auto-llenado de nombre de cuenta
```javascript
fetch_from: "cuenta.cuenta"
fetch_if_empty: 1
```
Cuando se selecciona una cuenta, su nombre se copia automáticamente.

### 2. Exclusión mutua (Debe XOR Haber)
El comportamiento JavaScript asegura que:
- Si se captura **Debe** > 0 → se limpia **Haber**
- Si se captura **Haber** > 0 → se limpia **Debe**
- No puede tener ambos al mismo tiempo

### 3. Recálculo de totales
Cada cambio en debe/haber dispara `recalc_totals()` que actualiza:
- `total_debe` en la póliza padre
- `total_haber` en la póliza padre
- `diferencia` (debe - haber)
- `cuadra` (boolean)

## Funciones JavaScript

### Evento: `cuenta(frm, cdt, cdn)`
```javascript
// Auto-llena el nombre de la cuenta desde Catalogo de Cuentas
frappe.db.get_value("Catalogo de Cuentas", row.cuenta, "cuenta")
```

### Evento: `debe(frm, cdt, cdn)`
```javascript
// Si debe > 0, limpia haber
// Recalcula totales de la póliza
```

### Evento: `haber(frm, cdt, cdn)`
```javascript
// Si haber > 0, limpia debe
// Recalcula totales de la póliza
```

### Función: `recalc_totals(frm)`
```javascript
// Suma todos los debe/haber de todas las filas
// Actualiza campos calculados en Poliza
```

## Filtrado de cuentas

Las cuentas disponibles se filtran mediante query personalizado:
```javascript
frm.set_query("cuenta", "table_qbss", function() {
    return {
        query: "endersuite.contabilidad.doctype.poliza.poliza.get_cuentas_by_compania",
        filters: { compania: frm.doc.compañia }
    };
});
```

Esto garantiza que solo se muestren:
- Cuentas del catálogo de la compañía seleccionada
- Cuentas que NO son grupo (`is_group = 0`)

## Ejemplo de uso

### Movimiento simple (Pago de nómina)
```
| Cuenta                    | Debe    | Haber   |
|---------------------------|---------|---------|
| 5201 Sueldos y Salarios   | 50,000  |         |
| 2101 ISR por Pagar        |         |  7,500  |
| 2102 IMSS por Pagar       |         |  2,500  |
| 1001 Bancos               |         | 40,000  |
```

### Movimiento compuesto (Venta con IVA)
```
| Cuenta                    | Debe    | Haber   |
|---------------------------|---------|---------|
| 1001 Bancos               | 11,600  |         |
| 4001 Ingresos por Ventas  |         | 10,000  |
| 2001 IVA por Pagar        |         |  1,600  |
```

## Relaciones
```
poliza_movimiento (n)
    ├──> Poliza (1) - Parent
    └──> Catalogo de Cuentas (1) - Cuenta usada
```

## Reglas de negocio

### ✅ Válido
- Debe: 1000, Haber: 0
- Debe: 0, Haber: 1000
- Referencia opcional

### ❌ Inválido
- Debe: 1000, Haber: 500 (no puede tener ambos)
- Debe: 0, Haber: 0 (debe tener al menos uno)
- Sin cuenta seleccionada

## Notas para desarrolladores

### Acceso al parent desde Python
```python
# En poliza.py
for movimiento in self.table_qbss:
    cuenta = movimiento.cuenta
    debe = movimiento.debe
    haber = movimiento.haber
```

### Acceso al parent desde JavaScript
```javascript
// En poliza_movimiento.js
const row = locals[cdt][cdn];
const parent = frm.doc; // Acceso al documento Poliza
```

### Performance
- Usar `editable_grid: 1` para edición rápida
- Evitar validaciones pesadas en cada keystroke
- Usar debounce para recálculos frecuentes

### Mejoras pendientes
- [ ] Agregar campo "centro de costo"
- [ ] Agregar campo "proyecto"
- [ ] Permitir adjuntar documentos por línea
- [ ] Agregar descripción por movimiento
- [ ] Validar contra presupuesto

## Troubleshooting

### El nombre de cuenta no se auto-llena
- Verificar que `fetch_from` esté configurado
- Verificar que la cuenta existe en Catalogo de Cuentas
- Clear cache y recargar

### Los totales no se actualizan
- Verificar que el evento `debe/haber` esté registrado
- Verificar que `recalc_totals()` esté definida
- Revisar console del navegador por errores JS

### No aparecen cuentas en el dropdown
- Verificar que la compañía tenga un catálogo asignado
- Verificar que el `set_query` esté en el evento `setup()`
- Verificar que las cuentas no sean grupos
