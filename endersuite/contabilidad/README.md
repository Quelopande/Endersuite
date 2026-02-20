# Módulo de Contabilidad - EnderSuite

## Visión General
Módulo completo de contabilidad que implementa el sistema de **pólizas contables mexicanas** con validaciones automáticas de partida doble, catálogos de cuentas jerárquicos y control de períodos fiscales.

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│                     CONTABILIDAD                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Anio Fiscal  │◄─────┤   Compania   │               │
│  └──────────────┘      └──────┬───────┘               │
│                               │                        │
│                               │ usa                    │
│                               ▼                        │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Calatologo   │◄─────┤  Catalogo de │               │
│  │  (Maestro)   │      │   Cuentas    │               │
│  └──────┬───────┘      └──────────────┘               │
│         │                     (Tree)                   │
│         │                                              │
│         │ contiene                                     │
│         ▼                                              │
│  ┌──────────────┐                                     │
│  │    Poliza    │                                     │
│  │  (Asiento)   │                                     │
│  └──────┬───────┘                                     │
│         │                                              │
│         │ tiene                                        │
│         ▼                                              │
│  ┌─────────────────┐                                  │
│  │ Poliza          │                                  │
│  │ Movimiento      │                                  │
│  │ (Child Table)   │                                  │
│  └─────────────────┘                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## DocTypes Principales

### 1. Anio Fiscal
**Propósito**: Define períodos fiscales anuales para la empresa.

**Campos clave**:
- Fecha inicio / fin
- Estado (Abierto/Cerrado)
- Es por defecto

**Documentación**: Ver `anio_fiscal/README.md`

---

### 2. Compania
**Propósito**: Representa una entidad legal que lleva contabilidad.

**Campos clave**:
- Nombre de la empresa
- Iniciales (autoname)
- Año fiscal
- Catálogo de cuentas

**Relaciones**:
- 1 Compañía → 1 Año Fiscal
- 1 Compañía → 1 Catálogo

**Documentación**: Ver `compania/README.md`

---

### 3. Calatologo (Catálogo Maestro)
**Propósito**: Agrupa planes de cuentas completos.

**Casos de uso**:
- Múltiples empresas con diferentes catálogos
- Diferentes versiones del catálogo (SAT 2024, SAT 2025)
- Catálogos por subsidiaria

**Relaciones**:
- 1 Catálogo → N Cuentas
- 1 Catálogo → N Compañías

📖 **[Ver documentación completa](calatologo/README.md)**

---

### 4. Catalogo de Cuentas
**Propósito**: Plan de cuentas jerárquico (Tree DocType).

**Características**:
- Estructura de árbol (grupos y cuentas finales)
- Pertenece a un Catálogo maestro
- Filtrado por catálogo

**Estructura típica**:
```
1000 - ACTIVO (grupo)
  ├─ 1100 - CIRCULANTE (grupo)
  │   ├─ 1101 - Caja (cuenta final)
  │   └─ 1102 - Bancos (cuenta final)
  └─ 1200 - FIJO (grupo)
      └─ 1201 - Equipo de cómputo (cuenta final)
```

**Documentación**: Ver `catalogo_de_cuentas/README.md`

---

### 5. Poliza (Póliza Contable)
**Propósito**: Asiento contable que registra operaciones financieras.

**Tipos de póliza**:
- **Diario**: Ajustes, depreciaciones, provisiones
- **Ingreso**: Ventas, cobros, ingresos
- **Egreso**: Compras, pagos, gastos
- **Cheque**: Pagos con cheque específicamente

**Validaciones automáticas**:
- ✅ Debe = Haber (partida doble)
- ✅ Fecha dentro del año fiscal
- ✅ Mínimo 2 movimientos
- ✅ Año fiscal abierto

**Estados del documento**:
- Draft (Borrador)
- Submitted (Aprobado)
- Cancelled (Cancelado)

📖 **[Ver documentación completa](poliza/README.md)**

---

### 6. Poliza Movimiento (Child Table)
**Propósito**: Detalle de cada línea del asiento contable.

**Campos**:
- Cuenta (filtrada por catálogo)
- Debe (cargo)
- Haber (abono)
- Referencia

**Comportamiento**:
- Debe XOR Haber (mutuamente excluyentes)
- Recálculo automático de totales
- Auto-llenado de nombre de cuenta

📖 **[Ver documentación completa](poliza_movimiento/README.md)**

---

## Flujo de Trabajo Completo

### Setup inicial

#### 1. Configurar año fiscal
```
Contabilidad > Anio Fiscal > New
- Nombre: "2025"
- Desde: 2025-01-01
- Hasta: 2025-12-31
- Estado: Abierto
- Es por defecto: ✓
```

#### 2. Crear catálogo maestro
```
Contabilidad > Calatologo > New
- Nombre: "Catálogo SAT 2025"
```

#### 3. Crear estructura de cuentas
```
Contabilidad > Catalogo de Cuentas > New
- Crear grupos principales (Activo, Pasivo, Capital, Ingresos, Egresos)
- Crear subcuentas bajo cada grupo
- Asignar todas al catálogo "Catálogo SAT 2025"
```

#### 4. Crear compañía
```
Contabilidad > Compania > New
- Nombre: "ACME S.A. de C.V."
- Iniciales: ACME (auto-generado)
- Año fiscal: 2025
- Catálogo: Catálogo SAT 2025
```

### Uso diario

#### 5. Registrar póliza
```
Contabilidad > Poliza > New
- Fecha: 2025-01-15
- Tipo: Egreso
- Compañía: ACME
- Concepto: "Pago de renta"

Movimientos:
| Cuenta              | Debe    | Haber   |
|---------------------|---------|---------|
| 5101 Gastos Renta   | 10,000  |         |
| 1182 IVA Acreditable|  1,600  |         |
| 1001 Bancos         |         | 11,600  |

✅ Save → Submit
```

---

## Reportes Disponibles

### Libro Diario (Pendiente)
Lista cronológica de todas las pólizas del período.

### Balance de Comprobación (Pendiente)
Sumas de debe y haber por cuenta.

### Estado de Resultados (Pendiente)
Ingresos - Egresos = Utilidad/Pérdida

### Balanza de Comprobación (Pendiente)
Saldos iniciales, movimientos y saldos finales.

---

## API / Desarrollo

### Crear póliza programáticamente

```python
import frappe

def crear_poliza_pago_nomina():
    poliza = frappe.get_doc({
        "doctype": "Poliza",
        "fecha": frappe.utils.now(),
        "tipo_de_poliza": "Egreso",
        "compañia": "ACME",
        "año_fiscal": "2025",
        "concepto": "Pago de nómina quincenal",
        "table_qbss": [
            {"cuenta": "5201", "debe": 50000, "haber": 0},
            {"cuenta": "2101", "debe": 0, "haber": 7500},
            {"cuenta": "2102", "debe": 0, "haber": 2500},
            {"cuenta": "1001", "debe": 0, "haber": 40000}
        ]
    })
    
    poliza.insert()
    poliza.submit()
    
    return poliza.name
```

### Consultar pólizas por período

```python
def obtener_polizas_mes(compania, año, mes):
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    polizas = frappe.get_all(
        "Poliza",
        filters={
            "compañia": compania,
            "periodo": meses[mes],
            "docstatus": 1  # Solo submitted
        },
        fields=["name", "fecha", "concepto", "total_debe", "total_haber"]
    )
    
    return polizas
```

### Obtener saldo de una cuenta (Pendiente implementar)

```python
def obtener_saldo_cuenta(cuenta, fecha_hasta):
    """
    TODO: Implementar cálculo de saldo
    Sumar todos los movimientos de la cuenta hasta la fecha
    """
    pass
```

---

## Hooks y Extensiones

### Hooks disponibles

```python
# hooks.py
doc_events = {
    "Poliza": {
        "on_submit": "endersuite.contabilidad.utils.actualizar_saldos",
        "on_cancel": "endersuite.contabilidad.utils.revertir_saldos"
    }
}
```

### Integraciones

- [ ] **Facturación**: Auto-crear pólizas desde facturas
- [ ] **Bancos**: Importar estados de cuenta y conciliar
- [ ] **Inventario**: Pólizas de movimientos de almacén
- [ ] **Nómina**: Pólizas automáticas de pago de nómina

---

## Normativas y Compliance

### México (SAT)
- ✅ Catálogo de cuentas según SAT
- ✅ Tipos de póliza (Diario, Ingreso, Egreso)
- ✅ Partida doble obligatoria
- ⏳ Exportación a formato XML (pendiente)
- ⏳ Balanza de comprobación XML (pendiente)

---

## Mejores Prácticas

### 1. Cierre de período
```
1. Verificar que todas las pólizas estén submitted
2. Generar reportes de cierre
3. Cambiar estado del Año Fiscal a "Cerrado"
4. Crear póliza de apertura para siguiente año
```

### 2. Nomenclatura de cuentas
```
1000-1999: ACTIVO
2000-2999: PASIVO
3000-3999: CAPITAL
4000-4999: INGRESOS
5000-5999: EGRESOS/COSTOS
```

### 3. Backup antes de cierre
```bash
bench --site local.dev backup --with-files
```

---

## Troubleshooting

### Problema: Póliza no cuadra
**Solución**: Verificar que la suma de debe = suma de haber con precisión de centavos.

### Problema: No aparecen cuentas
**Solución**: 
1. Verificar que la compañía tenga un catálogo asignado
2. Verificar que las cuentas pertenezcan a ese catálogo
3. Verificar que las cuentas no sean grupos

### Problema: No puedo crear póliza
**Solución**:
1. Verificar que el año fiscal esté "Abierto"
2. Verificar que la fecha esté dentro del año fiscal
3. Verificar permisos del rol

---

## Roadmap

### Versión 1.0 (Actual)
- ✅ Pólizas básicas
- ✅ Validación de partida doble
- ✅ Catálogos jerárquicos
- ✅ Control de años fiscales

### Versión 1.1 (Próxima)
- [ ] Libro Diario (reporte)
- [ ] Balance de Comprobación
- [ ] Actualización de saldos en cuentas
- [ ] Numeración automática de pólizas

### Versión 2.0 (Futuro)
- [ ] Estados financieros
- [ ] Presupuestos
- [ ] Centros de costo
- [ ] Conciliación bancaria
- [ ] Exportación XML SAT

---

## Contribuir

Para agregar funcionalidad al módulo:

1. Crear branch: `git checkout -b feature/nueva-funcionalidad`
2. Documentar en README.md correspondiente
3. Agregar tests unitarios
4. Commit con formato: `feat(Contabilidad): descripción - #numero`
5. Pull request a develop

---

## Contacto

**Equipo**: RenderCores.com  
**Email**: hola@rendercores.online  
**Licencia**: GPL-3.0
