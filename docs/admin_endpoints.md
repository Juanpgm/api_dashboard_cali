# Endpoints ADMIN y Diagnóstico

GET /health

- Verifica conexión a BD con SELECT 1.

GET /database_status

- Lista todas las tablas (schema public) y cuenta de registros.

GET /tables_info

- Lista columnas por tabla (schema public) con: column_name, data_type, is_nullable, default.
- Incluye un status lógico (active) a nivel tabla.

DELETE /clear_all_data

- Elimina datos de todas las tablas del schema public dentro de una transacción.
- Úsese solo para limpieza completa.
