#!/bin/sh
mc alias set myminio http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
mc mb myminio/edu-data || true
