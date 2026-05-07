# Plataforma Local de Documentos Regulatorios

Plataforma local para cargar, almacenar, procesar, auditar y consultar documentos regulatorios. El sistema simula una integración con un servicio gubernamental legacy SOAP, guarda los archivos en MinIO, persiste datos transaccionales en PostgreSQL, registra auditoría/eventos en MongoDB y notifica cambios de estado al frontend en tiempo real con Socket.IO.

El proyecto está pensado para ejecutarse completo con Docker Compose en ambiente local.

## Arquitectura

```txt
React Frontend (3000)
  -> FastAPI Document Processing (8000)
    -> MinIO (9000)
    -> PostgreSQL documents (5432)
    -> MongoDB audit_logs (27017)

React Frontend (3000)
  -> FastAPI Document Processing (8000)
    -> Flask SOAP Gateway (8001)
      -> Mock SOAP Server (8090)
      -> PostgreSQL compliance_checks (5432)
      -> MongoDB processing_events (27017)
    -> Express BFF webhook (4000)
      -> Socket.IO /notifications
        -> React Frontend
```

## Servicios


| Servicio            | Tecnología                      | Puerto host | Responsabilidad                                                       |
| ------------------- | ------------------------------- | ----------- | --------------------------------------------------------------------- |
| Frontend            | React + TypeScript + Vite/Nginx | 3000        | UI de carga, listado, detalle, procesamiento y notificaciones         |
| BFF Notifications   | Node.js + Express + Socket.IO   | 4000        | Dashboard, webhook y eventos en tiempo real                           |
| Document Processing | Python + FastAPI                | 8000        | Ciclo de vida del documento, MinIO, PostgreSQL, MongoDB e integración |
| SOAP Gateway        | Python + Flask                  | 8001        | Adaptador REST hacia SOAP y persistencia de compliance                |
| Mock SOAP Server    | Python estándar                 | 8090        | Simulación del sistema gubernamental legacy                           |
| PostgreSQL          | PostgreSQL 16                   | 5432        | `users`, `documents`, `compliance_checks`                             |
| MongoDB             | MongoDB 7                       | 27017       | `audit_logs`, `processing_events`                                     |
| MinIO API           | MinIO                           | 9000        | Object storage S3-compatible                                          |
| MinIO Console       | MinIO                           | 9001        | Consola web de almacenamiento                                         |


Nombres internos de servicio Docker:

```txt
postgres
mongo
minio
mock-soap-server
soap-gateway
document-processing
bff-notifications
frontend
```

Entre contenedores se usan esos nombres. `localhost` solo aplica desde la máquina host o desde el navegador.

## Requisitos

- Docker y Docker Compose v2.
- Node.js 20+ solo si quieres correr BFF/frontend fuera de Docker.
- Python 3.11+ solo si quieres correr tests o servicios Python fuera de Docker.
- `rg` recomendado para inspección local del repo.

## Levantar Desde Cero

1. Crear el archivo de entorno local:

```bash
cp .env.example .env
```

1. Validar la configuración de Compose:

```bash
docker compose config
```

1. Construir y levantar todo el stack:

```bash
docker compose up -d --build
```

1. Revisar estado de contenedores:

```bash
docker compose ps
```

Los servicios de aplicación deben quedar `healthy`. `minio-init` es un contenedor one-shot: debe terminar correctamente tras crear/verificar el bucket.

1. Abrir la aplicación:

```txt
http://localhost:3000
```

URLs útiles:

```txt
Frontend:             http://localhost:3000
FastAPI Docs:         http://localhost:8000/docs
BFF Health:           http://localhost:4000/health
SOAP Gateway Health:  http://localhost:8001/health
Mock SOAP Health:     http://localhost:8090/health
MinIO API:            http://localhost:9000
MinIO Console:        http://localhost:9001
```

Credenciales locales de MinIO por defecto:

```txt
Usuario:  local_minio_user
Password: change_me_local_minio_password
Bucket:   regulatory-documents
```

## Levantar Solo Infraestructura

Útil para correr servicios manualmente en el host:

```bash
docker compose up -d postgres mongo minio minio-init
```

## Desarrollo Con Frontend HMR

Si quieres iterar la UI con hot reload, levanta backend e infraestructura con Compose y corre Vite localmente:

```bash
docker compose up -d \
  postgres mongo minio minio-init \
  mock-soap-server soap-gateway document-processing bff-notifications

cd apps/frontend
npm ci
npm run dev
```

Abrir:

```txt
http://localhost:3000
```

Las variables `VITE_*` se evalúan al construir o arrancar Vite y deben apuntar a URLs accesibles desde el navegador:

```txt
VITE_DOCUMENT_PROCESSING_BASE_URL=http://localhost:8000
VITE_BFF_BASE_URL=http://localhost:4000
VITE_SOCKET_IO_NAMESPACE=/notifications
```

## Variables Importantes

El archivo `.env.example` contiene valores locales seguros para desarrollo. Las credenciales son placeholders y no deben reemplazarse por secretos reales en el repo.

Variables clave para comunicación interna:

```txt
FASTAPI_BASE_URL=http://document-processing:8000
SOAP_GATEWAY_BASE_URL=http://soap-gateway:8001
MOCK_SOAP_BASE_URL=http://mock-soap-server:8090
BFF_WEBHOOK_URL=http://bff-notifications:4000/api/v1/webhooks/processing-complete
MONGO_URI=mongodb://mongo:27017/regulatory_audit
MINIO_ENDPOINT=http://minio:9000
```

Variables clave para navegador/host:

```txt
FRONTEND_BASE_URL=http://localhost:3000
VITE_DOCUMENT_PROCESSING_BASE_URL=http://localhost:8000
VITE_BFF_BASE_URL=http://localhost:4000
MINIO_PUBLIC_ENDPOINT=http://localhost:9000
```

`MINIO_ENDPOINT` es interno para que `document-processing` suba archivos desde Docker. `MINIO_PUBLIC_ENDPOINT` se usa para firmar URLs de descarga que el navegador puede abrir.

## Flujo Funcional

Estados permitidos de documento:

```txt
UPLOADED
PROCESSING
COMPLIANT
NON_COMPLIANT
FAILED
```

Flujo de carga:

```txt
Usuario -> Frontend -> FastAPI upload
  -> MinIO object
  -> PostgreSQL documents
  -> MongoDB audit_logs
```

Flujo de procesamiento:

```txt
Usuario -> Frontend -> FastAPI process
  -> SOAP Gateway REST
  -> Mock SOAP Server
  -> PostgreSQL compliance_checks
  -> MongoDB processing_events
  -> FastAPI actualiza documents.status
  -> BFF webhook
  -> Socket.IO document-status-changed
  -> Frontend actualiza UI
```

Reglas del Mock SOAP:


| `document_type`         | Resultado                      |
| ----------------------- | ------------------------------ |
| `financial_report`      | `COMPLIANT`                    |
| `tax_filing`            | `NON_COMPLIANT`                |
| `regulatory_disclosure` | `COMPLIANT`                    |
| Cualquier otro valor    | SOAP Fault, documento `FAILED` |


## Prueba Manual Rápida

Con el stack levantado:

1. Subir documento:

```bash
curl -s \
  -F "document_type=financial_report" \
  -F "file=@README.md;type=text/markdown" \
  http://localhost:8000/api/v1/documents/upload
```

Guarda el `document_id` de la respuesta.

1. Procesar documento:

```bash
curl -s -X POST http://localhost:8000/api/v1/documents/<document_id>/process
```

Para `financial_report`, el documento debe terminar en `COMPLIANT`.

1. Obtener URL de descarga:

```bash
curl -s http://localhost:8000/api/v1/documents/<document_id>/download-url
```

La URL devuelta debe empezar con:

```txt
http://localhost:9000/regulatory-documents/...
```

1. Validar notificaciones desde el frontend:

Abrir `http://localhost:3000`, confirmar que el indicador diga `Socket activo`, subir/procesar un documento y revisar el panel `Notificaciones`.

Para probar solo el webhook del BFF:

```bash
curl -i -X POST http://localhost:4000/api/v1/webhooks/processing-complete \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "11111111-1111-4111-8111-111111111111",
    "status": "COMPLIANT",
    "document_type": "financial_report",
    "checked_at": "2026-05-07T10:30:00Z"
  }'
```

Respuesta esperada:

```json
{
  "status": "accepted",
  "event": "document-status-changed",
  "document_id": "11111111-1111-4111-8111-111111111111"
}
```

## Smoke E2E Automatizado

Con el stack levantado, puedes ejecutar un flujo HTTP completo:

```bash
python3 scripts/smoke_e2e.py
python3 scripts/smoke_e2e.py --document-type tax_filing
python3 scripts/smoke_e2e.py --document-type annual_statement
```

Resultados esperados:


| Comando                    | Estado esperado                    |
| -------------------------- | ---------------------------------- |
| `financial_report` default | `COMPLIANT`                        |
| `tax_filing`               | `NON_COMPLIANT`                    |
| `annual_statement`         | `FAILED` por SOAP Fault controlado |


## Healthchecks

```bash
curl -s http://localhost:8090/health
curl -s http://localhost:8001/health
curl -s http://localhost:8000/health
curl -s http://localhost:4000/health
curl -s http://localhost:3000/health
```

Backends responden JSON:

```json
{"status":"ok","service":"<service-name>"}
```

El frontend responde texto plano:

```txt
ok
```

## Endpoints Principales

Document Processing:

```http
GET  /health
POST /api/v1/documents/upload
GET  /api/v1/documents?limit=20&offset=0
GET  /api/v1/documents/{document_id}
POST /api/v1/documents/{document_id}/process
GET  /api/v1/documents/{document_id}/download-url
```

SOAP Gateway:

```http
GET  /health
POST /api/v1/compliance/check
GET  /api/v1/compliance/status/{document_id}
```

BFF Notifications:

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

Mock SOAP Server:

```http
GET  /health
POST /soap/compliance
```

## Base de Datos y Storage

PostgreSQL inicializa el esquema desde:

```txt
infra/postgres/init/001_schema.sql
```

MongoDB inicializa colecciones e índices desde:

```txt
infra/mongo/init/001_collections.js
```

MinIO crea/verifica el bucket desde:

```txt
infra/minio/create-bucket.sh
```

Los scripts de `init/` se ejecutan automáticamente solo cuando los volúmenes están vacíos. Para bases ya existentes, usar las copias de `migrations/` de forma manual y con cuidado:

```txt
infra/postgres/migrations/001_init_schema.sql
infra/mongo/migrations/001_init_collections.js
```

Comandos útiles de inspección:

```bash
docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select id, document_type, status, created_at from documents order by created_at desc limit 5;"'

docker compose exec -T mongo sh -lc 'mongosh "$MONGO_INITDB_DATABASE" --quiet --eval "db.audit_logs.find().sort({created_at:-1}).limit(5).toArray()"'

docker compose run --rm --entrypoint /bin/sh minio-init -lc 'mc alias set local "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null && mc ls "local/$MINIO_BUCKET/documents/"'
```

## Tests

Mock SOAP Server:

```bash
cd services/mock-soap-server
python3 -m unittest discover -s tests
```

SOAP Gateway:

```bash
cd services/soap-gateway
python -m pip install -r requirements.txt
python -m pytest
```

Document Processing:

```bash
cd services/document-processing
python -m pip install -r requirements.txt
python -m pytest
```

BFF Notifications:

```bash
cd services/bff-notifications
npm install
npm run lint --if-present
npm test --if-present
npm run build --if-present
```

Frontend:

```bash
cd apps/frontend
npm ci
npm run lint --if-present
npm test --if-present
npm run build --if-present
```

Validación general:

```bash
docker compose config
```

## CI

El workflow de GitHub Actions está en:

```txt
.github/workflows/ci.yml
```

Se ejecuta en `push`, `pull_request` y `workflow_dispatch`. Valida Compose y corre lint/tests/build por servicio cuando existe su manifest principal.

## Estructura Del Repo

```txt
apps/frontend/                         React + TypeScript
services/bff-notifications/            Express + Socket.IO
services/document-processing/          FastAPI
services/soap-gateway/                 Flask REST -> SOAP
services/mock-soap-server/             SOAP legacy simulado
infra/postgres/                        SQL de PostgreSQL
infra/mongo/                           init/migrations MongoDB
infra/minio/                           bucket MinIO
docs/                                  planificación y pruebas manuales
scripts/                               utilidades, smoke E2E
.github/workflows/                     CI
```

## Troubleshooting


| Síntoma                                                       | Causa probable                                   | Acción                                                                                      |
| ------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `docker compose config` falla                                 | `.env` incompleto o YAML inválido                | Copiar de nuevo `.env.example` y revisar cambios locales                                    |
| Un contenedor usa `localhost` para hablar con otro contenedor | URL interna mal configurada                      | Usar nombres Docker: `postgres`, `mongo`, `minio`, `soap-gateway`, etc.                     |
| URL de descarga apunta a `http://minio:9000`                  | Imagen vieja o falta `MINIO_PUBLIC_ENDPOINT`     | Reconstruir `document-processing` y confirmar `MINIO_PUBLIC_ENDPOINT=http://localhost:9000` |
| MinIO responde `NoSuchBucket`                                 | `minio-init` no corrió o falló                   | Ejecutar `docker compose up -d minio minio-init` y revisar logs                             |
| PostgreSQL no tiene tablas                                    | Volumen creado antes de montar init scripts      | Aplicar migración manual o recrear volúmenes solo si no hay datos importantes               |
| MongoDB no muestra colecciones                                | Volumen reutilizado sin init                     | Aplicar migración manual o recrear volúmenes solo si no hay datos importantes               |
| Frontend no recibe notificaciones                             | Socket desconectado, CORS o namespace incorrecto | Confirmar `Socket activo`, `VITE_SOCKET_IO_NAMESPACE=/notifications` y BFF healthy          |
| Dashboard falla                                               | BFF no puede consultar FastAPI                   | Revisar `FASTAPI_BASE_URL=http://document-processing:8000` en Compose                       |


Para reconstruir un servicio específico:

```bash
docker compose up -d --no-deps --build document-processing
```

Para ver logs:

```bash
docker compose logs -f document-processing
docker compose logs -f bff-notifications
docker compose logs -f soap-gateway
```

