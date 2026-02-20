# Sistema de Formatos de Ticket Personalizables

## 📋 Descripción

Sistema que permite a los clientes crear y personalizar múltiples formatos de tickets para impresión, con total control sobre el diseño, contenido y estilos.

## ✨ Características

### 1. **Múltiples Formatos**
- Crea tantos formatos de ticket como necesites
- Un formato puede ser marcado como "Predeterminado"
- Cada Perfil de POS puede tener su propio formato asignado

### 2. **Configuración Visual**
- **Ancho del Ticket**: 58mm, 80mm, o Carta
- **Fuente**: Courier New, Arial, Roboto, Monospace
- **Tamaño de Fuente**: 8-12px
- **Alineación del Encabezado**: Izquierda, Centro, Derecha
- **Mostrar Logo**: Opcional

### 3. **Plantillas HTML Editables**
Cada sección es completamente personalizable con HTML:

#### **Encabezado**
Variables disponibles:
- `{{ doc.name }}` - Número de nota de venta
- `{{ doc.fecha_y_hora_de_venta }}` - Fecha y hora
- `{{ doc.cliente }}` - Nombre del cliente
- `{{ perfil_pos }}` - Nombre del perfil POS
- `{{ compania.name }}` - Nombre de la compañía
- `{{ compania.razon_social }}` - Razón social

#### **Items/Productos**
Variables disponibles:
- `{{ item.producto }}` - Nombre del producto
- `{{ item.cantidad }}` - Cantidad
- `{{ item.precio_unitario }}` - Precio unitario
- `{{ item.total_linea }}` - Total de la línea
- `{{ item.descuento_porcentaje }}` - Descuento aplicado
- `{{ item.impuesto }}` - Tipo de impuesto

#### **Pie de Página**
Variables disponibles:
- `{{ doc.subtotal }}` - Subtotal
- `{{ doc.total_impuestos }}` - Total de impuestos
- `{{ doc.total_final }}` - Total final
- `{{ doc.cambio }}` - Cambio entregado
- `{{ doc.metodos_pago_nota }}` - Lista de métodos de pago
- `{{ doc.sesion_pos }}` - Sesión POS
- `{{ frappe.session.user }}` - Usuario/Cajero

### 4. **CSS Personalizado**
Agrega tus propios estilos CSS para personalizar:
- Colores
- Márgenes y espaciados
- Bordes y separadores
- Tamaños de fuente específicos
- Cualquier otro estilo CSS

### 5. **Vista Previa**
- Botón "Vista Previa" en cada formato
- Usa la última nota de venta creada como ejemplo
- Abre en nueva ventana para probar impresión

## 🚀 Uso

### Crear un Nuevo Formato

1. Ve a: **Ventas → Formato de Ticket → Nuevo**
2. Completa:
   - Nombre del Formato (ej: "Ticket Compacto", "Ticket Premium")
   - Descripción (opcional)
   - Marca "Predeterminado" si quieres que sea el formato por defecto
3. Configura el diseño:
   - Selecciona ancho del ticket
   - Elige fuente y tamaño
   - Define alineación
4. Personaliza las plantillas HTML (o deja las predeterminadas)
5. Agrega CSS personalizado (opcional)
6. Guardar

### Asignar Formato a un Perfil POS

1. Ve a: **Ventas → Perfil de POS → [Tu Perfil]**
2. En la sección "Opciones"
3. Campo "Formato de Ticket": Selecciona el formato deseado
4. Guardar

### Flujo de Impresión

El sistema elige el formato en este orden:

1. **Formato del Perfil POS** (si está configurado)
2. **Formato Predeterminado** (si hay uno marcado)
3. **Primer formato disponible**
4. **Formato de impresión estándar** (fallback)

## 📝 Ejemplos de Personalización

### Ejemplo 1: Ticket Minimalista

```html
<!-- header_html -->
<div style="text-align: center; margin-bottom: 10px;">
    <h3>{{ perfil_pos }}</h3>
    <p>{{ doc.name }} | {{ doc.fecha_y_hora_de_venta[:16] }}</p>
</div>
```

### Ejemplo 2: Ticket con Logo

```html
<!-- header_html -->
<div style="text-align: center;">
    {% if compania and compania.logo %}
    <img src="{{ compania.logo }}" style="max-width: 100px; margin-bottom: 10px;">
    {% endif %}
    <h2>{{ compania.name if compania else perfil_pos }}</h2>
</div>
```

### Ejemplo 3: CSS Personalizado con Colores

```css
/* estilos_css */
.header {
    background: #000;
    color: #fff;
    padding: 15px;
    margin: -5mm -5mm 10px -5mm;
}

.total-final {
    background: #f0f0f0;
    padding: 10px;
    font-size: 16px;
    font-weight: bold;
}

.items-table th {
    background: #333;
    color: #fff;
    padding: 5px;
}
```

## 🔧 Variables Jinja2 Disponibles

### Funciones de Frappe

- `{{ frappe.format_value(valor, {'fieldtype': 'Currency'}) }}` - Formatear moneda
- `{{ frappe.format_date(fecha, 'dd/MM/yyyy') }}` - Formatear fecha
- `{{ frappe.session.user }}` - Usuario actual

### Bucles

```html
{% for item in doc.tabla_de_productos %}
    <tr>
        <td>{{ item.producto }}</td>
        <td>{{ item.cantidad }}</td>
    </tr>
{% endfor %}
```

### Condicionales

```html
{% if doc.cambio and doc.cambio > 0 %}
    <p>Cambio: {{ frappe.format_value(doc.cambio, {'fieldtype': 'Currency'}) }}</p>
{% endif %}
```

## 🎯 Casos de Uso

### Ticket para Restaurante
- Más grande (Carta)
- Fuente Arial
- Detalles de mesa y mesero
- Categorías de productos

### Ticket para Retail
- 80mm estándar
- Logo de la tienda
- Programa de puntos
- Código QR para factura

### Ticket de Farmacia
- 58mm compacto
- Información de medicamentos
- Advertencias de salud
- Número de receta

## 🔒 Permisos

Por defecto, pueden gestionar formatos:
- **System Manager**: Acceso completo
- **POS Manager**: Crear, editar, eliminar formatos

## 📊 Ventajas

✅ **Flexibilidad Total**: HTML y CSS personalizables
✅ **Multi-formato**: Diferentes tickets para diferentes negocios
✅ **Vista Previa**: Prueba antes de usar
✅ **Sin Código**: Plantillas predeterminadas funcionales
✅ **Escalable**: Agrega tantos formatos como necesites

## 🆘 Solución de Problemas

### El formato no se aplica
- Verifica que el Perfil POS tenga el formato asignado
- Si no, marca un formato como "Predeterminado"

### Error al renderizar
- Revisa la sintaxis de Jinja2 en las plantillas
- Asegúrate de cerrar todos los tags HTML
- Verifica nombres de variables

### Vista previa en blanco
- Debe haber al menos una Nota de Venta creada
- Verifica que las plantillas HTML no estén vacías

## 🔄 Actualización del Sistema Antiguo

Si tenías el sistema anterior:
1. Crea un formato nuevo con las plantillas del print format antiguo
2. Marca como predeterminado
3. Asigna a tus perfiles POS
4. El sistema usará automáticamente los formatos personalizados
