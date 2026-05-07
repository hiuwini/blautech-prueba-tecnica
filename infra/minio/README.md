# MinIO

Inicialización local de MinIO como almacenamiento S3-compatible.

## Script disponible

- `create-bucket.sh`: configura el alias interno de MinIO, crea el bucket si no existe y mantiene acceso anónimo deshabilitado.

Bucket local esperado:

```txt
regulatory-documents
```

`docker-compose.yml` ejecuta este script desde el servicio `minio-init` después de que MinIO esté saludable.

En Compose, los contenedores usan el endpoint interno `http://minio:9000`. `http://localhost:9000` solo debe usarse desde la máquina host.

MinIO simula OCI Object Storage durante desarrollo local. Mantener compatibilidad S3-compatible cuando sea posible.
