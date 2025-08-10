# Cambios y Mejoras (Agosto 2025)

Versión actual: 2.0.0

Cambios desde la versión anterior:

- ADMIN dinámico: /database_status y /clear_all_data ahora recorren todas las tablas del schema public.
- tables_info consolidado: atributos por tabla + status (sin segregación por variable).
- NUEVO: PUT de edición por BPIN para equipamientos y vial.
- Removidos: PUT de corrección por BPIN inválido (a petición explícita).
- Cargas masivas más robustas: upsert con ON CONFLICT (claves simples/compuestas) y validación Pydantic.
- Unidades de proyecto: endpoints GET/POST + GeoJSON RFC7946.
- Inicialización: verificación/corrección automática de tipos críticos (bpin BIGINT, identificador VARCHAR).
