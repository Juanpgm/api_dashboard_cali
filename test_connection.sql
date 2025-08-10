-- Test de conexión a PostgreSQL
-- Usar SQLTools para ejecutar estas consultas

-- Ver las tablas disponibles
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Contar registros en algunas tablas principales
SELECT 
    'programas' as tabla, COUNT(*) as registros FROM programas
UNION ALL
SELECT 
    'proyectos' as tabla, COUNT(*) as registros FROM proyectos
UNION ALL
SELECT 
    'centros_gestores' as tabla, COUNT(*) as registros FROM centros_gestores
ORDER BY tabla;

-- Ver información de la base de datos
SELECT 
    current_database() as database_name,
    current_user as current_user,
    version() as postgresql_version;
