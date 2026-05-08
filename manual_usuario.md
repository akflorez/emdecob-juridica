# ⚖️ Manual de Usuario - EMDECOB Judicial Expert
**Versión 1.0 | Master Workflow Engine**

Este manual describe el funcionamiento de la plataforma EMDECOB para la gestión de procesos judiciales y control de tareas operativas.

---

## 1. Acceso al Sistema
Para ingresar, utilice sus credenciales autorizadas en la pantalla de inicio.
*   **Usuario:** Su identificador asignado.
*   **Contraseña:** Proporcionada por el administrador.
> [!TIP]
> El sistema cuenta con modo oscuro y claro. Puede cambiarlo en el interruptor de la parte inferior izquierda para su comodidad visual.

---

## 2. Gestión Judicial (Consola Principal)
El núcleo del sistema es el monitoreo automático de procesos ante la Rama Judicial.

### 🔍 Consulta de Casos
*   **Por Radicado:** Ingrese los 23 dígitos del proceso para obtener el historial completo de actuaciones.
*   **Por Nombre:** Busque procesos vinculados a un nombre o razón social específica.
*   **Alertas de Actuaciones:** El sistema marca en **ROJO** o con una etiqueta de "No Leído" aquellos casos que han tenido movimientos recientes en las últimas 24 horas.

### 📂 Importación de Datos
Utilice la opción **"Importar Excel"** para cargar masivamente nuevos procesos al sistema. El formato debe contener la columna `RADICADO`.

---

## 3. Gestión de Proyectos (Mis Proyectos)
Inspirado en metodologías ágiles (ClickUp), este módulo permite organizar la carga laboral del bufete.

### 🏗️ Jerarquía de Organización
1.  **Espacios (Workspaces):** Grandes áreas (Ej: Derecho Civil, Laboral).
2.  **Carpetas:** Agrupadores de proyectos.
3.  **Listas:** Listado específico de tareas (Ej: "Audiencias Mayo").

### 📋 El Tablero Kanban (Board)
Visualice sus tareas en columnas según su estado:
*   **ABIERTO:** Tareas recién creadas.
*   **EN PROCESO:** Tareas en ejecución.
*   **COMPLETADO:** Tareas finalizadas.
> [!NOTE]
> Puede arrastrar y soltar tareas (si está habilitado) o cambiar el estado directamente desde el detalle de la tarea.

---

## 4. Control de Tareas y Subtareas
Haga clic en cualquier tarea para abrir el **TaskDrawer (Panel de Detalle)**.

*   **Asignación:** Seleccione al abogado responsable. El sistema mostrará su nombre completo.
*   **Fechas de Vencimiento:** El sistema le avisará si una tarea está vencida o por vencer.
*   **Subtareas:** Desglose una tarea compleja en pasos más pequeños. Puede marcarlas como completadas directamente en el listado.
*   **Etiquetas (Tags):** Clasifique tareas por prioridad o tipo (Ej: "Urgente", "Cédula 468"). Puede crear etiquetas nuevas escribiendo el nombre y presionando Enter.

---

## 5. Agenda y Calendario
La vista de **"Agenda / Calendario"** es interactiva.
*   **Visualización:** Vea todas las tareas con fecha de vencimiento en un formato mensual o semanal.
*   **Creación Rápida:** Haga clic en cualquier día del calendario para abrir el formulario de "Nueva Tarea". La fecha se seleccionará automáticamente.

---

## 6. Panel Administrativo (Solo Administradores)
Acceda a `URL_DEL_SISTEMA/admin` para gestionar el núcleo de la plataforma:
*   **Usuarios:** Crear, editar o desactivar cuentas de abogados.
*   **Auditoría:** Revisar todos los radicados y tareas del sistema de forma global.
*   **Integraciones:** Configurar conexiones externas (Cally, ClickUp, etc.).

---

## 🆘 Soporte Técnico
Si encuentra algún error o requiere una función adicional, contacte al equipo de soporte de EMDECOB mencionando su **ID de Usuario** y una captura de pantalla del problema.
