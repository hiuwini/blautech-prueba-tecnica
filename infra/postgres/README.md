# PostgreSQL

Scripts reproducibles para el esquema transaccional mínimo de PostgreSQL.

## Estrategia

- Usar SQL plano versionado en `infra/postgres/migrations/`.
- Mantener `infra/postgres/init/001_schema.sql` alineado con la migración inicial porque `docker-compose.yml` lo monta en `/docker-entrypoint-initdb.d`.
- No agregar Alembic todavía: no existe servicio Python/ORM que lo consuma y el MVP solo requiere una base inicial local reproducible.
- Docker ejecuta los scripts de `init/` automáticamente solo cuando el volumen `postgres_data` está vacío; la aplicación manual queda para volúmenes existentes.
- Mantener ids principales como `UUID`.
- Usar `TIMESTAMPTZ` para timestamps; las APIs deberán serializar en ISO 8601 UTC.

## Migraciones

```txt
infra/postgres/init/001_schema.sql
infra/postgres/migrations/001_init_schema.sql
```

La migración inicial crea:

- `users`
- `documents`
- `compliance_checks`

También crea índices para consultas por estado, fecha de creación, usuario, documento y `check_id`.

## Aplicación Local

Primero levantar PostgreSQL:

```bash
docker compose up -d postgres
```

Si el volumen `postgres_data` está vacío, Docker ejecuta `infra/postgres/init/001_schema.sql` al crear el contenedor. Para una base local existente, aplicar manualmente la migración versionada:

```bash
docker compose exec -T postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' < infra/postgres/migrations/001_init_schema.sql
```

No ejecutar migraciones contra una base real o con datos importantes sin aprobación explícita.

## Validación

```bash
docker compose config
```

La validación completa de sintaxis SQL requiere ejecutarla con `psql`; no se debe hacer contra una base real sin aprobación.
