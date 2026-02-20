<template>
  <div class="pos-container">
    <!-- PANTALLA DE APERTURA -->
    <div v-if="pantalla === 'apertura'" class="pantalla-apertura">
      <div class="apertura-card">
        <h2>🏪 Apertura de Caja</h2>
        <div class="form-group">
          <label>Perfil POS</label>
          <select v-model="perfilPOSSeleccionado" class="form-control">
            <option value="">Seleccionar...</option>
            <option v-for="perfil in perfilesDisponibles" :key="perfil.name" :value="perfil.name">
              {{ perfil.nombre_perfil }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>Monto Inicial en Caja</label>
          <input v-model.number="montoApertura" type="number" class="form-control" placeholder="0.00" />
        </div>
        <button @click="abrirSesion" class="btn btn-primary btn-lg" :disabled="!perfilPOSSeleccionado || !montoApertura">
          Abrir Caja
        </button>
      </div>
    </div>

    <!-- PANTALLA PRINCIPAL (POS) -->
    <div v-else-if="pantalla === 'principal'" class="pantalla-principal">
      <!-- Header -->
      <div class="pos-header">
        <div class="header-info">
          <h3>🏪 {{ sesionActiva?.perfil_pos }}</h3>
          <small>Sesión: {{ sesionActiva?.name }} | Apertura: {{ formatDateTime(sesionActiva?.fecha_hora_apertura) }}</small>
        </div>
        <div class="header-search">
          <input 
            v-model="busqueda" 
            @input="buscarProductos" 
            type="text" 
            class="form-control" 
            placeholder="🔍 Buscar producto por nombre o SKU..." 
          />
        </div>
      </div>

      <div class="pos-body">
        <!-- PRODUCTOS (Izquierda) -->
        <div class="productos-panel">
          <div class="productos-grid">
            <div 
              v-for="prod in productosMostrados" 
              :key="prod.name" 
              @click="agregarAlCarrito(prod)"
              class="producto-card"
              :class="{ 'sin-stock': prod.mantener_stock && prod.cantidad_disponible <= 0 }"
            >
              <div class="producto-imagen">
                <img v-if="prod.imagen" :src="prod.imagen" :alt="prod.name" />
                <div v-else class="placeholder-imagen">📦</div>
              </div>
              <div class="producto-info">
                <div class="producto-nombre">{{ prod.name }}</div>
                <div class="producto-sku">{{ prod.sku }}</div>
                <div class="producto-precio">${{ formatCurrency(prod.precio) }}</div>
                <div v-if="prod.mantener_stock" class="producto-stock" :class="stockClass(prod.cantidad_disponible)">
                  Stock: {{ prod.cantidad_disponible }}
                </div>
              </div>
            </div>
          </div>
          <div v-if="cargando" class="text-center">Cargando productos...</div>
          <div v-if="!cargando && productosMostrados.length === 0" class="text-center text-muted">
            No se encontraron productos
          </div>
        </div>

        <!-- CARRITO Y PAGO (Derecha) -->
        <div class="carrito-panel">
          <!-- Cliente -->
          <div class="cliente-section">
            <label>Cliente (opcional)</label>
            <input v-model="cliente" type="text" class="form-control" placeholder="Nombre del cliente" />
          </div>

          <!-- Items del carrito -->
          <div class="carrito-items">
            <div v-for="(item, idx) in carrito" :key="idx" class="carrito-item">
              <div class="item-info">
                <strong>{{ item.name }}</strong>
                <small>{{ item.sku }}</small>
              </div>
              <div class="item-cantidad">
                <button @click="decrementarCantidad(idx)" class="btn btn-sm">-</button>
                <input v-model.number="item.cantidad" type="number" min="1" class="cantidad-input" />
                <button @click="incrementarCantidad(idx)" class="btn btn-sm">+</button>
              </div>
              <div class="item-precio">${{ formatCurrency(item.precio * item.cantidad) }}</div>
              <button @click="eliminarDelCarrito(idx)" class="btn btn-sm btn-danger">🗑️</button>
            </div>
            <div v-if="carrito.length === 0" class="text-center text-muted">
              Carrito vacío
            </div>
          </div>

          <!-- Totales -->
          <div class="totales-section">
            <div class="total-row">
              <span>Subtotal:</span>
              <span>${{ formatCurrency(subtotal) }}</span>
            </div>
            <div class="total-row">
              <span>Impuestos:</span>
              <span>${{ formatCurrency(totalImpuestos) }}</span>
            </div>
            <div class="total-row total-final">
              <strong>Total:</strong>
              <strong>${{ formatCurrency(totalFinal) }}</strong>
            </div>
          </div>

          <!-- Métodos de Pago -->
          <div class="pago-section">
            <label>Métodos de Pago</label>
            <div v-for="(metodo, idx) in metodosPago" :key="idx" class="metodo-pago-row">
              <select v-model="metodo.metodo" class="form-control form-control-sm">
                <option v-for="m in metodosDisponibles" :key="m" :value="m">{{ m }}</option>
              </select>
              <input v-model.number="metodo.monto" type="number" class="form-control form-control-sm" placeholder="Monto" />
              <button @click="eliminarMetodoPago(idx)" class="btn btn-sm btn-danger">×</button>
            </div>
            <button @click="agregarMetodoPago" class="btn btn-sm btn-secondary">+ Agregar método</button>
            
            <div class="pago-info">
              <div>Total Pagado: ${{ formatCurrency(totalPagado) }}</div>
              <div v-if="cambioCalculado > 0" class="cambio-info">
                Cambio: ${{ formatCurrency(cambioCalculado) }}
              </div>
              <div v-if="totalPagado < totalFinal" class="text-danger">
                Falta: ${{ formatCurrency(totalFinal - totalPagado) }}
              </div>
            </div>
          </div>

          <!-- Botones de acción -->
          <div class="acciones-section">
            <button @click="limpiarCarrito" class="btn btn-secondary">🗑️ Limpiar</button>
            <button @click="procesarVenta" class="btn btn-success btn-lg" :disabled="!puedeFinalizarVenta">
              ✓ Finalizar Venta
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- PANTALLA DE CIERRE -->
    <div v-else-if="pantalla === 'cierre'" class="pantalla-cierre">
      <div class="cierre-card">
        <h2>💰 Cierre de Caja</h2>
        <div class="resumen-sesion">
          <h4>Resumen de la Sesión</h4>
          <p><strong>Sesión:</strong> {{ sesionActiva?.name }}</p>
          <p><strong>Total de Ventas:</strong> {{ ventasSesion.length }}</p>
          <p><strong>Efectivo Sistema:</strong> ${{ formatCurrency(efectivoSistema) }}</p>
          <p><strong>Tarjeta Sistema:</strong> ${{ formatCurrency(tarjetaSistema) }}</p>
          <p><strong>Total Sistema:</strong> ${{ formatCurrency(totalSistema) }}</p>
        </div>
        
        <div class="form-group">
          <label>Efectivo Contado (Arqueo)</label>
          <input v-model.number="efectivoContado" type="number" class="form-control" placeholder="0.00" />
        </div>
        
        <div v-if="efectivoContado !== null" class="diferencia-info" :class="diferenciaCierreClass">
          Diferencia: ${{ formatCurrency(diferenciaCierre) }}
        </div>
        
        <div class="form-group">
          <label>Observaciones</label>
          <textarea v-model="observacionesCierre" class="form-control" rows="3"></textarea>
        </div>
        
        <div class="btn-group-cierre">
          <button @click="volverAPrincipal" class="btn btn-secondary">← Volver</button>
          <button @click="cerrarSesion" class="btn btn-primary btn-lg" :disabled="efectivoContado === null">
            Cerrar Sesión
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL POST-VENTA -->
    <div v-if="mostrarModalVenta" class="modal-overlay" @click="cerrarModalVenta">
      <div class="modal-content" @click.stop>
        <h3>✅ Venta Exitosa</h3>
        <div class="venta-resumen">
          <p><strong>Nota de Venta:</strong> {{ ultimaVenta.name }}</p>
          <p><strong>Total:</strong> ${{ formatCurrency(ultimaVenta.total_final) }}</p>
          <p v-if="ultimaVenta.cambio > 0"><strong>Cambio:</strong> ${{ formatCurrency(ultimaVenta.cambio) }}</p>
        </div>
        <div class="modal-actions">
          <button @click="imprimirTicket" class="btn btn-primary">🖨️ Imprimir Ticket</button>
          <button @click="nuevaVenta" class="btn btn-success">🛒 Nueva Venta</button>
          <button @click="irACierre" class="btn btn-warning">💰 Cerrar Caja</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

// Estados principales
const pantalla = ref('apertura'); // 'apertura' | 'principal' | 'cierre'
const sesionActiva = ref(null);
const perfilesDisponibles = ref([]);
const perfilPOSSeleccionado = ref('');
const montoApertura = ref(1000);

// Productos y búsqueda
const productos = ref([]);
const productosMostrados = ref([]);
const busqueda = ref('');
const cargando = ref(false);
const busquedaTimeout = ref(null);

// Carrito
const carrito = ref([]);
const cliente = ref('');

// Métodos de pago
const metodosPago = ref([{ metodo: 'Efectivo', monto: 0 }]);
const metodosDisponibles = ref(['Efectivo', 'Tarjeta', 'Transferencia', 'Cheque']);

// Modal y última venta
const mostrarModalVenta = ref(false);
const ultimaVenta = ref({});

// Cierre
const efectivoContado = ref(null);
const observacionesCierre = ref('');
const ventasSesion = ref([]);

// ============================================================================
// CICLO DE VIDA
// ============================================================================

onMounted(async () => {
  await verificarSesionActiva();
  if (!sesionActiva.value) {
    await cargarPerfiles();
  } else {
    pantalla.value = 'principal';
    await cargarProductosIniciales();
  }
});

// ============================================================================
// GESTIÓN DE SESIÓN
// ============================================================================

async function cargarPerfiles() {
  try {
    const res = await window.frappe.call({
      method: 'frappe.client.get_list',
      args: {
        doctype: 'Perfil de POS',
        filters: { habilitado: 1 },
        fields: ['name', 'nombre_perfil']
      }
    });
    perfilesDisponibles.value = res.message || [];
  } catch (error) {
    console.error('Error cargando perfiles:', error);
    window.frappe.show_alert({ message: 'Error al cargar perfiles', indicator: 'red' });
  }
}

async function verificarSesionActiva() {
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.get_active_session'
    });
    if (res.message) {
      sesionActiva.value = res.message;
    }
  } catch (error) {
    console.error('Error verificando sesión:', error);
  }
}

async function abrirSesion() {
  if (!perfilPOSSeleccionado.value || !montoApertura.value) {
    window.frappe.show_alert({ message: 'Complete todos los campos', indicator: 'red' });
    return;
  }
  
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.open_pos_session',
      args: {
        perfil_pos: perfilPOSSeleccionado.value,
        monto_apertura: montoApertura.value
      }
    });
    sesionActiva.value = res.message;
    pantalla.value = 'principal';
    await cargarProductosIniciales();
    window.frappe.show_alert({ message: 'Sesión abierta exitosamente', indicator: 'green' });
  } catch (error) {
    console.error('Error abriendo sesión:', error);
    window.frappe.show_alert({ message: 'Error al abrir sesión', indicator: 'red' });
  }
}

async function cerrarSesion() {
  if (efectivoContado.value === null) {
    window.frappe.show_alert({ message: 'Debe ingresar el efectivo contado', indicator: 'red' });
    return;
  }
  
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.close_pos_session',
      args: {
        sesion_pos: sesionActiva.value.name,
        efectivo_contado: efectivoContado.value,
        observaciones: observacionesCierre.value
      }
    });
    
    window.frappe.show_alert({ message: 'Sesión cerrada exitosamente', indicator: 'green' });
    
    // Resetear estado
    sesionActiva.value = null;
    efectivoContado.value = null;
    observacionesCierre.value = '';
    ventasSesion.value = [];
    carrito.value = [];
    pantalla.value = 'apertura';
    
    await cargarPerfiles();
  } catch (error) {
    console.error('Error cerrando sesión:', error);
    window.frappe.show_alert({ message: 'Error al cerrar sesión', indicator: 'red' });
  }
}

// ============================================================================
// PRODUCTOS
// ============================================================================

async function cargarProductosIniciales() {
  if (!sesionActiva.value) return;
  
  cargando.value = true;
  try {
    const perfil = await obtenerPerfil();
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.get_products_with_price',
      args: { 
        lista_de_precios: perfil.lista_de_precios,
        limit: 50 
      }
    });
    productos.value = res.message || [];
    productosMostrados.value = productos.value;
  } catch (error) {
    console.error('Error cargando productos:', error);
  } finally {
    cargando.value = false;
  }
}

function buscarProductos() {
  if (busquedaTimeout.value) {
    clearTimeout(busquedaTimeout.value);
  }
  
  busquedaTimeout.value = setTimeout(async () => {
    if (!busqueda.value || busqueda.value.length < 2) {
      productosMostrados.value = productos.value;
      return;
    }
    
    cargando.value = true;
    try {
      const perfil = await obtenerPerfil();
      const res = await window.frappe.call({
        method: 'endersuite.ventas.services.pos_service.search_products',
        args: {
          query: busqueda.value,
          lista_de_precios: perfil.lista_de_precios,
          limit: 20
        }
      });
      productosMostrados.value = res.message || [];
    } catch (error) {
      console.error('Error buscando productos:', error);
    } finally {
      cargando.value = false;
    }
  }, 300);
}

async function obtenerPerfil() {
  const res = await window.frappe.call({
    method: 'endersuite.ventas.services.pos_service.get_pos_profile',
    args: { profile_name: sesionActiva.value.perfil_pos }
  });
  return res.message;
}

// ============================================================================
// CARRITO
// ============================================================================

function agregarAlCarrito(prod) {
  if (prod.mantener_stock && prod.cantidad_disponible <= 0) {
    window.frappe.show_alert({ message: 'Producto sin stock', indicator: 'red' });
    return;
  }
  
  const item = carrito.value.find(i => i.name === prod.name);
  if (item) {
    if (prod.mantener_stock && item.cantidad >= prod.cantidad_disponible) {
      window.frappe.show_alert({ message: 'Stock insuficiente', indicator: 'orange' });
      return;
    }
    item.cantidad += 1;
  } else {
    carrito.value.push({
      name: prod.name,
      producto: prod.name,
      sku: prod.sku,
      cantidad: 1,
      precio_unitario: prod.precio,
      precio: prod.precio,
      tipo_de_impuesto: prod.tipo_de_impuesto,
      descuento_porcentaje: 0,
      mantener_stock: prod.mantener_stock,
      cantidad_disponible: prod.cantidad_disponible
    });
  }
}

function incrementarCantidad(idx) {
  const item = carrito.value[idx];
  if (item.mantener_stock && item.cantidad >= item.cantidad_disponible) {
    window.frappe.show_alert({ message: 'Stock insuficiente', indicator: 'orange' });
    return;
  }
  item.cantidad += 1;
}

function decrementarCantidad(idx) {
  if (carrito.value[idx].cantidad > 1) {
    carrito.value[idx].cantidad -= 1;
  }
}

function eliminarDelCarrito(idx) {
  carrito.value.splice(idx, 1);
}

function limpiarCarrito() {
  if (confirm('¿Limpiar todo el carrito?')) {
    carrito.value = [];
    metodosPago.value = [{ metodo: 'Efectivo', monto: 0 }];
  }
}

// ============================================================================
// MÉTODOS DE PAGO
// ============================================================================

function agregarMetodoPago() {
  metodosPago.value.push({ metodo: 'Efectivo', monto: 0 });
}

function eliminarMetodoPago(idx) {
  if (metodosPago.value.length > 1) {
    metodosPago.value.splice(idx, 1);
  }
}

// ============================================================================
// COMPUTADOS Y TOTALES
// ============================================================================

const subtotal = computed(() => {
  return carrito.value.reduce((sum, item) => {
    const subtotal_sin_impuesto = item.cantidad * item.precio_unitario;
    const descuento_monto = subtotal_sin_impuesto * (item.descuento_porcentaje || 0) / 100;
    return sum + (subtotal_sin_impuesto - descuento_monto);
  }, 0);
});

const totalImpuestos = computed(() => {
  // Estimación simplificada - el backend calculará exacto
  return subtotal.value * 0.16;
});

const totalFinal = computed(() => {
  return subtotal.value + totalImpuestos.value;
});

const totalPagado = computed(() => {
  return metodosPago.value.reduce((sum, m) => sum + (m.monto || 0), 0);
});

const cambioCalculado = computed(() => {
  const efectivo = metodosPago.value.find(m => m.metodo === 'Efectivo');
  if (efectivo && totalPagado.value > totalFinal.value) {
    return totalPagado.value - totalFinal.value;
  }
  return 0;
});

const puedeFinalizarVenta = computed(() => {
  return carrito.value.length > 0 && totalPagado.value >= totalFinal.value;
});

const efectivoSistema = computed(() => {
  return ventasSesion.value
    .filter(v => v.metodo_pago === 'Efectivo')
    .reduce((sum, v) => sum + v.total, 0);
});

const tarjetaSistema = computed(() => {
  return ventasSesion.value
    .filter(v => v.metodo_pago === 'Tarjeta')
    .reduce((sum, v) => sum + v.total, 0);
});

const totalSistema = computed(() => {
  return ventasSesion.value.reduce((sum, v) => sum + v.total, 0);
});

const diferenciaCierre = computed(() => {
  if (efectivoContado.value === null || !sesionActiva.value) return 0;
  return efectivoContado.value - (efectivoSistema.value + sesionActiva.value.monto_apertura);
});

const diferenciaCierreClass = computed(() => {
  const diff = diferenciaCierre.value;
  if (diff > 0) return 'diferencia-positiva';
  if (diff < 0) return 'diferencia-negativa';
  return 'diferencia-cero';
});

// ============================================================================
// PROCESAR VENTA
// ============================================================================

async function procesarVenta() {
  if (!puedeFinalizarVenta.value) {
    window.frappe.show_alert({ message: 'Complete el pago', indicator: 'red' });
    return;
  }
  
  // Preparar items
  const items = carrito.value.map(item => ({
    producto: item.producto,
    cantidad: item.cantidad,
    precio_unitario: item.precio_unitario,
    descuento_porcentaje: item.descuento_porcentaje || 0,
    detalle_lote_serie: []
  }));
  
  // Preparar métodos de pago
  const pagos = metodosPago.value.filter(m => m.monto > 0);
  
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.create_nota_de_venta',
      args: {
        sesion_pos: sesionActiva.value.name,
        perfil_pos: sesionActiva.value.perfil_pos,
        cliente: cliente.value || null,
        items: JSON.stringify(items),
        metodos_pago: JSON.stringify(pagos),
        descuento_global: 0
      }
    });
    
    ultimaVenta.value = res.message;
    mostrarModalVenta.value = true;
    
    // Agregar a ventas de sesión
    ventasSesion.value.push({
      nota_de_venta: res.message.name,
      total: res.message.total_final,
      metodo_pago: pagos[0]?.metodo || 'Efectivo'
    });
    
  } catch (error) {
    console.error('Error procesando venta:', error);
    window.frappe.show_alert({ message: 'Error al procesar venta', indicator: 'red' });
  }
}

// ============================================================================
// MODAL POST-VENTA
// ============================================================================

function cerrarModalVenta() {
  mostrarModalVenta.value = false;
}

function nuevaVenta() {
  carrito.value = [];
  cliente.value = '';
  metodosPago.value = [{ metodo: 'Efectivo', monto: 0 }];
  mostrarModalVenta.value = false;
  busqueda.value = '';
  productosMostrados.value = productos.value;
}

async function imprimirTicket() {
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.generate_ticket_html',
      args: {
        nota_venta_name: ultimaVenta.value.name
      }
    });
    
    // Abrir ventana de impresión
    const printWindow = window.open('', '_blank');
    printWindow.document.write(res.message);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
  } catch (error) {
    console.error('Error imprimiendo ticket:', error);
    window.frappe.show_alert({ message: 'Error al imprimir ticket', indicator: 'red' });
  }
}

function irACierre() {
  mostrarModalVenta.value = false;
  pantalla.value = 'cierre';
}

function volverAPrincipal() {
  pantalla.value = 'principal';
}

// ============================================================================
// UTILIDADES
// ============================================================================

function formatCurrency(value) {
  return (value || 0).toFixed(2);
}

function formatDateTime(dt) {
  if (!dt) return '';
  const date = new Date(dt);
  return date.toLocaleString('es-MX', { 
    day: '2-digit', 
    month: '2-digit', 
    year: 'numeric',
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

function stockClass(cantidad) {
  if (cantidad <= 0) return 'stock-vacio';
  if (cantidad <= 10) return 'stock-bajo';
  return 'stock-normal';
}
</script>

<style scoped>
.pos-container {
  height: 100vh;
  background: #f5f7fa;
}

/* PANTALLA APERTURA */
.pantalla-apertura {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.apertura-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  max-width: 400px;
  width: 100%;
}

.apertura-card h2 {
  text-align: center;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

/* PANTALLA PRINCIPAL */
.pantalla-principal {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pos-header {
  background: white;
  padding: 16px 24px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-info h3 {
  margin: 0 0 4px 0;
}

.header-info small {
  color: #666;
}

.header-search {
  margin-top: 12px;
}

.header-search input {
  width: 100%;
  max-width: 600px;
  font-size: 16px;
  padding: 10px;
}

.pos-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Panel de productos */
.productos-panel {
  flex: 2;
  padding: 20px;
  overflow-y: auto;
}

.productos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.producto-card {
  background: white;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.producto-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.producto-card.sin-stock {
  opacity: 0.5;
  cursor: not-allowed;
}

.producto-imagen {
  width: 100%;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 6px;
  margin-bottom: 8px;
}

.producto-imagen img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.placeholder-imagen {
  font-size: 48px;
}

.producto-nombre {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.producto-sku {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.producto-precio {
  font-size: 16px;
  font-weight: 700;
  color: #2196f3;
  margin-bottom: 4px;
}

.producto-stock {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}

.stock-normal {
  background: #e8f5e9;
  color: #2e7d32;
}

.stock-bajo {
  background: #fff3e0;
  color: #f57c00;
}

.stock-vacio {
  background: #ffebee;
  color: #c62828;
}

/* Panel de carrito */
.carrito-panel {
  flex: 1;
  min-width: 350px;
  max-width: 450px;
  background: white;
  padding: 20px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #ddd;
  overflow-y: auto;
}

.cliente-section {
  margin-bottom: 16px;
}

.carrito-items {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.carrito-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  margin-bottom: 8px;
}

.item-info {
  flex: 1;
}

.item-info strong {
  display: block;
  font-size: 14px;
}

.item-info small {
  color: #666;
  font-size: 12px;
}

.item-cantidad {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cantidad-input {
  width: 50px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 4px;
}

.item-precio {
  font-weight: 600;
  min-width: 70px;
  text-align: right;
}

.totales-section {
  border-top: 2px solid #e0e0e0;
  padding-top: 12px;
  margin-bottom: 16px;
}

.total-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.total-final {
  font-size: 18px;
  padding-top: 8px;
  border-top: 1px solid #e0e0e0;
}

.pago-section {
  margin-bottom: 16px;
}

.metodo-pago-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.pago-info {
  margin-top: 12px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
}

.cambio-info {
  color: #4caf50;
  font-weight: 600;
}

.acciones-section {
  display: flex;
  gap: 8px;
}

.acciones-section button {
  flex: 1;
}

/* PANTALLA CIERRE */
.pantalla-cierre {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.cierre-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  max-width: 600px;
  width: 100%;
}

.cierre-card h2 {
  text-align: center;
  margin-bottom: 30px;
}

.resumen-sesion {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.resumen-sesion h4 {
  margin-top: 0;
}

.diferencia-info {
  padding: 12px;
  border-radius: 6px;
  margin: 16px 0;
  font-weight: 600;
  font-size: 16px;
}

.diferencia-cero {
  background: #e8f5e9;
  color: #2e7d32;
}

.diferencia-positiva {
  background: #fff3e0;
  color: #f57c00;
}

.diferencia-negativa {
  background: #ffebee;
  color: #c62828;
}

.btn-group-cierre {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-group-cierre button {
  flex: 1;
}

/* MODAL */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 32px;
  border-radius: 12px;
  max-width: 500px;
  width: 100%;
}

.modal-content h3 {
  text-align: center;
  margin-bottom: 20px;
}

.venta-resumen {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  flex-direction: column;
}

.modal-actions button {
  width: 100%;
}
</style>
