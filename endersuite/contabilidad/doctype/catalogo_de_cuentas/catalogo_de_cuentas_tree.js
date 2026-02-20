// Configuración de vista de árbol para `Catalogo de Cuentas` (en español)
// Esta configuración usa el método whitelisted `get_children` definido en el
// controlador Python para obtener nodos y muestra filtros/etiquetas en español.

frappe.treeview_settings['Catalogo de Cuentas'] = {
    breadcrumb: 'Contabilidad',
    title: 'Catálogo de Cuentas',
    // filtros de ejemplo (modifica según campos reales en el Doctype)
    filters: [
        // Ejemplo: filtrar por compañía si existiera el campo
        // {
        //     fieldname: 'company',
        //     fieldtype: 'Select',
        //     options: 'Compañía 1\nCompañía 2',
        //     label: 'Compañía',
        //     on_change: function() { /* handle_company_change() */ }
        // }
    ],
    get_tree_nodes: 'endersuite.contabilidad.doctype.catalogo_de_cuentas.catalogo_de_cuentas.get_children',
    add_tree_node: 'frappe.desk.treeview.add_node',
    // campos del formulario para crear un nuevo nodo (personaliza si hace falta)
    fields: [
        { fieldtype: 'Data', fieldname: 'cuenta', label: 'Nombre de la cuenta', reqd: true, description: 'Ej.: Caja, Bancos, Ventas' },
        { fieldtype: 'Check', fieldname: 'is_group', label: '¿Es un grupo (carpeta)?', default: 0, description: 'Marque si la cuenta tendrá subcuentas' }
    ],
    ignore_fields: ['parent_catalogo_de_cuentas'],
    // Personalizaciones del UI
    onload: function(treeview) {
        // Ejecutado cuando se instancia la vista de árbol
    },
    post_render: function(treeview) {
        // Ejecutado después de renderizar el árbol
    },
    onrender: function(node) {
        // Ejecutado para cada nodo cuando se instancia
    },
    on_get_node: function(nodes) {
        // Ejecutado cuando `get_tree_nodes` devuelve nodos
    },
    extend_toolbar: true,
    toolbar: [
        {
            label: 'Añadir subcuenta',
            condition: function(node) { return node.expandable; },
            click: function(node) { /* abrir diálogo para añadir hijo */ },
            btnClass: 'hidden-xs'
        }
    ]
};
