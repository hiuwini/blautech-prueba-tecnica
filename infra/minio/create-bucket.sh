#!/bin/sh
set -eu

MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
MINIO_BUCKET="${MINIO_BUCKET:-regulatory-documents}"

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"

mc alias set local "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"
mc mb --ignore-existing "local/${MINIO_BUCKET}"
mc anonymous set none "local/${MINIO_BUCKET}"
mc ls "local/${MINIO_BUCKET}" >/dev/null
