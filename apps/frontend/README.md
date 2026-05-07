# Frontend

SPA operativa para el flujo principal de documentos regulatorios.

Tecnología: Vite + React + TypeScript.

Puerto objetivo: `3000`.

Responsabilidades:

- Upload de documentos.
- Lista de documentos.
- Detalle de documento.
- Acción de procesamiento.
- Dashboard summary básico desde el BFF.
- Recepción de notificaciones Socket.IO desde `/notifications`.

## Estructura Interna

```txt
src/
  App.test.tsx                    # tests de integración de UI
  app/                            # composición principal, bootstrap y estilos globales
  config/                         # lectura de variables Vite
  features/
    documents/                    # upload, listado, detalle, proceso y descarga
    dashboard/                    # summary y gráfico de estados
    notifications/                # Socket.IO y panel de eventos
  shared/                         # cliente HTTP, UI reusable y utilidades
  test/                           # setup de Vitest/Testing Library
```

## Variables

```txt
VITE_DOCUMENT_PROCESSING_BASE_URL=http://localhost:8000
VITE_BFF_BASE_URL=http://localhost:4000
VITE_SOCKET_IO_NAMESPACE=/notifications
```

Estas variables son de navegador y Vite las evalúa al arrancar o construir la app.

## Comandos

```bash
npm install
npm run dev
npm run lint --if-present
npm test --if-present
npm run build --if-present
```

`npm run dev` sirve la aplicación en `http://localhost:3000`.

## Contratos Consumidos

FastAPI Document Processing:

```http
POST /api/v1/documents/upload
GET  /api/v1/documents
GET  /api/v1/documents/{document_id}
POST /api/v1/documents/{document_id}/process
GET  /api/v1/documents/{document_id}/download-url
```

BFF Notifications:

```http
GET /api/v1/dashboard/summary
```

Socket.IO:

```txt
namespace: /notifications
event: document-status-changed
```

## Docker

El Dockerfile construye assets estáticos y los sirve con Nginx en el puerto `3000`.

El servicio está registrado en `docker-compose.yml` como `frontend`. Compose pasa las variables `VITE_*` como build args, por lo que deben apuntar a URLs accesibles desde el navegador y requieren rebuild si cambian.

Healthcheck:

```http
GET /health
```

Para desarrollo iterativo con HMR se puede levantar el backend con Compose y ejecutar `npm run dev` localmente.
