# EMDECOB Consultas

Aplicación web para consultar procesos/casos legales y sus eventos.

## Configuración

### Variable de Entorno

Configura la URL base de la API creando un archivo `.env` en la raíz del proyecto:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Si no se configura, por defecto usa `http://localhost:8000`.

### Endpoints de la API

La aplicación espera los siguientes endpoints en tu backend FastAPI:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/cases/import-excel` | Importar casos desde Excel (multipart/form-data) |
| GET | `/cases?search=&juzgado=&page=1&page_size=20` | Listar casos con filtros |
| GET | `/cases/by-radicado/{radicado}` | Obtener caso por radicado |
| GET | `/cases/{id}/events` | Obtener eventos de un caso |

## Desarrollo

```bash
# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

## Rutas de la Aplicación

- `/importar` - Importar archivo Excel con casos
- `/consultar` - Buscar caso por radicado
- `/casos` - Lista de todos los casos con paginación
- `/casos/{radicado}` - Detalle de caso con timeline de eventos

## Tecnologías

- React + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- React Router
