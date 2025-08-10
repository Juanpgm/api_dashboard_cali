# Inicialización, Despliegue y Mantenimiento

Inicialización (validación/corrección de esquema):

- database_initializer.py: crea/verifica tablas, corrige tipos claves y valida esquema final.

Ejecución local:

- Uvicorn con reload para desarrollo.
- Pool de conexiones configurado para producción en database.py.

Mantenimiento:

- production_maintenance.py: health checks, optimizaciones, backup opcional.
- production_deployment.py: despliegue con opciones de force/quiet.
