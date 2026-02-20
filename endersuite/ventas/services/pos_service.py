import frappe
from frappe import _
from frappe.utils import now_datetime
import json
from endersuite.ventas.services.stock_service import check_availability
from endersuite.ventas.services.payment_service import validar_metodo_pago_existe, obtener_metodo_predeterminado

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def calcular_efectivo_disponible(sesion):
    """
    Calcula el efectivo disponible en caja considerando:
    - Monto de apertura
    - Ventas en efectivo
    - Cambios dados
    
    Args:
        sesion: Documento de Sesion POS
    
    Returns:
        float: Efectivo disponible en caja
    """
    efectivo_disponible = sesion.monto_apertura
    
    # Obtener todas las ventas de la sesión
    ventas = frappe.get_all(
        "Nota de Venta",
        filters={"sesion_pos": sesion.name, "docstatus": 1},
        fields=["name"]
    )
    
    for venta in ventas:
        # Sumar pagos en efectivo
        pagos_efectivo = frappe.get_all(
            "Metodos de Pago Nota",
            filters={"parent": venta.name, "metodo": "Efectivo"},
            fields=["monto"]
        )
        
        for pago in pagos_efectivo:
            efectivo_disponible += pago.monto
        
        # Restar cambio dado
        cambio = frappe.db.get_value("Nota de Venta", venta.name, "cambio") or 0
        efectivo_disponible -= cambio
    
    return efectivo_disponible

@frappe.whitelist()
def get_efectivo_disponible(sesion_name):
    """
    Obtiene el efectivo disponible en caja para una sesión.
    
    Args:
        sesion_name: Nombre de la sesión POS
    
    Returns:
        dict: {efectivo_disponible: float}
    """
    sesion = frappe.get_doc("Sesion POS", sesion_name)
    efectivo = calcular_efectivo_disponible(sesion)
    
    return {
        "efectivo_disponible": efectivo
    }

# ============================================================================
# GESTIÓN DE SESIONES POS
# ============================================================================

@frappe.whitelist()
def open_pos_session(perfil_pos, monto_apertura):
    """
    Abre una nueva sesión de POS.
    
    Args:
        perfil_pos (str): Nombre del Perfil POS
        monto_apertura (float): Monto inicial en caja
    
    Returns:
        dict: Datos de la sesión creada
    """
    usuario = frappe.session.user
    
    # Validar que no haya otra sesión abierta para este usuario
    sesiones_abiertas = frappe.db.get_list(
        "Sesion POS",
        filters={
            "usuario": usuario,
            "estado": "Abierta"
        },
        fields=["name"],
        limit=1
    )
    
    if sesiones_abiertas:
        frappe.throw(_("Ya tiene una sesión POS abierta: {0}. Debe cerrarla antes de abrir una nueva.").format(sesiones_abiertas[0].name))
    
    # Crear nueva sesión
    sesion = frappe.new_doc("Sesion POS")
    sesion.perfil_pos = perfil_pos
    sesion.usuario = usuario
    sesion.fecha_hora_apertura = now_datetime()
    sesion.monto_apertura = float(monto_apertura)
    sesion.estado = "Abierta"
    sesion.insert(ignore_permissions=True)
    frappe.db.commit()
    
    # Obtener almacén y lista de precios del perfil
    perfil = frappe.db.get_value(
        "Perfil de POS",
        perfil_pos,
        ["almacen", "lista_de_precios"],
        as_dict=True
    )
    
    return {
        "name": sesion.name,
        "perfil_pos": sesion.perfil_pos,
        "punto_de_venta": sesion.punto_de_venta,
        "fecha_hora_apertura": sesion.fecha_hora_apertura,
        "monto_apertura": sesion.monto_apertura,
        "almacen": perfil.get("almacen") if perfil else None,
        "lista_de_precios": perfil.get("lista_de_precios") if perfil else None
    }


@frappe.whitelist()
def get_ultima_venta_info(sesion_pos):
    """
    Obtiene información de la última venta realizada en una sesión.

    Args:
        sesion_pos (str): Nombre de la sesión POS

    Returns:
        dict: Información de la última venta o None
    """
    ultima_venta = frappe.get_all(
        "Nota de Venta",
        filters={"sesion_pos": sesion_pos, "docstatus": 1},
        fields=["name", "fecha_y_hora_de_venta", "total_final", "cliente"],
        order_by="fecha_y_hora_de_venta desc",
        limit=1
    )

    if ultima_venta:
        return ultima_venta[0]

    return None


@frappe.whitelist()
def get_active_session(usuario=None):
    """
    Obtiene la sesión activa del usuario actual o especificado.
    
    Args:
        usuario (str, optional): Usuario a consultar
    
    Returns:
        dict: Datos de la sesión activa o None
    """
    if not usuario:
        usuario = frappe.session.user
    
    sesion = frappe.db.get_value(
        "Sesion POS",
        {
            "usuario": usuario,
            "estado": "Abierta"
        },
        ["name", "perfil_pos", "punto_de_venta", "fecha_hora_apertura", "monto_apertura"],
        as_dict=True
    )
    
    if sesion:
        # Obtener almacén y lista de precios del perfil
        perfil = frappe.db.get_value(
            "Perfil de POS",
            sesion.perfil_pos,
            ["almacen", "lista_de_precios"],
            as_dict=True
        )
        
        if perfil:
            sesion["almacen"] = perfil.get("almacen")
            sesion["lista_de_precios"] = perfil.get("lista_de_precios")
        else:
            frappe.log_error(
                f"Perfil de POS '{sesion.perfil_pos}' no encontrado para sesión {sesion.name}",
                "POS Session - Missing Profile"
            )
        # Cargar ventas de la sesión directamente de Notas de Venta (solo enviadas, no canceladas)
        ventas = frappe.get_all(
            "Nota de Venta",
            filters={"sesion_pos": sesion.name, "docstatus": 1},  # docstatus 1 = enviada, 2 = cancelada
            fields=["name as nota_de_venta", "total_final as total", "total_pagado", "cambio", "fecha_y_hora_de_venta", "cliente"],
            order_by="fecha_y_hora_de_venta desc"
        )

        # Enriquecer con método de pago principal
        for v in ventas:
            metodo = frappe.db.get_value("Metodos de Pago Nota", {"parent": v.nota_de_venta}, "metodo")
            v["metodo_pago"] = metodo or "Efectivo"  # Defaultear a Efectivo si no hay método

        sesion["ventas"] = ventas

        # Agregar información de la última venta
        if ventas:
            ultima = ventas[0]  # Ya viene ordenada por fecha descendente
            sesion["ultima_venta"] = {
                "nota": ultima["nota_de_venta"],
                "fecha_hora": ultima.get("fecha_y_hora_de_venta"),
                "total": ultima["total"],
                "cliente": ultima.get("cliente")
            }

    return sesion


@frappe.whitelist()
def get_metodos_pago_perfil(perfil_pos):
    """
    Obtiene los métodos de pago configurados en el perfil POS.
    
    Args:
        perfil_pos (str): Nombre del perfil POS
    
    Returns:
        list: Lista de métodos de pago con campo predeterminado
    """
    perfil = frappe.get_doc("Perfil de POS", perfil_pos)
    
    metodos = []
    for metodo in perfil.metodos_de_pago:
        metodos.append({
            "metodo": metodo.metodo,
            "predeterminado": metodo.get("predeterminado", 0)
        })
    
    return metodos


@frappe.whitelist()
def get_session_summary(sesion_pos):
    """
    Obtiene el resumen de una sesión POS para el cierre.

    Args:
        sesion_pos (str): Nombre de la sesión

    Returns:
        dict: Resumen con ventas, totales y monto esperado
    """
    sesion = frappe.get_doc("Sesion POS", sesion_pos)

    # Obtener todas las notas de venta de la sesión (solo enviadas)
    ventas = frappe.get_all(
        "Nota de Venta",
        filters={"sesion_pos": sesion_pos, "docstatus": 1},
        fields=["name", "fecha_y_hora_de_venta as fecha", "total_final", "cliente"],
        order_by="fecha_y_hora_de_venta desc"
    )

    # Calcular totales
    total_ventas = sum([v.total_final for v in ventas])
    num_ventas = len(ventas)

    # Calcular monto esperado en efectivo
    # Monto apertura + ventas en efectivo - cambios dados
    monto_efectivo = sesion.monto_apertura

    for venta in ventas:
        # Obtener métodos de pago de cada venta
        metodos = frappe.get_all(
            "Metodos de Pago Nota",
            filters={"parent": venta.name},
            fields=["metodo", "monto"]
        )

        for metodo in metodos:
            if metodo.metodo == "Efectivo":
                monto_efectivo += metodo.monto

        # Restar el cambio dado (solo se da en efectivo)
        cambio = frappe.db.get_value("Nota de Venta", venta.name, "cambio") or 0
        monto_efectivo -= cambio

    return {
        "total_ventas": total_ventas,
        "num_ventas": num_ventas,
        "monto_esperado": monto_efectivo,
        "ventas": ventas
    }


@frappe.whitelist()
def close_pos_session(sesion_pos, monto_real, observaciones=None):
    """
    Cierra una sesión de POS con arqueo de caja.

    Args:
        sesion_pos (str): Nombre de la sesión
        monto_real (float): Efectivo contado físicamente
        observaciones (str, optional): Observaciones del cierre

    Returns:
        dict: Resumen del cierre
    """
    sesion = frappe.get_doc("Sesion POS", sesion_pos)

    # Validar que sea del usuario actual
    if sesion.usuario != frappe.session.user:
        frappe.throw(_("No tiene permisos para cerrar esta sesión"))

    if sesion.estado == "Cerrada":
        frappe.throw(_("Esta sesión ya está cerrada"))

    # Limpiar ventas que no existen o están canceladas
    ventas_validas = []
    if hasattr(sesion, 'ventas') and sesion.ventas:
        for venta in sesion.ventas:
            if venta.nota_de_venta and frappe.db.exists("Nota de Venta", venta.nota_de_venta):
                docstatus = frappe.db.get_value("Nota de Venta", venta.nota_de_venta, "docstatus")
                if docstatus == 1:  # Solo ventas enviadas
                    ventas_validas.append(venta)

    # Actualizar la tabla con solo ventas válidas
    sesion.ventas = []
    for venta in ventas_validas:
        sesion.append('ventas', {
            'nota_de_venta': venta.nota_de_venta,
            'total': venta.total,
            'metodo_pago': venta.metodo_pago
        })

    # Calcular totales por método de pago
    totales_metodos = {
        'Efectivo': 0,
        'Tarjeta': 0,
        'Transferencia': 0,
        'Cheque': 0
    }
    
    # Obtener todos los métodos de pago de las ventas válidas
    for venta in ventas_validas:
        metodos = frappe.get_all(
            "Metodos de Pago Nota",
            filters={"parent": venta.nota_de_venta},
            fields=["metodo", "monto"]
        )
        
        for metodo in metodos:
            if metodo.metodo in totales_metodos:
                totales_metodos[metodo.metodo] += metodo.monto

    # Actualizar datos de cierre
    sesion.fecha_hora_cierre = now_datetime()
    sesion.estado = "Cerrada"
    
    # Guardar totales del sistema
    sesion.total_efectivo_sistema = totales_metodos['Efectivo']
    sesion.total_tarjeta_sistema = totales_metodos['Tarjeta']
    sesion.total_transferencia_sistema = totales_metodos['Transferencia']
    sesion.total_cheque_sistema = totales_metodos['Cheque']
    sesion.total_general_sistema = sum(totales_metodos.values())

    # Usar el campo correcto según lo que tenga el DocType
    monto_real_float = float(monto_real)
    if hasattr(sesion, 'efectivo_contado'):
        sesion.efectivo_contado = monto_real_float
    if hasattr(sesion, 'monto_cierre'):
        sesion.monto_cierre = monto_real_float
    
    # Calcular diferencia (efectivo contado - efectivo sistema)
    sesion.diferencia = monto_real_float - totales_metodos['Efectivo']

    if observaciones:
        if hasattr(sesion, 'observaciones'):
            sesion.observaciones = observaciones
        if hasattr(sesion, 'observaciones_cierre'):
            sesion.observaciones_cierre = observaciones

    # Guardar y enviar
    sesion.save(ignore_permissions=True)
    sesion.submit()
    frappe.db.commit()

    # Calcular diferencia para retornar
    resumen = get_session_summary(sesion_pos)
    diferencia = monto_real_float - resumen.get('monto_esperado', 0)

    return {
        "name": sesion.name,
        "total_ventas": len(sesion.ventas),
        "monto_esperado": resumen.get('monto_esperado', 0),
        "monto_real": monto_real_float,
        "diferencia": diferencia,
        "total_general": resumen.get('total_ventas', 0)
    }


# ============================================================================
# BÚSQUEDA Y LISTADO DE PRODUCTOS
# ============================================================================

@frappe.whitelist()
def get_productos_pos(almacen, lista_de_precios, limit=100):
    """
    Obtiene todos los productos disponibles para el POS con precio y stock.

    Args:
        almacen (str): Almacén para consultar stock
        lista_de_precios (str): Lista de precios a usar
        limit (int): Límite de productos

    Returns:
        list: Productos con precio, stock e impuesto
    """
    if not lista_de_precios:
        frappe.throw(_('Se requiere Lista de Precios'))

    # Obtener productos activos
    productos = frappe.get_all(
        'Producto',
        fields=['name as name', 'nombre_del_producto as nombre', 'sku', 'imagen',
                'mantener_stock', 'cantidad_disponible', 'tipo_de_impuesto', 'categoria'],
        limit_page_length=limit,
        order_by='nombre_del_producto asc'
    )

    if not productos:
        return []

    nombres = [p['name'] for p in productos]

    # Obtener precios de la lista especificada
    precios = frappe.get_all(
        'Precios productos',
        filters={
            'parenttype': 'Producto',
            'lista_de_precios': lista_de_precios,
            'parent': ['in', nombres],
        },
        fields=['parent', 'precio_unitario'],
        limit_page_length=len(nombres)
    )

    precio_map = {pp['parent']: pp.get('precio_unitario', 0) for pp in precios}

    # Obtener porcentajes de impuesto
    impuestos_map = {}
    impuestos_unicos = list(set([p.get('tipo_de_impuesto') for p in productos if p.get('tipo_de_impuesto')]))

    if impuestos_unicos:
        impuestos_data = frappe.get_all(
            'Impuestos',
            filters={'name': ['in', impuestos_unicos]},
            fields=['name', 'porciento_impuesto', 'incluido_en_el_precio']
        )
        impuestos_map = {imp['name']: {
            'porcentaje': imp.get('porciento_impuesto', 0),
            'incluido': imp.get('incluido_en_el_precio', 0)
        } for imp in impuestos_data}

    # Construir resultado
    resultado = []
    for p in productos:
        impuesto_info = impuestos_map.get(p.get('tipo_de_impuesto'), {'porcentaje': 0, 'incluido': 0})
        resultado.append({
            'name': p['name'],
            'nombre': p.get('nombre', p['name']),
            'sku': p.get('sku', ''),
            'imagen': p.get('imagen'),
            'precio': precio_map.get(p['name'], 0),
            'cantidad_disponible': p.get('cantidad_disponible', 0) if p.get('mantener_stock') else 999999,
            'mantener_stock': p.get('mantener_stock', 0),
            'tipo_de_impuesto': p.get('tipo_de_impuesto'),
            'porcentaje_impuesto': impuesto_info['porcentaje'],
            'incluido_en_el_precio': impuesto_info['incluido'],
            'codigo_barras': p.get('codigo_barras', '')
        })

    return resultado


@frappe.whitelist()
def get_stock_actual(productos, almacen):
    """
    Obtiene el stock actual de una lista de productos.

    Args:
        productos (list): Lista de nombres de productos
        almacen (str): Almacén a consultar

    Returns:
        dict: Mapa de producto -> cantidad disponible
    """
    if isinstance(productos, str):
        productos = json.loads(productos)

    if not productos:
        return {}

    stock_map = {}
    for producto in productos:
        cantidad = frappe.db.get_value('Producto', producto, 'cantidad_disponible') or 0
        stock_map[producto] = cantidad

    return stock_map


@frappe.whitelist()
def get_product_price(producto, lista_de_precios):
    """
    Obtiene el precio de un producto en una lista de precios específica.

    Args:
        producto (str): Nombre del producto
        lista_de_precios (str): Lista de precios

    Returns:
        dict: Precio y datos del producto
    """
    precio = frappe.db.get_value(
        'Precios productos',
        {
            'parent': producto,
            'parenttype': 'Producto',
            'lista_de_precios': lista_de_precios
        },
        'precio_unitario'
    )

    return {
        'precio': precio or 0,
        'producto': producto
    }


@frappe.whitelist()
def search_products(query, lista_de_precios, almacen=None, limit=20):
    """
    Busca productos por nombre o SKU con precio y stock.
    
    Args:
        query (str): Término de búsqueda
        lista_de_precios (str): Lista de precios a usar
        almacen (str, optional): Almacén para consultar stock
        limit (int): Límite de resultados
    
    Returns:
        list: Productos encontrados con precio y stock
    """
    if not query or len(query) < 2:
        return []
    
    # Buscar por nombre o SKU
    productos = frappe.db.sql("""
        SELECT 
            name, sku, imagen, mantener_stock, cantidad_disponible,
            requiere_lote, requiere_serie, tipo_de_impuesto
        FROM `tabProducto`
        WHERE (nombre_del_producto LIKE %(query)s OR sku LIKE %(query)s)
        LIMIT %(limit)s
    """, {
        "query": f"%{query}%",
        "limit": limit
    }, as_dict=True)
    
    if not productos:
        return []
    
    nombres = [p['name'] for p in productos]
    
    # Obtener precios
    precios = frappe.get_all(
        'Precios productos',
        filters={
            'parenttype': 'Producto',
            'lista_de_precios': lista_de_precios,
            'parent': ['in', nombres],
        },
        fields=['parent', 'precio_unitario'],
        limit_page_length=len(nombres)
    )
    
    precio_map = {pp['parent']: pp.get('precio_unitario', 0) for pp in precios}
    
    # Construir resultado
    resultado = []
    for p in productos:
        resultado.append({
            'name': p['name'],
            'sku': p.get('sku'),
            'imagen': p.get('imagen'),
            'precio': precio_map.get(p['name'], 0),
            'cantidad_disponible': p.get('cantidad_disponible', 0) if p.get('mantener_stock') else 999999,
            'mantener_stock': p.get('mantener_stock', 0),
            'requiere_lote': p.get('requiere_lote', 0),
            'requiere_serie': p.get('requiere_serie', 0),
            'tipo_de_impuesto': p.get('tipo_de_impuesto')
        })
    
    return resultado


@frappe.whitelist()
def get_products_with_price(lista_de_precios: str, almacen=None, limit: int = 50):
    """
    Devuelve productos con su precio, stock e imagen según Lista de Precios.
    """
    if not lista_de_precios:
        frappe.throw(_('Se requiere Lista de Precios'))

    productos = frappe.get_all(
        'Producto',
        fields=['name', 'sku', 'imagen', 'mantener_stock', 'cantidad_disponible', 
                'requiere_lote', 'requiere_serie', 'tipo_de_impuesto'],
        limit_page_length=limit,
    )

    if not productos:
        return []

    nombres = [p['name'] for p in productos]

    precios = frappe.get_all(
        'Precios productos',
        filters={
            'parenttype': 'Producto',
            'lista_de_precios': lista_de_precios,
            'parent': ['in', nombres],
        },
        fields=['parent', 'precio_unitario'],
        limit_page_length=limit * 3,
    )

    precio_map = {pp['parent']: pp.get('precio_unitario') for pp in precios}

    resultado = []
    for p in productos:
        resultado.append({
            'name': p['name'],
            'sku': p.get('sku'),
            'imagen': p.get('imagen'),
            'precio': precio_map.get(p['name'], 0),
            'cantidad_disponible': p.get('cantidad_disponible', 0) if p.get('mantener_stock') else 999999,
            'mantener_stock': p.get('mantener_stock', 0),
            'requiere_lote': p.get('requiere_lote', 0),
            'requiere_serie': p.get('requiere_serie', 0),
            'tipo_de_impuesto': p.get('tipo_de_impuesto')
        })

    return resultado


@frappe.whitelist()
def get_pos_profile(profile_name: str):
    """
    Devuelve configuración del Perfil de POS.
    """
    if not profile_name:
        frappe.throw(_('Se requiere nombre de Perfil POS'))

    profile = frappe.get_value(
        'Perfil de POS',
        profile_name,
        ['lista_de_precios', 'almacen', 'punto_de_venta'],
        as_dict=True,
    )

    if not profile:
        frappe.throw(_('Perfil POS no encontrado'))

    return profile


@frappe.whitelist()
def get_pos_payment_methods(profile_name):
    """
    Obtiene los métodos de pago configurados para un perfil POS.
    Valida que los métodos existan antes de retornarlos.
    """
    if not profile_name:
        return []

    methods = frappe.get_all(
        'Metodos de Pago POS',
        filters={'parent': profile_name, 'parenttype': 'Perfil de POS', 'habilitado': 1},
        fields=['metodo', 'predeterminado']
    )

    # Validar que cada método exista
    metodos_validos = []
    for metodo in methods:
        if validar_metodo_pago_existe(metodo.get('metodo')):
            metodos_validos.append(metodo)
        else:
            frappe.log_error(
                f"Método de pago '{metodo.get('metodo')}' configurado en perfil '{profile_name}' no existe",
                "Validación Métodos de Pago POS"
            )

    if not metodos_validos:
        frappe.throw(_("No hay métodos de pago válidos configurados en el perfil POS"))

    return metodos_validos


# ============================================================================
# CREACIÓN DE NOTAS DE VENTA
# ============================================================================

@frappe.whitelist()
def create_sale(sesion_pos, productos, metodos_pago, total, cliente=None, imprimir_ticket=False):
    """
    Crea una venta desde el POS (wrapper simplificado).

    Args:
        sesion_pos (str): Sesión POS activa
        productos (list): Lista de productos del carrito
        metodos_pago (list): Lista de métodos de pago
        total (float): Total de la venta
        cliente (str, optional): Cliente para la venta
        imprimir_ticket (bool): Si se debe marcar como impreso o no

    Returns:
        dict: Datos de la nota de venta creada con productos y métodos de pago
    """
    # Parsear JSON si viene como string
    if isinstance(productos, str):
        productos = json.loads(productos)
    if isinstance(metodos_pago, str):
        metodos_pago = json.loads(metodos_pago)

    # Obtener sesión y perfil
    sesion = frappe.get_doc("Sesion POS", sesion_pos)
    perfil_pos = sesion.perfil_pos

    # Obtener perfil para almacén y lista de precios
    profile = frappe.get_doc("Perfil de POS", perfil_pos)
    almacen = profile.almacen
    lista_de_precios = profile.lista_de_precios

    # Crear nota de venta
    nota = frappe.new_doc("Nota de Venta")
    nota.sesion_pos = sesion_pos
    nota.perfil_pos = perfil_pos
    nota.almacen = almacen
    nota.lista_de_precios = lista_de_precios
    nota.fecha_y_hora_de_venta = now_datetime()

    # Usar cliente proporcionado o cliente genérico
    if cliente:
        nota.cliente = cliente
    else:
        # Cliente genérico si no hay
        if not frappe.db.exists("Cliente", "Cliente Genérico"):
            cliente_gen = frappe.new_doc("Cliente")
            cliente_gen.nombre_del_cliente = "Cliente Genérico"
            cliente_gen.flags.ignore_mandatory = True
            cliente_gen.insert(ignore_permissions=True)

        nota.cliente = "Cliente Genérico"

    # Agregar productos
    for item in productos:
        nota.append('tabla_de_productos', {
            'producto': item.get('producto'),
            'cantidad': item.get('cantidad'),
            'precio_unitario': item.get('precio_unitario'),
            'descuento_porcentaje': item.get('descuento_porcentaje', 0),
            'impuesto': item.get('impuesto')
        })

    # Agregar métodos de pago
    for metodo in metodos_pago:
        nota.append('metodos_pago_nota', {
            'metodo': metodo.get('metodo_de_pago'),
            'monto': metodo.get('monto')
        })

    # Establecer estado de impresión según preferencia
    if imprimir_ticket:
        nota.estado_impresion = "Pendiente"
    else:
        nota.estado_impresion = "No Requiere"

    # Guardar y enviar
    nota.insert(ignore_permissions=True)
    nota.submit()
    frappe.db.commit()

    # Recargar para obtener todos los datos calculados
    nota.reload()

    # Retornar datos completos para el ticket
    return {
        'name': nota.name,
        'subtotal': nota.subtotal,
        'total_impuestos': nota.total_impuestos,
        'total_final': nota.total_final,
        'productos': [{
            'nombre': item.producto,
            'cantidad': item.cantidad,
            'precio_unitario': item.precio_unitario
        } for item in nota.tabla_de_productos],
        'metodos_pago': [{
            'metodo_de_pago': mp.metodo,
            'monto': mp.monto
        } for mp in nota.metodos_pago_nota]
    }


# ============================================================================
# IMPRESIÓN DE TICKET
# ============================================================================

@frappe.whitelist()
def generate_ticket_html(nota_venta_name, formato_name=None):
    """
    Genera el HTML del ticket para impresión usando formato personalizado.
    
    Args:
        nota_venta_name (str): Nombre de la Nota de Venta
        formato_name (str): Nombre del formato de ticket (opcional)
    
    Returns:
        str: HTML del ticket
    """
    try:
        # Si no se especifica formato, intentar obtenerlo del perfil POS
        if not formato_name:
            nota = frappe.get_doc("Nota de Venta", nota_venta_name)
            if nota.perfil_pos:
                formato_name = frappe.get_value("Perfil de POS", nota.perfil_pos, "formato_ticket")
        
        # Si hay formato personalizado, usarlo
        if formato_name and frappe.db.exists("Formato de Ticket", formato_name):
            from endersuite.ventas.doctype.formato_de_ticket.formato_de_ticket import generar_ticket_html
            return generar_ticket_html(nota_venta_name, formato_name)
        
        # Buscar formato predeterminado
        formato_pred = frappe.get_value("Formato de Ticket", {"predeterminado": 1}, "name")
        if formato_pred:
            from endersuite.ventas.doctype.formato_de_ticket.formato_de_ticket import generar_ticket_html
            return generar_ticket_html(nota_venta_name, formato_pred)
        
        # Fallback al formato de impresión estándar
        html = frappe.get_print(
            doctype="Nota de Venta",
            name=nota_venta_name,
            print_format="Ticket Nota de Venta",
            no_letterhead=1
        )
        return html
    except Exception as e:
        frappe.log_error(f"Error generando ticket: {str(e)}")
        frappe.throw(_("Error al generar el ticket: {0}").format(str(e)))
