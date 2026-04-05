#!/bin/bash

# Configuration
PROJECT_NAME="emdecob-consultas"

echo "🚀 Iniciando despliegue de $PROJECT_NAME..."

# Ensure .env exists
if [ ! -f .env ]; then
    echo "❌ Error: Archivo .env no encontrado. Por favor créalo con las variables necesarias (NEON_URL)."
    exit 1
fi

# Build and start containers
echo "📦 Construyendo imágenes y arrancando contenedores..."
docker compose build --no-cache
docker compose up -d

echo "✅ Despliegue completado con éxito!"
echo "🌐 La aplicación debería estar disponible en: http://<tu-ip-contabo>:8081"
echo "🔍 Revisa los logs con: docker compose logs -f"

# --- NOTA DE MIGRACIÓN ---
# Si es la primera vez que despliegas con la base de datos local,
# ejecuta el script de migración una vez que los contenedores estén listos:
# bash migrate_neon_to_local.sh
