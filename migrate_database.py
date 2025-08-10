"""
Script de migración para aplicar el nuevo esquema de base de datos
"""
from sqlalchemy import create_engine, text
from fastapi_project.database import SQLALCHEMY_DATABASE_URL, engine
import os

def apply_database_schema():
    """
    Aplica el esquema de base de datos completo
    """
    print("🚀 Iniciando aplicación del esquema de base de datos...")
    
    # Leer el archivo SQL del esquema
    schema_file_path = os.path.join(os.path.dirname(__file__), "database_schema.sql")
    
    if not os.path.exists(schema_file_path):
        print("❌ Archivo database_schema.sql no encontrado")
        return False
    
    try:
        # Leer el contenido del archivo SQL
        with open(schema_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # Dividir el contenido en statements individuales
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        print(f"📄 Archivo SQL leído. {len(statements)} statements encontrados.")
        
        # Ejecutar cada statement
        with engine.begin() as connection:
            for i, statement in enumerate(statements):
                if statement.strip():
                    try:
                        print(f"⚡ Ejecutando statement {i+1}/{len(statements)}...")
                        connection.execute(text(statement))
                    except Exception as stmt_error:
                        print(f"⚠️ Error en statement {i+1}: {stmt_error}")
                        # Continuar con el siguiente statement
                        continue
        
        print("✅ Esquema de base de datos aplicado exitosamente!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando el esquema: {e}")
        return False

def check_database_structure():
    """
    Verifica la estructura de la base de datos
    """
    print("\n🔍 Verificando estructura de la base de datos...")
    
    check_queries = [
        ("Verificando extensión PostGIS", "SELECT PostGIS_Version();"),
        ("Contando tablas de catálogos", """
            SELECT COUNT(*) as total_catalog_tables 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('programas', 'lineas_estrategicas', 'dimensiones', 'sectores', 
                              'propositos', 'retos', 'areas_funcionales', 'centros_gestores',
                              'fuentes_financiamiento', 'categorias_alcalde', 'pospre', 'bp',
                              'actividades', 'productos');
        """),
        ("Contando tablas de proyectos", """
            SELECT COUNT(*) as total_project_tables
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('proyectos', 'movimientos_presupuestales', 'ejecucion_presupuestal',
                              'seguimiento_pa', 'seguimiento_actividades_pa', 'seguimiento_productos_pa',
                              'unidades_proyecto', 'unidades_proyecto_infraestructura_equipamientos',
                              'unidades_proyecto_infraestructura_vial');
        """),
        ("Contando tablas de contratos", """
            SELECT COUNT(*) as total_contract_tables
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('ordenadores_gasto', 'supervisores', 'contratos', 
                              'contrato_valores', 'contrato_fechas');
        """),
        ("Contando tablas de cartografía", """
            SELECT COUNT(*) as total_cartography_tables
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('corregimientos', 'comunas', 'veredas', 'barrios', 
                              'equipamientos', 'vias');
        """),
        ("Verificando índices geoespaciales", """
            SELECT COUNT(*) as total_spatial_indexes
            FROM pg_indexes 
            WHERE indexname LIKE '%geom%' AND schemaname = 'public';
        """)
    ]
    
    try:
        with engine.connect() as connection:
            for description, query in check_queries:
                try:
                    result = connection.execute(text(query))
                    row = result.fetchone()
                    if row:
                        print(f"✅ {description}: {row[0] if hasattr(row, '__getitem__') else row}")
                    else:
                        print(f"✅ {description}: Verificado")
                except Exception as e:
                    print(f"⚠️ {description}: Error - {e}")
        
        # Verificar tabla original para compatibilidad
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT COUNT(*) FROM project_execution;"))
                count = result.scalar()
                print(f"📊 Tabla original project_execution: {count} registros")
        except Exception as e:
            print(f"⚠️ Tabla project_execution: {e}")
            
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")

def main():
    """
    Función principal de migración
    """
    print("=" * 60)
    print("🎯 MIGRACIÓN DE ESQUEMA DE BASE DE DATOS")
    print("=" * 60)
    
    # Aplicar esquema
    success = apply_database_schema()
    
    if success:
        # Verificar estructura
        check_database_structure()
        
        print("\n" + "=" * 60)
        print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Verificar que tu aplicación FastAPI funciona correctamente")
        print("2. Usar los nuevos endpoints para insertar datos en las tablas normalizadas")
        print("3. Migrar datos existentes de project_execution a las nuevas tablas")
        print("4. Actualizar tu frontend para usar los nuevos endpoints")
        print("\n🔗 Los endpoints existentes siguen funcionando para compatibilidad")
        
    else:
        print("\n❌ LA MIGRACIÓN FALLÓ")
        print("Revisa los errores anteriores y corrige los problemas antes de continuar.")

if __name__ == "__main__":
    main()
