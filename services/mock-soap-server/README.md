# Mock SOAP Server

Servicio local que simula el sistema gubernamental legacy de compliance.

Puerto: `8090`.

## Implementación

Implementado con Python estándar:

- `http.server` para HTTP.
- `xml.etree.ElementTree` para parsear y generar XML SOAP.
- `uuid` para `CheckId`.
- `datetime` para `CheckedAt` ISO 8601 UTC.
- `unittest` para pruebas.

No instala dependencias externas. Esta decisión mantiene el mock autocontenido y suficiente para el MVP, donde no se requiere framework web ni persistencia.

## Estructura Interna

```txt
app/
  __main__.py             # entrypoint runtime
  config.py               # host, puerto y límites HTTP
  http/
    handler.py            # BaseHTTPRequestHandler y endpoints
    server.py             # factory ThreadingHTTPServer
  soap/
    builder.py            # response SOAP y SOAP Fault
    faults.py             # excepciones SOAP
    models.py             # dataclasses del contrato
    namespaces.py         # namespaces XML
    parser.py             # request SOAP -> modelo
    rules.py              # reglas MVP por DocumentType
```

## Endpoints

- `GET /health`.
- `POST /soap/compliance`.

## Reglas MVP

| DocumentType | Resultado |
|---|---|
| `financial_report` | `COMPLIANT` |
| `tax_filing` | `NON_COMPLIANT` |
| `regulatory_disclosure` | `COMPLIANT` |
| Cualquier otro valor | SOAP Fault |

## Contrato SOAP

Namespace SOAP:

```txt
http://schemas.xmlsoap.org/soap/envelope/
```

Namespace compliance:

```txt
http://gov.example/regulatory/compliance
```

Request esperado:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
  xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:com="http://gov.example/regulatory/compliance">
  <soapenv:Header />
  <soapenv:Body>
    <com:ComplianceCheckRequest>
      <com:DocumentId>11111111-1111-4111-8111-111111111111</com:DocumentId>
      <com:DocumentType>financial_report</com:DocumentType>
    </com:ComplianceCheckRequest>
  </soapenv:Body>
</soapenv:Envelope>
```

Response exitoso:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:com="http://gov.example/regulatory/compliance" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <com:ComplianceCheckResponse>
      <com:DocumentId>11111111-1111-4111-8111-111111111111</com:DocumentId>
      <com:DocumentType>financial_report</com:DocumentType>
      <com:Status>COMPLIANT</com:Status>
      <com:CheckId>uuid</com:CheckId>
      <com:CheckedAt>2026-05-05T10:30:00Z</com:CheckedAt>
      <com:Details>Document is compliant</com:Details>
    </com:ComplianceCheckResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

SOAP Fault:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <soapenv:Fault>
      <faultcode>soapenv:Client</faultcode>
      <faultstring>Unsupported DocumentType: annual_statement</faultstring>
    </soapenv:Fault>
  </soapenv:Body>
</soapenv:Envelope>
```

## Desarrollo local

Ejecutar tests:

```bash
cd services/mock-soap-server
python3 -m unittest discover -s tests
```

Ejecutar el servicio localmente:

```bash
cd services/mock-soap-server
MOCK_SOAP_HOST=0.0.0.0 MOCK_SOAP_PORT=8090 python3 -m app
```

Validar Compose:

```bash
docker compose config
```

El Dockerfile copia `app/` y arranca con `python -m app`. El servicio está registrado en `docker-compose.yml` como `mock-soap-server`, publica el puerto `8090` y tiene healthcheck HTTP contra `/health`.

## Fixtures

Los fixtures XML usados por tests están en:

```txt
services/mock-soap-server/tests/fixtures/
```
