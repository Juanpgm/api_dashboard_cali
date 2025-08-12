#!/bin/bash

# Script de inicio para producción - Compatible con Render y otras plataformas

echo "🚀 Iniciando API Dashboard - Alcaldía de Santiago de Cali"
echo "⏰ Timestamp: $(date)"

# Configurar variables de entorno por defecto si no existen
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-1}

# Verificar que las variables de entorno críticas estén configuradas
if [ -z "$DATABASE_URL" ] && [ -z "$POSTGRES_SERVER" ]; then
    echo "❌ ERROR: Variables de base de datos no configuradas"
    echo "   Configura DATABASE_URL o POSTGRES_SERVER, POSTGRES_USER, etc."
    exit 1
fi

echo "✅ Variables de entorno verificadas"

# Instalar dependencias si es necesario (para algunos entornos)
if [ ! -d "venv" ] && [ -f "requirements.txt" ]; then
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Crear directorio de logs si no existe
mkdir -p logs

echo "🔄 Iniciando servidor FastAPI en puerto $PORT..."

# Ejecutar la aplicación con configuración optimizada para producción
exec uvicorn fastapi_project.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers $WORKERS \
    --access-log \
    --log-level info
