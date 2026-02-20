<template>
  <div class="pos-container">
    <!-- ETAPA 1: APERTURA DE CAJA -->
    <div v-if="etapa === 'apertura'" class="etapa-apertura">
      <div class="card-center">
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
          <input v-model.number="montoApertura" type="number" class="form-control" placeholder="0.00" step="0.01" />
        </div>
        <button @click="abrirSesion" class="btn btn-primary btn-lg btn-block" :disabled="!perfilPOSSeleccionado || !montoApertura">
          Abrir Caja
        </button>
      </div>
    </div>

    <!-- ETAPA 2: AGREGAR ARTÍCULOS -->
    <div v-else-if="etapa === 'agregar-articulos'" class="etapa-agregar">
      <!-- Header con búsqueda y botón Hacer Cierre -->
      <div class="pos-header">
        <div class="header-left">
          <h3>🏪 {{ sesionActiva?.perfil_pos }}</h3>
          <small class="sesion-info">Sesión: {{ sesionActiva?.name }}</small>
          <small class="sesion-info">{{ formatDateTime(sesionActiva?.fecha_hora_apertura) }}</small>
        </div>
        <div class="header-center">
          <div class="search-wrapper">
            <input 
              v-model="busqueda" 
              @input="buscarProductos" 
              type="text" 
              class="form-control search-input" 
              placeholder="🔍 Buscar por nombre, SKU o código..."
              ref="searchInput"
            />
            <button v-if="busqueda" @click="limpiarBusqueda" class="btn-clear-search">
              ×
            </button>
          </div>
        </div>
        <div class="header-right">
          <button v-if="isMobile" @click="toggleVistaMobile" class="btn btn-icon btn-mobile-toggle" :title="vistaActualMobile === 'productos' ? 'Ver Carrito' : 'Ver Productos'">
            <span class="toggle-icon">{{ vistaActualMobile === 'productos' ? '🛒' : '📦' }}</span>
            <span v-if="carrito.length > 0 && vistaActualMobile === 'productos'" class="badge-count">{{ carrito.length }}</span>
          </button>
          <button @click="irACierre" class="btn btn-warning btn-cierre">
            <span class="text-full">💰 Hacer Cierre</span>
            <span class="text-short">💰</span>
          </button>
          <button @click="irACierre" class="btn btn-warning btn-cierre">
            <span class="text-full">💰 Hacer Cierre</span>
            <span class="text-short">💰</span>
          </button>
          <!-- Sync button hidden as per user request for "real-time" feel -->
          <!-- <button @click="sincronizarDatos" class="btn btn-info btn-sync" :disabled="cargando" title="Sincronizar Stock">
            <span :class="{ 'spin': cargando }">🔄</span>
          </button> -->
        </div>
      </div>

      <div class="pos-body">
        <!-- Panel de Productos -->
        <div class="productos-panel" :class="{ 'hidden-mobile': isMobile && vistaActualMobile === 'carrito' }">
          <div v-if="cargando" class="loading-state">
            <div class="spinner"></div>
            <p>Cargando productos...</p>
          </div>
          
          <div v-else-if="productosMostrados.length === 0" class="empty-state">
            <div class="empty-icon">📦</div>
            <p>No se encontraron productos</p>
          </div>
          
          <div v-else class="productos-grid">
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
        </div>

        <!-- Panel de Carrito (SIN MÉTODOS DE PAGO) -->
        <div class="carrito-panel" :class="{ 'hidden-mobile': isMobile && vistaActualMobile === 'productos' }">
          <h4 class="panel-title">Carrito de Compra</h4>
          
          <div class="carrito-items">
            <div v-if="carrito.length === 0" class="empty-cart">
              <div class="empty-icon">🛒</div>
              <p>Carrito vacío</p>
              <small>Selecciona productos para agregar</small>
            </div>
            
            <div v-else>
              <div v-for="(item, idx) in carrito" :key="idx" class="carrito-item">
                <div class="item-main">
                  <div class="item-info">
                    <strong>{{ item.name }}</strong>
                    <small>{{ item.sku }}</small>
                  </div>
                  <button @click="eliminarDelCarrito(idx)" class="btn-icon btn-danger">
                    <span>🗑️</span>
                  </button>
                </div>
                <div class="item-controls">
                  <div class="cantidad-control">
                    <button @click="decrementarCantidad(idx)" class="btn-qty">-</button>
                    <input v-model.number="item.cantidad" type="number" min="1" class="qty-input" />
                    <button @click="incrementarCantidad(idx)" class="btn-qty">+</button>
                  </div>
                  <div class="item-precio">
                    ${{ formatCurrency(item.precio * item.cantidad) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Totales Preliminares -->
          <div class="totales-section">
            <div class="total-row">
              <span>Subtotal:</span>
              <span>${{ formatCurrency(subtotal) }}</span>
            </div>
            <div class="total-row">
              <span>Impuestos (est.):</span>
              <span>${{ formatCurrency(totalImpuestos) }}</span>
            </div>
            <div class="total-row total-final">
              <strong>Total:</strong>
              <strong>${{ formatCurrency(totalFinal) }}</strong>
            </div>
          </div>

          <!-- Botones de Acción -->
          <div class="acciones-carrito">
            <button @click="limpiarCarrito" class="btn btn-secondary btn-block" :disabled="carrito.length === 0">
              🗑️ Limpiar Carrito
            </button>
            <button @click="irAResumenPago" class="btn btn-success btn-lg btn-block" :disabled="carrito.length === 0">
              Continuar al Pago →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ETAPA 3: RESUMEN Y PAGO -->
    <div v-else-if="etapa === 'resumen-pago'" class="etapa-resumen">
      <div class="resumen-container">
        <!-- Header -->
        <div class="resumen-header">
          <button @click="volverAProductos" class="btn btn-secondary">
            ← Volver
          </button>
          <h3>Resumen del Pedido y Pago</h3>
          <div></div>
        </div>

        <div class="resumen-body">
          <!-- Columna Izquierda: Resumen de Productos -->
          <div class="resumen-productos">
            <h4>Productos Seleccionados</h4>
            <div class="resumen-items">
              <div v-for="(item, idx) in carrito" :key="idx" class="resumen-item">
                <div class="item-detalle">
                  <strong>{{ item.name }}</strong>
                  <small>{{ item.sku }}</small>
                </div>
                <div class="item-cantidad">x{{ item.cantidad }}</div>
                <div class="item-precio">${{ formatCurrency(item.precio * item.cantidad) }}</div>
              </div>
            </div>
            
            <div class="resumen-totales">
              <div class="total-row"><span>Subtotal:</span><span>${{ formatCurrency(subtotal) }}</span></div>
              <div class="total-row"><span>Impuestos:</span><span>${{ formatCurrency(totalImpuestos) }}</span></div>
              <div class="total-row total-final"><strong>Total a Pagar:</strong><strong>${{ formatCurrency(totalFinal) }}</strong></div>
            </div>
          </div>

          <!-- Columna Derecha: Cliente y Métodos de Pago -->
          <div class="resumen-pago">
            <!-- Cliente -->
            <div class="pago-section">
              <h4>Cliente (Opcional)</h4>
              <div class="form-group">
                <div id="cliente-link-field"></div>
              </div>
            </div>

            <!-- Métodos de Pago -->
            <div class="pago-section">
              <h4>Métodos de Pago</h4>
              <div class="metodos-pago-list">
                <div v-for="(metodo, idx) in metodosPago" :key="idx" class="metodo-pago-item">
                  <select v-model="metodo.metodo" class="form-control">
                    <option v-for="m in metodosDisponibles" :key="m" :value="m">{{ m }}</option>
                  </select>
                  <input 
                    v-model.number="metodo.monto" 
                    type="number" 
                    class="form-control" 
                    placeholder="Monto" 
                    step="0.01"
                    @input="calcularCambio"
                  />
                  <button 
                    @click="eliminarMetodoPago(idx)" 
                    class="btn-icon btn-danger"
                    :disabled="metodosPago.length === 1"
                  >
                    ×
                  </button>
                </div>
              </div>
              <button @click="agregarMetodoPago" class="btn btn-sm btn-secondary">
                + Agregar Método
              </button>
            </div>

            <!-- Información de Pago -->
            <div class="pago-info">
              <div class="info-row">
                <span>Total a Pagar:</span>
                <strong>${{ formatCurrency(totalFinal) }}</strong>
              </div>
              <div class="info-row">
                <span>Total Pagado:</span>
                <strong :class="{ 'text-success': totalPagado >= totalFinal, 'text-danger': totalPagado < totalFinal }">
                  ${{ formatCurrency(totalPagado) }}
                </strong>
              </div>
              <div v-if="totalPagado < totalFinal" class="info-row text-danger">
                <span>Falta:</span>
                <strong>${{ formatCurrency(totalFinal - totalPagado) }}</strong>
              </div>
              <div v-if="cambioCalculado > 0" class="info-row cambio-destacado">
                <span>Cambio:</span>
                <strong>${{ formatCurrency(cambioCalculado) }}</strong>
              </div>
            </div>

            <!-- Botón Finalizar Venta -->
            <button 
              @click="procesarVenta" 
              class="btn btn-success btn-lg btn-block"
              :disabled="!puedeFinalizarVenta"
            >
              ✓ Finalizar Venta
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ETAPA 4: TICKET/NOTA DE VENTA -->
    <div v-if="mostrarTicket" class="etapa-ticket">
      <div class="ticket-modal">
        <div class="ticket-content">
          <div class="ticket-header">
            <h2>✅ Venta Exitosa</h2>
          </div>
          
          <div class="ticket-body">
            <div class="ticket-info">
              <div class="info-item">
                <span>Nota de Venta:</span>
                <strong>{{ ultimaVenta.name }}</strong>
              </div>
              <div class="info-item">
                <span>Total:</span>
                <strong>${{ formatCurrency(ultimaVenta.total_final) }}</strong>
              </div>
              <div v-if="ultimaVenta.cambio > 0" class="info-item cambio">
                <span>Cambio:</span>
                <strong>${{ formatCurrency(ultimaVenta.cambio) }}</strong>
              </div>
            </div>
          </div>

          <div class="ticket-actions">
            <button @click="imprimirTicket" class="btn btn-primary btn-lg">
              🖨️ Imprimir Ticket
            </button>
            <button @click="nuevaVenta" class="btn btn-success btn-lg">
              🛒 Nueva Venta
            </button>
            <button @click="irACierreDesdeTicket" class="btn btn-warning btn-lg">
              💰 Hacer Cierre
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ETAPA 5: CIERRE DE CAJA -->
    <div v-else-if="etapa === 'cierre'" class="etapa-cierre">
      <div class="card-center card-wide">
        <h2>💰 Cierre de Caja</h2>
        
        <div class="cierre-resumen">
          <h4>Resumen de la Sesión</h4>
          <div class="resumen-grid">
            <div class="resumen-item">
              <label>Sesión:</label>
              <span>{{ sesionActiva?.name }}</span>
            </div>
            <div class="resumen-item">
              <label>Total de Ventas:</label>
              <span>{{ ventasSesion.length }}</span>
            </div>
            <div class="resumen-item">
              <label>Monto Apertura:</label>
              <span>${{ formatCurrency(sesionActiva?.monto_apertura || 0) }}</span>
            </div>
            <div class="resumen-item">
              <label>Efectivo Sistema:</label>
              <span>${{ formatCurrency(efectivoSistema) }}</span>
            </div>
            <div class="resumen-item">
              <label>Tarjeta Sistema:</label>
              <span>${{ formatCurrency(tarjetaSistema) }}</span>
            </div>
            <div class="resumen-item">
              <label>Total Sistema:</label>
              <span>${{ formatCurrency(totalSistema) }}</span>
            </div>
          </div>
        </div>

        <div class="form-group">
          <label>Efectivo Contado (Arqueo)</label>
          <input 
            v-model.number="efectivoContado" 
            type="number" 
            class="form-control" 
            placeholder="Ingresar efectivo contado..." 
            step="0.01"
            @input="calcularDiferencia"
          />
        </div>

        <div v-if="efectivoContado !== null" class="diferencia-box" :class="diferenciaCierreClass">
          <span>Diferencia:</span>
          <strong>${{ formatCurrency(diferenciaCierre) }}</strong>
        </div>

        <div class="form-group">
          <label>Observaciones</label>
          <textarea 
            v-model="observacionesCierre" 
            class="form-control" 
            rows="3"
            placeholder="Observaciones sobre el cierre..."
          ></textarea>
        </div>

        <div class="cierre-actions">
          <button @click="volverAProductos" class="btn btn-secondary btn-lg">
            ← Volver a Ventas
          </button>
          <button 
            @click="cerrarSesion" 
            class="btn btn-primary btn-lg"
            :disabled="efectivoContado === null"
          >
            Cerrar Sesión
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue';

// ============================================================================
// ESTADOS PRINCIPALES
// ============================================================================

const etapa = ref('apertura'); // 'apertura' | 'agregar-articulos' | 'resumen-pago' | 'cierre'
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
const searchInput = ref(null);

// Carrito
const carrito = ref([]);
const clienteSeleccionado = ref('');
let clienteLinkField = null;

// Métodos de pago
const metodosPago = ref([{ metodo: '', monto: 0 }]);
const metodosDisponibles = ref([]);

// Modal y última venta
const mostrarTicket = ref(false);
const ultimaVenta = ref({});

// Cierre
const efectivoContado = ref(null);
const observacionesCierre = ref('');
const ventasSesion = ref([]);
const pollingInterval = ref(null);
const ultimaSincronizacion = ref(null);

// Responsividad
const isMobile = ref(window.innerWidth <= 768);
const vistaActualMobile = ref('productos'); // 'productos' | 'carrito'

// ============================================================================
// PERSISTENCIA LOCAL
// ============================================================================

const STORAGE_KEY = 'pos_state_v1';

function saveLocalState() {
  if (!sesionActiva.value) return; // Solo guardar si hay sesión
  
  const state = {
    carrito: carrito.value,
    etapa: etapa.value,
    clienteSeleccionado: clienteSeleccionado.value,
    metodosPago: metodosPago.value,
    perfilPOSSeleccionado: perfilPOSSeleccionado.value,
    montoApertura: montoApertura.value,
    sesionId: sesionActiva.value.name,
    timestamp: Date.now()
  };
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function loadLocalState() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (!saved) return false;
  
  try {
    const state = JSON.parse(saved);
    
    // Validar que sea de la misma sesión (si existe sesión activa)
    if (sesionActiva.value && state.sesionId !== sesionActiva.value.name) {
      console.warn('Estado local de otra sesión, limpiando...');
      localStorage.removeItem(STORAGE_KEY);
      return false;
    }
    
    // Restaurar valores
    if (state.carrito) carrito.value = state.carrito;
    if (state.etapa) etapa.value = state.etapa;
    if (state.clienteSeleccionado) clienteSeleccionado.value = state.clienteSeleccionado;
    if (state.metodosPago) metodosPago.value = state.metodosPago;
    if (state.perfilPOSSeleccionado) perfilPOSSeleccionado.value = state.perfilPOSSeleccionado;
    if (state.montoApertura) montoApertura.value = state.montoApertura;
    
    return true;
  } catch (e) {
    console.error('Error cargando estado local:', e);
    return false;
  }
}

function clearLocalState() {
  localStorage.removeItem(STORAGE_KEY);
}

// ============================================================================
// CICLO DE VIDA
// ============================================================================

onMounted(async () => {
  detectarTheme();
  
  // Listener para responsividad
  window.addEventListener('resize', handleResize);
  
  await verificarSesionActiva();
  
  if (!sesionActiva.value) {
    await cargarPerfiles();
  } else {
    // Intentar cargar estado local primero
    const restored = loadLocalState();
    
    if (!restored) {
        etapa.value = 'agregar-articulos';
    }
    
    await cargarProductosIniciales();
    
    // Iniciar polling de stock
    iniciarPollingStock();
    
    nextTick(() => {
      if (searchInput.value) {
        searchInput.value.focus();
      }
    });
  }
  
  // Watchers para persistencia
  watch([carrito, etapa, clienteSeleccionado, metodosPago], () => {
    saveLocalState();
  }, { deep: true });
});

import { watch, onUnmounted } from 'vue';

onUnmounted(() => {
    detenerPollingStock();
});

// ============================================================================
// DETECCIÓN DE THEME
// ============================================================================

function detectarTheme() {
  // Detectar theme de Frappe correctamente
  const updateTheme = () => {
    const isDark = document.documentElement.getAttribute('data-theme-mode') === 'dark' ||
                   document.body.classList.contains('dark') ||
                   document.documentElement.classList.contains('dark');
    
    document.documentElement.setAttribute('data-pos-theme', isDark ? 'dark' : 'light');
  };
  
  updateTheme();
  
  // Observer para cambios de theme
  const observer = new MutationObserver(updateTheme);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme-mode', 'class']
  });
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ['class']
  });
}

// ============================================================================
// RESPONSIVIDAD
// ============================================================================

function handleResize() {
  isMobile.value = window.innerWidth <= 768;
  // En desktop siempre mostrar ambos paneles
  if (!isMobile.value) {
    vistaActualMobile.value = 'productos';
  }
}

function toggleVistaMobile() {
  vistaActualMobile.value = vistaActualMobile.value === 'productos' ? 'carrito' : 'productos';
}

function limpiarBusqueda() {
  busqueda.value = '';
  productosMostrados.value = productos.value;
}

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
      // Cargar las ventas de la sesión si existen
      if (res.message.ventas && res.message.ventas.length > 0) {
        ventasSesion.value = res.message.ventas.map(v => ({
          nota_de_venta: v.nota_de_venta,
          total: v.total,
          metodo_pago: v.metodo_pago
        }));
      }
      
      // Cargar métodos de pago del perfil
      await cargarMetodosPago(res.message.perfil_pos);
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
    ventasSesion.value = []; // Nueva sesión sin ventas
    etapa.value = 'agregar-articulos';
    
    await cargarMetodosPago(perfilPOSSeleccionado.value);
    await cargarProductosIniciales();
    window.frappe.show_alert({ message: 'Sesión abierta exitosamente', indicator: 'green' });
    
    // Iniciar polling
    iniciarPollingStock();
    saveLocalState();
    
    nextTick(() => {
      if (searchInput.value) {
        searchInput.value.focus();
      }
    });
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
    await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.close_pos_session',
      args: {
        sesion_pos: sesionActiva.value.name,
        efectivo_contado: efectivoContado.value,
        observaciones: observacionesCierre.value
      }
    });
    
    window.frappe.show_alert({ message: 'Sesión cerrada exitosamente', indicator: 'green' });
    
    // Resetear todo
    sesionActiva.value = null;
    efectivoContado.value = null;
    observacionesCierre.value = '';
    ventasSesion.value = [];
    carrito.value = [];
    etapa.value = 'apertura';
    
    clearLocalState();
    detenerPollingStock();
    
    await cargarPerfiles();
  } catch (error) {
    console.error('Error cerrando sesión:', error);
    window.frappe.show_alert({ message: 'Error al cerrar sesión', indicator: 'red' });
  }
}

async function cargarMetodosPago(perfil) {
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.get_pos_payment_methods',
      args: { profile_name: perfil }
    });
    
    if (res.message && res.message.length > 0) {
      metodosDisponibles.value = res.message.map(m => m.metodo);
      
      // Establecer predeterminado si existe
      const predeterminado = res.message.find(m => m.predeterminado);
      const defaultMethod = predeterminado ? predeterminado.metodo : res.message[0].metodo;
      
      // Actualizar método inicial si está vacío
      if (metodosPago.value.length === 1 && !metodosPago.value[0].metodo) {
         metodosPago.value[0].metodo = defaultMethod;
      }
    } else {
      metodosDisponibles.value = [];
      window.frappe.show_alert({ message: 'No hay métodos de pago configurados para este perfil', indicator: 'orange' });
    }
  } catch (error) {
    console.error('Error cargando métodos de pago:', error);
  }
}

// ============================================================================
// PRODUCTOS Y STOCK
// ============================================================================

function iniciarPollingStock() {
  if (pollingInterval.value) return;

  // Suscribirse a eventos de actualización de stock en tiempo real
  frappe.realtime.on('stock_updated', (data) => {
    actualizarStockProducto(data.producto, data.cantidad_disponible);
  });

  // Polling cada 30 segundos como respaldo (reducido de 5 segundos)
  pollingInterval.value = setInterval(() => {
    sincronizarDatos(true);
  }, 30000);
}

function detenerPollingStock() {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value);
    pollingInterval.value = null;
  }

  // Desuscribirse de eventos realtime
  frappe.realtime.off('stock_updated');
}

function actualizarStockProducto(productoName, cantidadDisponible) {
  // Actualizar en la lista de productos
  const productoIdx = productos.value.findIndex(p => p.name === productoName);
  if (productoIdx !== -1) {
    productos.value[productoIdx].cantidad_disponible = cantidadDisponible;
  }

  // Actualizar en productos mostrados
  const mostradoIdx = productosMostrados.value.findIndex(p => p.name === productoName);
  if (mostradoIdx !== -1) {
    productosMostrados.value[mostradoIdx].cantidad_disponible = cantidadDisponible;
  }

  // Actualizar en el carrito si existe
  const carritoIdx = carrito.value.findIndex(item => item.name === productoName);
  if (carritoIdx !== -1) {
    carrito.value[carritoIdx].cantidad_disponible = cantidadDisponible;
  }
}

async function sincronizarDatos(silencioso = false) {
  if (!sesionActiva.value) return;
  
  if (!silencioso) {
    cargando.value = true;
  }
  
  try {
    // 1. Actualizar productos y stock
    const perfil = await obtenerPerfil();
    const resProductos = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.get_products_with_price',
      args: { 
        lista_de_precios: perfil.lista_de_precios,
        limit: 100
      }
    });
    
    // Actualizar lista de productos manteniendo estado local si es necesario
    // Aquí reemplazamos todo, pero podríamos hacer merge si fuera más complejo
    productos.value = resProductos.message || [];
    
    // Si no hay búsqueda activa, actualizar mostrados
    if (!busqueda.value) {
      productosMostrados.value = productos.value;
    }
    
    // 2. Actualizar ventas de la sesión (para totales)
    const resSesion = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.get_active_session'
    });
    
    if (resSesion.message) {
      if (resSesion.message.ventas) {
        ventasSesion.value = resSesion.message.ventas.map(v => ({
          nota_de_venta: v.nota_de_venta,
          total: v.total,
          metodo_pago: v.metodo_pago
        }));
      } else {
        ventasSesion.value = [];
      }
    }
    
    ultimaSincronizacion.value = new Date();
    
    if (!silencioso) {
      window.frappe.show_alert({ message: 'Datos sincronizados', indicator: 'green' });
    }
    
  } catch (error) {
    console.error('Error sincronizando datos:', error);
    if (!silencioso) {
      window.frappe.show_alert({ message: 'Error al sincronizar', indicator: 'red' });
    }
  } finally {
    if (!silencioso) {
      cargando.value = false;
    }
  }
}

async function cargarProductosIniciales() {
  if (!sesionActiva.value) return;
  
  cargando.value = true;
  try {
    const perfil = await obtenerPerfil();
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.get_products_with_price',
      args: { 
        lista_de_precios: perfil.lista_de_precios,
        limit: 100
      }
    });
    productos.value = res.message || [];
    productosMostrados.value = productos.value;
    ultimaSincronizacion.value = new Date();
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
          limit: 50
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
  
  window.frappe.show_alert({ 
    message: `${prod.name} agregado al carrito`, 
    indicator: 'green' 
  });
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
    window.frappe.show_alert({ message: 'Carrito limpiado', indicator: 'blue' });
  }
}

// ============================================================================
// NAVEGACIÓN ENTRE ETAPAS
// ============================================================================

function irAResumenPago() {
  if (carrito.value.length === 0) {
    window.frappe.show_alert({ message: 'El carrito está vacío', indicator: 'red' });
    return;
  }
  
  etapa.value = 'resumen-pago';
  
  // Inicializar Link Field para Cliente
  nextTick(() => {
    inicializarClienteLink();
    
    // Auto-completar total en primer método de pago
    if (metodosPago.value.length > 0) {
      metodosPago.value[0].monto = totalFinal.value;
      
      // Asegurar que tenga un método seleccionado
      if (!metodosPago.value[0].metodo && metodosDisponibles.value.length > 0) {
        metodosPago.value[0].metodo = metodosDisponibles.value[0];
      }
    }
  });
}

function volverAProductos() {
  etapa.value = 'agregar-articulos';
  nextTick(() => {
    if (searchInput.value) {
      searchInput.value.focus();
    }
  });
}

function irACierre() {
  etapa.value = 'cierre';
}

function irACierreDesdeTicket() {
  mostrarTicket.value = false;
  etapa.value = 'cierre';
}

// ============================================================================
// CLIENTE LINK FIELD
// ============================================================================

function inicializarClienteLink() {
  const container = document.getElementById('cliente-link-field');
  if (!container || clienteLinkField) return;
  
  clienteLinkField = frappe.ui.form.make_control({
    parent: container,
    df: {
      fieldtype: 'Link',
      fieldname: 'cliente',
      options: 'Cliente',
      label: 'Buscar Cliente',
      placeholder: 'Escribir para buscar...',
      onchange: function() {
        clienteSeleccionado.value = this.get_value();
      }
    },
    render_input: true
  });
  
  clienteLinkField.refresh();
}

// ============================================================================
// MÉTODOS DE PAGO
// ============================================================================

function agregarMetodoPago() {
  const defaultMethod = metodosDisponibles.value.length > 0 ? metodosDisponibles.value[0] : '';
  metodosPago.value.push({ metodo: defaultMethod, monto: 0 });
}

function eliminarMetodoPago(idx) {
  if (metodosPago.value.length > 1) {
    metodosPago.value.splice(idx, 1);
  }
}

function calcularCambio() {
  // Se calcula automáticamente en el computed cambioCalculado
}

function calcularDiferencia() {
  // Se calcula automáticamente en el computed diferenciaCierre
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
  return subtotal.value * 0.16;
});

const totalFinal = computed(() => {
  return subtotal.value + totalImpuestos.value;
});

const totalPagado = computed(() => {
  return metodosPago.value.reduce((sum, m) => sum + (parseFloat(m.monto) || 0), 0);
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
  return efectivoContado.value - (efectivoSistema.value + (sesionActiva.value.monto_apertura || 0));
});

const diferenciaCierreClass = computed(() => {
  const diff = diferenciaCierre.value;
  if (diff > 0.1) return 'diferencia-positiva';
  if (diff < -0.1) return 'diferencia-negativa';
  return 'diferencia-cero';
});

// ============================================================================
// PROCESAR VENTA
// ============================================================================

async function procesarVenta() {
  if (!puedeFinalizarVenta.value) {
    window.frappe.show_alert({ message: 'Complete el pago correctamente', indicator: 'red' });
    return;
  }
  
  const items = carrito.value.map(item => ({
    producto: item.producto,
    cantidad: item.cantidad,
    precio_unitario: item.precio_unitario,
    descuento_porcentaje: item.descuento_porcentaje || 0,
    detalle_lote_serie: []
  }));
  
  const pagos = metodosPago.value.filter(m => m.monto > 0);
  
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.create_nota_de_venta',
      args: {
        sesion_pos: sesionActiva.value.name,
        perfil_pos: sesionActiva.value.perfil_pos,
        cliente: clienteSeleccionado.value || null,
        items: JSON.stringify(items),
        metodos_pago: JSON.stringify(pagos),
        descuento_global: 0
      }
    });
    
    ultimaVenta.value = res.message;
    mostrarTicket.value = true;
    

    ventasSesion.value.push({
      nota_de_venta: res.message.name,
      total: res.message.total_final,
      metodo_pago: pagos[0]?.metodo || (metodosDisponibles.value[0] || 'Efectivo')
    });
    
    // Limpiar carrito del estado local pero mantener sesión
    carrito.value = [];
    saveLocalState();
    
  } catch (error) {
    console.error('Error procesando venta:', error);
    window.frappe.show_alert({ message: 'Error al procesar venta', indicator: 'red' });
  }
}

// ============================================================================
// POST-VENTA
// ============================================================================

function nuevaVenta() {
  carrito.value = [];
  clienteSeleccionado.value = '';
  const defaultMethod = metodosDisponibles.value.length > 0 ? metodosDisponibles.value[0] : '';
  metodosPago.value = [{ metodo: defaultMethod, monto: 0 }];
  mostrarTicket.value = false;
  etapa.value = 'agregar-articulos';
  busqueda.value = '';
  productosMostrados.value = productos.value;
  
  nextTick(() => {
    if (searchInput.value) {
      searchInput.value.focus();
    }
  });
}

async function imprimirTicket() {
  try {
    const res = await window.frappe.call({
      method: 'endersuite.ventas.services.pos_service.generate_ticket_html',
      args: {
        nota_venta_name: ultimaVenta.value.name
      }
    });
    
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
/* VARIABLES ADAPTADAS AL THEME DE FRAPPE */
:root {
  --pos-bg: var(--bg-color, #f5f7fa);
  --pos-card-bg: var(--card-bg, #ffffff);
  --pos-text: var(--text-color, #1f272e);
  --pos-text-muted: var(--text-muted, #6c757d);
  --pos-border: var(--border-color, #d1d8dd);
  --pos-primary: var(--primary, #2490ef);
  --pos-success: var(--success, #28a745);
  --pos-danger: var(--danger, #dc3545);
  --pos-warning: var(--warning, #ffc107);
  --pos-shadow: 0 2px 4px rgba(0,0,0,0.1);
  --pos-shadow-lg: 0 4px 12px rgba(0,0,0,0.15);
}

/* Theme Oscuro */
[data-pos-theme="dark"] {
  --pos-bg: #1c1e21;
  --pos-card-bg: #262729;
  --pos-text: #e8e9ea;
  --pos-text-muted: #a8aaad;
  --pos-border: #3e4146;
}

.pos-container {
  height: 100vh;
  background: var(--pos-bg);
  color: var(--pos-text);
}

/* COMPONENTES COMUNES */
.card-center {
  background: var(--pos-card-bg);
  padding: 40px;
  border-radius: 12px;
  box-shadow: var(--pos-shadow-lg);
  max-width: 450px;
  width: 100%;
  margin: auto;
  position: relative;
  overflow: visible;
  z-index: 1;
}

.card-wide {
  max-width: 700px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--pos-text);
}

.form-control {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--pos-border);
  border-radius: 6px;
  background: var(--pos-card-bg);
  color: var(--pos-text);
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: var(--pos-primary);
  box-shadow: 0 0 0 3px rgba(36, 144, 239, 0.1);
}

select.form-control {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23666' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
  position: relative;
  z-index: 10000;
}

select.form-control option {
  background: var(--pos-card-bg);
  color: var(--pos-text);
  padding: 8px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-block {
  display: block;
  width: 100%;
}

.btn-lg {
  padding: 14px 24px;
  font-size: 16px;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-primary {
  background: var(--pos-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-success {
  background: var(--pos-success);
  color: white;
}

.btn-success:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-danger {
  background: var(--pos-danger);
  color: white;
}

.btn-warning {
  background: var(--pos-warning);
  color: #000;
}

.btn-secondary {
  background: var(--pos-text-muted);
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon {
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.btn-sync {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-left: 8px;
}

.btn-info {
  background: #17a2b8;
  color: white;
}

.spin {
  animation: spin 1s linear infinite;
}

/* ETAPA 1: APERTURA */
.etapa-apertura {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  overflow: visible;
  padding: 20px;
}

.etapa-apertura h2 {
  text-align: center;
  margin-bottom: 30px;
  color: var(--pos-text);
}

/* ETAPA 2: AGREGAR ARTÍCULOS */
.etapa-agregar {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.pos-header {
  background: var(--pos-card-bg);
  padding: 16px 24px;
  box-shadow: var(--pos-shadow);
  display: flex;
  align-items: center;
  gap: 20px;
  border-bottom: 1px solid var(--pos-border);
}

.header-left {
  flex: 1;
}

.header-left h3 {
  margin: 0 0 4px 0;
  color: var(--pos-text);
  font-size: 18px;
}

.header-left small {
  color: var(--pos-text-muted);
  font-size: 12px;
}

.header-center {
  flex: 2;
}

.search-input {
  font-size: 16px;
  padding: 12px 16px;
}

.header-right {
  flex: 0;
}

.pos-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Panel de Productos */
.productos-panel {
  flex: 2;
  padding: 20px;
  overflow-y: auto;
  background: var(--pos-bg);
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 50vh;
  color: var(--pos-text-muted);
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid var(--pos-border);
  border-top-color: var(--pos-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.productos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.producto-card {
  background: var(--pos-card-bg);
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid var(--pos-border);
}

.producto-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--pos-shadow-lg);
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
  background: var(--pos-bg);
  border-radius: 6px;
  margin-bottom: 8px;
  overflow: hidden;
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
  color: var(--pos-text);
}

.producto-sku {
  font-size: 12px;
  color: var(--pos-text-muted);
  margin-bottom: 4px;
}

.producto-precio {
  font-size: 16px;
  font-weight: 700;
  color: var(--pos-primary);
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

/* Panel de Carrito */
.carrito-panel {
  flex: 0 0 400px;
  background: var(--pos-card-bg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid var(--pos-border);
  overflow-y: auto;
}

.panel-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: var(--pos-text);
  padding-bottom: 12px;
  border-bottom: 2px solid var(--pos-border);
}

.carrito-items {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.empty-cart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--pos-text-muted);
}

.empty-cart .empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.carrito-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid var(--pos-border);
  border-radius: 6px;
  background: var(--pos-bg);
}

.item-main {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 8px;
}

.item-info {
  flex: 1;
}

.item-info strong {
  display: block;
  font-size: 14px;
  color: var(--pos-text);
  margin-bottom: 2px;
}

.item-info small {
  color: var(--pos-text-muted);
  font-size: 12px;
}

.item-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cantidad-control {
  display: flex;
  gap: 6px;
  align-items: center;
}

.btn-qty {
  width: 28px;
  height: 28px;
  border: 1px solid var(--pos-border);
  background: var(--pos-card-bg);
  color: var(--pos-text);
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
}

.btn-qty:hover {
  background: var(--pos-primary);
  color: white;
  border-color: var(--pos-primary);
}

.qty-input {
  width: 50px;
  text-align: center;
  padding: 4px;
  border: 1px solid var(--pos-border);
  border-radius: 4px;
  background: var(--pos-card-bg);
  color: var(--pos-text);
}

.item-precio {
  font-weight: 600;
  font-size: 16px;
  color: var(--pos-text);
}

.totales-section {
  padding: 16px;
  background: var(--pos-bg);
  border-radius: 6px;
  margin-bottom: 16px;
}

.total-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--pos-text);
}

.total-final {
  font-size: 20px;
  padding-top: 12px;
  margin-top: 8px;
  border-top: 2px solid var(--pos-border);
}

.acciones-carrito {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ETAPA 3: RESUMEN Y PAGO */
.etapa-resumen {
  height: 100%;
  overflow-y: auto;
  padding: 20px;
  background: var(--pos-bg);
}

.resumen-container {
  max-width: 1200px;
  margin: 0 auto;
}

.resumen-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--pos-border);
}

.resumen-header h3 {
  margin: 0;
  font-size: 24px;
  color: var(--pos-text);
}

.resumen-body {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 24px;
}

.resumen-productos, .resumen-pago {
  background: var(--pos-card-bg);
  padding: 24px;
  border-radius: 12px;
  box-shadow: var(--pos-shadow);
}

.resumen-productos h4, .resumen-pago h4 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: var(--pos-text);
  padding-bottom: 12px;
  border-bottom: 2px solid var(--pos-border);
}

.resumen-items {
  margin-bottom: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.resumen-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  background: var(--pos-bg);
  border-radius: 6px;
}

.item-detalle strong {
  display: block;
  font-size: 14px;
  color: var(--pos-text);
  margin-bottom: 2px;
}

.item-detalle small {
  color: var(--pos-text-muted);
  font-size: 12px;
}

.item-cantidad {
  padding: 4px 12px;
  background: var(--pos-border);
  border-radius: 4px;
  font-weight: 600;
  color: var(--pos-text);
}

.resumen-totales {
  padding: 16px;
  background: var(--pos-bg);
  border-radius: 6px;
}

.pago-section {
  margin-bottom: 24px;
}

#cliente-link-field {
  margin-top: 8px;
}

.metodos-pago-list {
  margin-bottom: 12px;
}

.metodo-pago-item {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.metodo-pago-item .form-control {
  flex: 1;
}

.pago-info {
  padding: 16px;
  background: var(--pos-bg);
  border-radius: 6px;
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--pos-text);
}

.text-success {
  color: var(--pos-success) !important;
}

.text-danger {
  color: var(--pos-danger) !important;
}

.cambio-destacado {
  padding: 12px;
  background: #e8f5e9;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 600;
  color: #2e7d32;
}

[data-pos-theme="dark"] .cambio-destacado {
  background: rgba(76, 175, 80, 0.2);
  color: #81c784;
}

/* ETAPA 4: TICKET */
.etapa-ticket {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.ticket-modal {
  background: var(--pos-card-bg);
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  box-shadow: var(--pos-shadow-lg);
}

.ticket-content {
  padding: 32px;
}

.ticket-header {
  text-align: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--pos-border);
}

.ticket-header h2 {
  margin: 0;
  font-size: 28px;
  color: var(--pos-success);
}

.ticket-body {
  margin-bottom: 24px;
}

.ticket-info {
  background: var(--pos-bg);
  padding: 20px;
  border-radius: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 16px;
  color: var(--pos-text);
}

.info-item.cambio {
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid var(--pos-border);
  color: var(--pos-success);
  font-size: 18px;
}

.ticket-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ETAPA 5: CIERRE */
.etapa-cierre {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
}

.etapa-cierre h2 {
  text-align: center;
  margin-bottom: 24px;
  color: var(--pos-text);
}

.cierre-resumen {
  background: var(--pos-bg);
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.cierre-resumen h4 {
  margin: 0 0 16px 0;
  color: var(--pos-text);
}

.resumen-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.resumen-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: var(--pos-text);
}

.resumen-item label {
  color: var(--pos-text-muted);
  font-weight: 500;
}

.diferencia-box {
  display: flex;
  justify-content: space-between;
  padding: 16px;
  border-radius: 6px;
  margin: 16px 0;
  font-size: 18px;
  font-weight: 600;
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

[data-pos-theme="dark"] .diferencia-cero {
  background: rgba(76, 175, 80, 0.2);
  color: #81c784;
}

[data-pos-theme="dark"] .diferencia-positiva {
  background: rgba(255, 152, 0, 0.2);
  color: #ffb74d;
}

[data-pos-theme="dark"] .diferencia-negativa {
  background: rgba(244, 67, 54, 0.2);
  color: #ef5350;
}

.cierre-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.cierre-actions button {
  flex: 1;
}

/* HEADER ESPECÍFICO */
.search-wrapper {
  position: relative;
  width: 100%;
}

.btn-clear-search {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: var(--pos-text-muted);
  color: white;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  transition: all 0.2s;
}

.btn-clear-search:hover {
  background: var(--pos-danger);
}

.btn-mobile-toggle {
  position: relative;
  background: var(--pos-primary);
  color: white;
  width: 48px;
  height: 48px;
  font-size: 20px;
}

.badge-count {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--pos-danger);
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 11px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sesion-info, .sesion-fecha {
  display: block;
}

.text-short {
  display: none;
}

.hidden-mobile {
  display: none !important;
}

/* RESPONSIVE */
@media (max-width: 1200px) {
  .productos-grid {
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  }
  
  .carrito-panel {
    flex: 0 0 380px;
  }
}

@media (max-width: 1024px) {
  .pos-header {
    flex-wrap: wrap;
    gap: 12px;
  }
  
  .header-left {
    flex: 1 1 auto;
  }
  
  .header-center {
    order: 3;
    flex: 100%;
  }
  
  .header-right {
    flex: 0 0 auto;
    display: flex;
    gap: 8px;
  }
  
  .carrito-panel {
    flex: 0 0 350px;
  }
  
  .productos-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }
  
  .resumen-body {
    grid-template-columns: 1fr;
  }
  
  .sesion-fecha {
    display: none;
  }
}

@media (max-width: 768px) {
  /* Header mobile */
  .pos-header {
    padding: 12px 16px;
  }
  
  .header-left h3 {
    font-size: 16px;
  }
  
  .header-left small {
    font-size: 11px;
  }
  
  .search-input {
    font-size: 14px;
    padding: 10px 40px 10px 12px;
  }
  
  .text-full {
    display: none;
  }
  
  .text-short {
    display: inline;
  }
  
  .btn-cierre {
    width: 48px;
    height: 48px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  /* Body mobile - toggle entre paneles */
  .pos-body {
    position: relative;
  }
  
  .productos-panel,
  .carrito-panel {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    transition: transform 0.3s ease;
  }
  
  .productos-panel.hidden-mobile,
  .carrito-panel.hidden-mobile {
    display: block !important;
    transform: translateX(-100%);
    pointer-events: none;
  }
  
  .carrito-panel {
    flex: 1;
    border-left: none;
    box-shadow: -2px 0 8px rgba(0,0,0,0.1);
  }
  
  /* Productos grid mobile */
  .productos-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .producto-card {
    padding: 10px;
  }
  
  .producto-imagen {
    height: 100px;
  }
  
  .producto-nombre {
    font-size: 13px;
  }
  
  .producto-precio {
    font-size: 14px;
  }
  
  /* Carrito items mobile */
  .carrito-item {
    padding: 10px;
    margin-bottom: 10px;
  }
  
  .item-info strong {
    font-size: 13px;
  }
  
  /* Modales y cards mobile */
  .card-center {
    padding: 24px;
    max-width: 100%;
    margin: 16px;
  }
  
  .ticket-modal {
    max-width: 90%;
    margin: 0 16px;
  }
  
  .ticket-content {
    padding: 24px;
  }
  
  /* Cierre mobile */
  .resumen-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .cierre-actions {
    flex-direction: column;
  }
  
  .cierre-actions button {
    width: 100%;
  }
  
  /* Resumen pago mobile */
  .resumen-container {
    padding: 16px;
  }
  
  .resumen-header h3 {
    font-size: 20px;
  }
  
  .resumen-productos,
  .resumen-pago {
    padding: 16px;
  }
  
  .metodo-pago-item {
    flex-direction: column;
    gap: 8px;
  }
  
  .metodo-pago-item .form-control {
    width: 100%;
  }
  
  .btn-icon {
    width: 100%;
    border-radius: 6px;
  }
}

@media (max-width: 480px) {
  .productos-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .producto-card {
    padding: 8px;
  }
  
  .producto-imagen {
    height: 80px;
  }
  
  .placeholder-imagen {
    font-size: 32px;
  }
  
  .producto-nombre {
    font-size: 12px;
  }
  
  .producto-precio {
    font-size: 13px;
  }
  
  .btn-lg {
    padding: 12px 20px;
    font-size: 15px;
  }
}
</style>
