# Document Processing

Servicio principal de documentos regulatorios con Python + FastAPI.

Puerto objetivo: `8000`.

## Endpoints

```http
GET  /health
POST /api/v1/documents/upload
GET  /api/v1/documents?limit=20&offset=0
GET  /api/v1/documents/{document_id}
POST /api/v1/documents/{document_id}/process
GET  /api/v1/documents/{document_id}/download-url
```

## Responsabilidades Implementadas

- Recibe upload multipart con `file`, `document_type` y `user_id` opcional.
- Guarda el objeto en MinIO usando cliente S3-compatible.
- Persiste metadata en PostgreSQL `documents`.
- Registra `DOCUMENT_UPLOADED` en MongoDB `audit_logs`.
- Lista documentos con paginación por `limit` y `offset`.
- Devuelve detalle de documento y último compliance check cuando existe.
- Procesa documentos de forma síncrona contra SOAP Gateway.
- Actualiza estados `PROCESSING`, `COMPLIANT`, `NON_COMPLIANT` o `FAILED`.
- Registra eventos de procesamiento en MongoDB `processing_events`.
- Llama al webhook del BFF solo si `BFF_WEBHOOK_URL` está configurado.
- Genera URL presignada temporal para descarga desde MinIO.

## Estructura Interna

```txt
app/
  main.py                              # factory FastAPI y wiring de dependencias
  __main__.py                          # entrypoint uvicorn
  core/                                # config, errores, estados y tiempo
  api/                                 # health y routers /api/v1
  domain/
    documents/                         # modelos, validadores y caso de uso principal
    compliance/                        # modelos de compliance
  infrastructure/
    clients/                           # SOAP Gateway y BFF webhook
    mongo/                             # audit_logs y processing_events
    postgres/                          # documents + latest compliance
    storage/                           # MinIO object storage
```

## Variables Principales

```txt
DOCUMENT_PROCESSING_HOST=0.0.0.0
DOCUMENT_PROCESSING_PORT=8000
DOCUMENT_PROCESSING_CORS_ALLOWED_ORIGINS=http://localhost:3000
DOCUMENT_PROCESSING_PRESIGNED_URL_EXPIRY_SECONDS=900
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=regulatory_platform
POSTGRES_USER=regulatory_user
POSTGRES_PASSWORD=change_me_local_postgres_password
MONGO_URI=mongodb://mongo:27017/regulatory_audit
MONGO_DATABASE=regulatory_audit
MINIO_ENDPOINT=http://minio:9000
MINIO_PUBLIC_ENDPOINT=http://localhost:9000
MINIO_BUCKET=regulatory-documents
MINIO_ACCESS_KEY=local_minio_user
MINIO_SECRET_KEY=change_me_local_minio_password
MINIO_SECURE=false
MINIO_REGION=us-east-1
SOAP_GATEWAY_BASE_URL=http://soap-gateway:8001
SOAP_GATEWAY_TIMEOUT_SECONDS=5
BFF_WEBHOOK_URL=http://bff-notifications:4000/api/v1/webhooks/processing-complete
BFF_WEBHOOK_TIMEOUT_SECONDS=3
```

`MINIO_ENDPOINT` es el endpoint interno usado por el contenedor para subir objetos. `MINIO_PUBLIC_ENDPOINT` se usa solo para firmar URLs de descarga que abre el navegador; en Compose local debe apuntar a `http://localhost:9000`.

`BFF_WEBHOOK_URL` usa el nombre de servicio Docker para notificar al BFF implementado. Si este servicio se ejecuta directamente en la máquina host, usar:

```txt
http://localhost:4000/api/v1/webhooks/processing-complete
```

## Docker

El Dockerfile usa Python 3.11 slim, instala `requirements.txt`, copia `app/` y arranca con:

```bash
python -m app
```

El servicio está registrado en `docker-compose.yml` como `document-processing`, publica el puerto `8000`, depende de PostgreSQL, MongoDB, MinIO, `minio-init` y SOAP Gateway, y tiene healthcheck HTTP contra:

```http
GET /health
```

## Tests

Los tests mockean PostgreSQL, MongoDB, MinIO, SOAP Gateway y BFF.

```bash
cd services/document-processing
python -m pytest
```

En entornos donde `python` no exista, usar `python3 -m pytest`.
