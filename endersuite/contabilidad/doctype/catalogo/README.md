# Calatologo (Catálogo Maestro)

## Descripción
DocType maestro que agrupa y organiza diferentes catálogos de cuentas contables. Permite que una compañía tenga su propio catálogo de cuentas independiente.

## Propósito
- Crear múltiples catálogos de cuentas (ej: "SAT 2024", "Catálogo Principal", "Catálogo Subsidiaria")
- Asociar un catálogo completo a una o más compañías
- Separar los planes de cuentas por empresa o subsidiaria

## Campos

### Información General
| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| `nombre_del_catalogo` | Data | Nombre identificador del catálogo (ej: "SAT 2024") | Sí |
| `compañia` | Link | Compañía asociada al catálogo | No |

## Configuración
- **Autoname**: `field:nombre_del_catalogo` - El nombre se usa como ID único
- **Naming Rule**: By fieldname

## Relaciones
```
Calatologo (1)
    ├──> Compania (n) - Una compañía usa un catálogo
    └──> Catalogo de Cuentas (n) - Múltiples cuentas pertenecen a un catálogo
```

## Uso

### Crear un nuevo catálogo
1. Ir a: **Contabilidad > Calatologo > New**
2. Ingresar nombre descriptivo (ej: "Catálogo SAT 2024")
3. Opcionalmente asociar a una compañía
4. Guardar

### Mejores prácticas
- Usar nomenclatura descriptiva: "SAT 2024", "Plan de Cuentas 2025"
- Un catálogo por ejercicio fiscal o por normativa
- Copiar catálogos existentes para nuevos ejercicios

## Flujo de trabajo
```
1. Crear Calatologo
2. Crear/Asignar Catalogo de Cuentas al Calatologo
3. Asociar Calatologo a Compania
4. Usar cuentas del catálogo en Pólizas
```

## Notas para desarrolladores
- Este DocType no tiene validaciones complejas
- Es un maestro simple que actúa como agrupador
- La lógica de filtrado se implementa en Poliza y Catalogo de Cuentas
