# SOAP Gateway

Gateway REST que traduce solicitudes JSON hacia el Mock SOAP Server y persiste
resultados de compliance.

Tecnología: Python + Flask.

Puerto: `8001`.

## Endpoints

- `GET /health`.
- `POST /api/v1/compliance/check`.
- `GET /api/v1/compliance/status/{document_id}`.

## Contrato REST

Request principal:

```json
{
  "document_id": "11111111-1111-4111-8111-111111111111",
  "document_type": "financial_report"
}
```

Response exitoso:

```json
{
  "document_id": "11111111-1111-4111-8111-111111111111",
  "status": "COMPLIANT",
  "check_id": "22222222-2222-4222-8222-222222222222",
  "details": "Document is compliant",
  "checked_at": "2026-05-05T10:30:00Z"
}
```

SOAP Fault se convierte a error JSON controlado. Si el fault es de cliente
(`soapenv:Client`), el gateway responde HTTP `400`; otros faults se tratan como
error upstream HTTP `502`. Los faults se guardan como `FAILED` con `check_id`
generado localmente para mantener trazabilidad.

## Persistencia

PostgreSQL:

- Inserta en `compliance_checks`.
- Guarda `raw_request_xml` y `raw_response_xml`.
- Requiere que `document_id` exista en `documents` por la llave foránea del
  esquema actual.

MongoDB:

- Inserta eventos en `processing_events`.
- Usa estados `COMPLIANT`, `NON_COMPLIANT` o `FAILED`.

## Estructura Interna

```txt
app/
  __init__.py                         # application factory
  __main__.py                         # entrypoint Flask
  core/                               # config, errores, estados y tiempo
  api/
    health.py                         # GET /health
    v1/compliance/                    # blueprint /api/v1/compliance
  services/
    compliance_service.py             # REST -> SOAP -> persistencia
  soap/                               # builder, parser, faults, modelos y namespaces
  clients/
    mock_soap_client.py               # cliente HTTP hacia Mock SOAP Server
  repositories/                       # PostgreSQL y MongoDB
```

## Variables

Valores por defecto pensados para Docker Compose:

```txt
SOAP_GATEWAY_HOST=0.0.0.0
SOAP_GATEWAY_PORT=8001
MOCK_SOAP_BASE_URL=http://mock-soap-server:8090
MOCK_SOAP_TIMEOUT_SECONDS=5
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=regulatory_platform
POSTGRES_USER=regulatory_user
POSTGRES_PASSWORD=change_me_local_postgres_password
MONGO_URI=mongodb://mongo:27017/regulatory_audit
MONGO_DATABASE=regulatory_audit
```

Si se ejecuta directamente en la máquina host, usar
`MOCK_SOAP_BASE_URL=http://localhost:8090` y apuntar PostgreSQL/MongoDB según
corresponda.

## Docker

El Dockerfile usa Python 3.11 slim, instala `requirements.txt`, copia `app/` y arranca con:

```bash
python -m app
```

El servicio está registrado en `docker-compose.yml` como `soap-gateway`, publica el puerto `8001`, depende de PostgreSQL, MongoDB y Mock SOAP Server, y tiene healthcheck HTTP contra:

```http
GET /health
```

## Dependencias

- `Flask`: framework HTTP requerido por el componente.
- `defusedxml`: parser XML seguro para respuestas SOAP no confiables.
- `psycopg`: cliente PostgreSQL para `compliance_checks`.
- `pymongo`: cliente MongoDB para `processing_events`.
- `pytest`: pruebas automatizadas del servicio.

No se usa `requests`; el cliente SOAP usa `urllib` de la librería estándar para
mantener el alcance de dependencias acotado.

## Desarrollo local

Instalar dependencias en un entorno virtual local aprobado:

```bash
cd services/soap-gateway
python -m pip install -r requirements.txt
```

Ejecutar tests:

```bash
cd services/soap-gateway
python -m pytest
```

Ejecutar el servicio directamente contra servicios locales:

```bash
cd services/soap-gateway
SOAP_GATEWAY_HOST=0.0.0.0 \
SOAP_GATEWAY_PORT=8001 \
MOCK_SOAP_BASE_URL=http://localhost:8090 \
python -m app
```

Validar Compose desde la raíz:

```bash
docker compose config
```
