# Año Fiscal (Anio Fiscal)

## Descripción
DocType que define el rango temporal en el cual se registran pólizas y movimientos contables. Implementa reglas estrictas para garantizar que el período cubra **exactamente un año calendario** (365 o 366 días en caso de año bisiesto).

Nombre interno del DocType: `Anio Fiscal`  
Etiqueta mostrada (traducción): `Año Fiscal`.

## Objetivos
- Controlar en qué intervalo se pueden crear pólizas.
- Permitir múltiples ejercicios (históricos y futuros).
- Definir el año fiscal por defecto de la compañía.
- Impedir creación de pólizas en años cerrados.

## Campos
| Campo | Tipo | Descripción | Requerido | Notas |
|-------|------|-------------|-----------|-------|
| `nombre` | Data | Identificador ("2025" o "2025-2026") | Sí | Autoname por campo. Único. |
| `desde` | Date | Fecha de inicio del ejercicio | Sí | Al establecerse, se autocalcula `hasta` si está vacío. |
| `hasta` | Date | Fecha de fin del ejercicio | Sí | Debe ser inclusivamente 365 o 366 días después de `desde`. Editable. |
| `empresa` | Link | (Opcional) Relación con entidad/cliente | No | Puede usarse para filtrar reportes futuros. |
| `es_por_defecto` | Check | Marca el ejercicio que se asignará automáticamente | No | Usado para seleccionar año fiscal en pólizas. |
| `estado` | Select | Borrador / Abierto / Cerrado | No | "Cerrado" bloquea nuevas pólizas. |

## Comportamiento Automático
### Autocálculo de Fecha Final
Si el usuario ingresa `desde` y deja `hasta` vacío:
1. Se calcula `hasta` = ( misma fecha del año siguiente ) - 1 día.
   - Ejemplo: 2025-01-01 → 2025-12-31
   - Ejemplo (bisiesto): 2024-02-29 → 2025-02-28

### Validación de Duración
En `validate()`:
- Se calcula duración inclusiva: `(hasta - desde).days + 1`
- Solo se permite 365 o 366.
- Si no cumple: `frappe.throw("El año fiscal debe durar exactamente 1 año…")`

### Edge Cases (Casos Especiales)
| Caso | Inicio | Fin esperado | Duración |
|------|--------|--------------|----------|
| Año normal | 2025-01-01 | 2025-12-31 | 365 |
| Año bisiesto inicia 1-Enero | 2024-01-01 | 2024-12-31 | 366 |
| Inicio en 29-Feb bisiesto | 2024-02-29 | 2025-02-28 | 366 |
| Inicio 30-Jun | 2025-06-30 | 2026-06-29 | 365 |

## Estados Recomendados
- Borrador: configuración inicial / edición.
- Abierto: se permiten pólizas dentro de rango.
- Cerrado: se bloquean nuevas pólizas (solo lectura y reportes).

## Flujo de Uso
```
1. Crear Año Fiscal (se autocompleta fecha fin si está vacía)
2. Guardar (validación de duración exacta)
3. Marcar "Es por defecto" si será el ejercicio activo
4. Cambiar estado a "Abierto"
5. Registrar pólizas dentro de su rango
6. Al cerrar el ejercicio → cambiar estado a "Cerrado"
```

## Integración con Pólizas
Al crear una póliza:
- Si no se eligió año fiscal manualmente, se busca el que tiene `es_por_defecto = 1`.
- Se valida que la fecha de la póliza esté entre `desde` y `hasta`.
- Se impide crear pólizas si `estado = Cerrado`.

## Código Clave (Resumen)
```python
class AnioFiscal(Document):
    def before_validate(self):
        if self.desde and not self.hasta:
            self.hasta = self._calcular_fecha_fin_automatica(self.desde)

    def validate(self):
        if not self.desde or not self.hasta:
            return
        inicio = getdate(self.desde)
        fin = getdate(self.hasta)
        if fin < inicio:
            frappe.throw("La fecha de fin no puede ser anterior a la fecha de inicio.")
        duracion = (fin - inicio).days + 1
        if duracion not in (365, 366):
            frappe.throw(f"El año fiscal debe durar exactamente 1 año. Duración actual: {duracion} días")
```

## Extensiones Futuras Propuestas
- [ ] Cierre automático que genere póliza de ajuste final.
- [ ] Generar Año Fiscal siguiente con botón "Crear siguiente".
- [ ] Validar que no existan superposiciones de rangos.
- [ ] Relacionar con períodos mensuales (DocType Periodo Contable).
- [ ] Auditoría: log de quién abrió/cerró el ejercicio.

## Buenas Prácticas
- Nunca modifiques fechas de un año fiscal con pólizas existentes (puede desajustar reportes).
- Usa estado "Cerrado" solo después de generar todos los reportes finales.
- No reutilices el mismo `nombre` para ejercicios distintos.

## Troubleshooting
| Problema | Causa | Solución |
|----------|-------|----------|
| Error: "Duración actual: 364 días" | Fecha fin manual incorrecta | Ajustar fecha fin al día anterior de la misma fecha del año siguiente |
| No autocompleta fecha fin | Campo `hasta` ya tenía valor | Borrar valor y volver a establecer `desde` |
| Póliza lanza "fuera del rango" | Fecha de póliza fuera de límites | Ajustar fecha de póliza o crear nuevo año fiscal |
| No asigna año fiscal por defecto | Ningún registro con `es_por_defecto = 1` | Editar el año correcto y marcarlo |

## Ejemplo Completo
```
Año Fiscal: 2025
Desde: 2025-01-01
Hasta: 2025-12-31 (autogenerado)
Estado: Abierto
Es por defecto: ✓
```

## Commit Relacionado
Documentación añadida en commit: `feat(Contabilidad): documentar Año Fiscal` (este archivo).

---
**Licencia**: GPL-3.0  
**Mantener coherencia**: Actualizar este README cada vez que cambie la lógica de validación.
