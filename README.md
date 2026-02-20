# EnderSuite
> All the right were assigned to Quelopande the February 19, 2026 by RenderCores.
> Un ERP moderno e integral para MiPyMEs, construido sobre la robusta plataforma Frappe.

EnderSuite es una solución de software SaaS diseñada para centralizar y optimizar las operaciones de las MiPyMEs. A diferencia de otras herramientas, EnderSuite se enfoca en la facilidad de uso y total integracion a cada uno de los giros de nuestros clientes.

## 🛠️ Stack Tecnológico y Arquitectura

EnderSuite está construido 100% sobre el **Frappe Framework**.

Esto significa que toda la lógica de negocio, la interfaz de usuario (frontend y backend) y la API están gestionadas de forma nativa dentro de esta plataforma.

Las tecnologías clave subyacentes que utiliza Frappe (y por lo tanto EnderSuite) incluyen:

* **Backend**: Python
* **Base de Datos**: MariaDB (principalmente) / PostgreSQL
* **Frontend**: Frappe UI (JavaScript, HTML, CSS/SCSS)
* **APIs**: REST API nativa y autogenerada por Frappe
* **Gestión de Tareas/Caché**: Redis
* **Entorno de Ejecución JS**: Node.js (utilizado para la construcción de assets y scripts del framework)

### Despliegue

El despliegue y la gestión de la infraestructura de EnderSuite se realizan a través de **EnderDeploy**, nuestra plataforma interna diseñada para optimizar la entrega y el rendimiento de aplicaciones Frappe.

## 🔧 Modo de Uso

Una vez que tengas acceso a tu instancia de EnderSuite:

* **URL de Acceso**: `[la-url-de-tu-instancia.com]`
* **Credenciales**: Estas son enviadas al correo

## 🤝 Contribuciones

Actualmente, el desarrollo de EnderSuite se maneja de forma interna. Si estás interesado en colaborar o reportar un error, por favor contacta a hola@rendercores.online.

> ¡Las contribuciones son bienvenidas! Si deseas contribuir a EnderSuite, por favor:
> 1.  Haz un "Fork" del proyecto.
> 2.  Crea una nueva rama para tu feature (`git checkout -b feature/NuevaCaracteristica`).
> 3.  Haz "Commit" de tus cambios y haz "Push".
> 4.  Abre un "Pull Request" para revisión.

## 📄 Licencia

Este proyecto está bajo la licencia GNU AFFERO GENERAL PUBLIC LICENSE. Mira el archivo `LICENSE` para más detalles.

## 📞 Contacto
## 📚 Guías de desarrollo (módulos clave)

- Contabilidad → Catálogo de Cuentas (vista en árbol):
	- Documentación para desarrolladores y decisiones de diseño en:
		`endersuite/contabilidad/doctype/catalogo_de_cuentas/README.es.md`
	- Incluye estructura por defecto (raíces protegidas y subgrupos), reglas de protección,
		naming por campo `cuenta`, configuración del tree view, hook `after_install`,
		traducciones y pruebas.


**RenderCores** (Desarrolladores de EnderSuite)

* **Web**: www.rendercores.com
* **Email**: hola@rendercores.online
