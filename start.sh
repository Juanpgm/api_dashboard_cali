#!/bin/bash
# Start script para Railway deployment
echo "🚀 Iniciando API Dashboard Cali en Railway..."
exec uvicorn fastapi_project.main:app --host 0.0.0.0 --port $PORT
