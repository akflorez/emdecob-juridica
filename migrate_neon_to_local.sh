#!/bin/bash

# Configuration (These values should match your .env or be set as environment variables)
# If running on your server, ensure you have Docker installed and the containers are running.

NEON_URL="postgresql://neondb_owner:npg_eWCA1gPd0ryo@ep-icy-thunder-akkkr42v.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require"
TARGET_DB_USER="emdecob"
TARGET_DB_NAME="emdecob_consultas"
CONTAINER_NAME="emdecob-db"

echo "🐘 Iniciando migración de datos desde Neon a Coolify..."

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Error: El contenedor $CONTAINER_NAME no está corriendo. Por favor asegúrate de haber desplegado los cambios en Coolify antes de ejecutar este script."
    exit 1
fi

echo "📦 Extrayendo datos de Neon e importando al contenedor local..."

# Perform the dump and restore in a single pipe
# Using -c (clean) to drop existing data in target before importing
docker exec -i "$CONTAINER_NAME" pg_dump "$NEON_URL" \
    --clean --if-exists --no-owner --no-privileges \
    | docker exec -i "$CONTAINER_NAME" psql -U "$TARGET_DB_USER" -d "$TARGET_DB_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Migración completada con éxito!"
    echo "🔍 Ahora puedes actualizar las variables de entorno en Coolify para usar el nuevo DATABASE_URL."
else
    echo "❌ Error durante la migración. Por favor revisa los logs."
    exit 1
fi
