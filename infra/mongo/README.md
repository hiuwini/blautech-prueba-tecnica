# MongoDB

Scripts reproducibles para auditoría y eventos de procesamiento en MongoDB.

## Estrategia

- Usar JavaScript de `mongosh` versionado en `infra/mongo/migrations/`.
- Mantener `infra/mongo/init/001_collections.js` alineado con la migración inicial porque `docker-compose.yml` lo monta en `/docker-entrypoint-initdb.d`.
- Docker ejecuta los scripts de `init/` automáticamente solo cuando el volumen `mongo_data` está vacío; la aplicación manual queda para volúmenes existentes.
- Guardar UUIDs como strings para interoperar de forma simple con Python, Node.js y PostgreSQL.
- Guardar timestamps como BSON `Date`; las APIs deberán exponerlos en ISO 8601 UTC.

MongoDB se usa para trazabilidad y eventos, no como fuente primaria de metadata transaccional.

## Migraciones

```txt
infra/mongo/init/001_collections.js
infra/mongo/migrations/001_init_collections.js
```

La migración inicial crea o actualiza:

- `audit_logs`
- `processing_events`

También crea índices para búsquedas por entidad, acción, documento, estado y fecha de creación.

## Aplicación Local

Primero levantar MongoDB:

```bash
docker compose up -d mongo
```

Si el volumen `mongo_data` está vacío, Docker ejecuta `infra/mongo/init/001_collections.js` al crear el contenedor. Para una base local existente, aplicar manualmente la migración versionada:

```bash
docker compose exec -T mongo sh -lc 'mongosh "$MONGO_INITDB_DATABASE"' < infra/mongo/migrations/001_init_collections.js
```

No ejecutar scripts contra una base real o con datos importantes sin aprobación explícita.

## Validación

```bash
docker compose config
```

Si `node` está disponible localmente, se puede validar la sintaxis JavaScript sin conectar a MongoDB:

```bash
node --check infra/mongo/migrations/001_init_collections.js
```
