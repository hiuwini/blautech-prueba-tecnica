# BFF Notifications

Servicio Node.js + Express + Socket.IO para dashboard, webhooks y notificaciones en tiempo real.

Puerto objetivo: `4000`.

## Endpoints

```http
GET  /health
GET  /api/v1/dashboard/summary
POST /api/v1/webhooks/processing-complete
```

Socket.IO:

```txt
namespace: /notifications
event: document-status-changed
```

## Estructura Interna

```txt
src/
  server.js                         # entrypoint runtime
  index.js                          # exports publicos para tests/helpers
  app/                              # factories de Express + HTTP server
  api/                              # routers versionados
  controllers/                      # traduccion HTTP -> servicios
  services/                         # dashboard y notificaciones
  clients/                          # cliente de Document Processing
  sockets/                          # namespace Socket.IO /notifications
  middleware/                       # CORS, 404 y errores
  contracts/                        # estados y validacion de payloads
  config/                           # variables de entorno
```

## Webhook

`POST /api/v1/webhooks/processing-complete` recibe el webhook de FastAPI al finalizar el procesamiento.

Payload requerido:

```json
{
  "document_id": "11111111-1111-4111-8111-111111111111",
  "status": "COMPLIANT",
  "document_type": "financial_report",
  "checked_at": "2026-05-05T10:30:00Z"
}
```

`status` debe ser un estado final: `COMPLIANT`, `NON_COMPLIANT` o `FAILED`.
El webhook acepta campos extra enviados por FastAPI, como `check_id` y `details`, pero el evento emitido conserva el contrato documentado de cambio de estado.

Respuesta exitosa:

```json
{
  "status": "accepted",
  "event": "document-status-changed",
  "document_id": "11111111-1111-4111-8111-111111111111"
}
```

## Dashboard Summary

`GET /api/v1/dashboard/summary` consume `GET /api/v1/documents` desde FastAPI usando `FASTAPI_BASE_URL` y agrega:

- `total_documents`.
- `aggregated_documents`.
- `is_complete`.
- `by_status`.
- `by_document_type`.
- `recent_documents`.

El BFF pagina hasta `BFF_DASHBOARD_MAX_DOCUMENTS` para evitar requests sin límite. Si existen más documentos que el máximo, `is_complete` será `false`.

## Variables

```txt
BFF_HOST=0.0.0.0
BFF_PORT=4000
FRONTEND_BASE_URL=http://localhost:3000
BFF_CORS_ALLOWED_ORIGINS=
FASTAPI_BASE_URL=http://document-processing:8000
BFF_FASTAPI_TIMEOUT_SECONDS=3
BFF_DASHBOARD_PAGE_SIZE=100
BFF_DASHBOARD_MAX_DOCUMENTS=500
SOCKET_IO_NAMESPACE=/notifications
```

`FRONTEND_BASE_URL` controla CORS HTTP y Socket.IO cuando `BFF_CORS_ALLOWED_ORIGINS` está vacío. Usar `BFF_CORS_ALLOWED_ORIGINS` solo cuando se necesite una lista separada por comas. Para ejecución en Docker, las URLs service-to-service deben usar nombres de servicio.

## Docker

El Dockerfile usa Node.js 20 Alpine, copia `package*.json` y `src/`, instala dependencias de producción y arranca con `npm start`.

El servicio está registrado en `docker-compose.yml` como `bff-notifications`, publica el puerto `4000` y tiene healthcheck HTTP contra:

```http
GET /health
```

## Desarrollo

Dependencias justificadas:

- `express`: servidor HTTP y rutas REST.
- `socket.io`: notificaciones en tiempo real.
- `socket.io-client`: prueba de emisión real en el namespace `/notifications`.

Comandos:

```bash
npm run lint --if-present
npm test --if-present
npm run build --if-present
```

Nota local: si Node.js/npm no están instalados, ejecutar estos comandos en un entorno con Node.js 20+ o dentro de Docker.
