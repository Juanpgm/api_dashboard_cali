"""
Script inteligente de migración para actualizar la estructura de ejecución presupuestal
Analiza, repara y optimiza la base de datos con la nueva estructura de archivos JSON
"""

import logging
import sys
import os
import time
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Dict, List, Tuple, Any
import json

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi_project.database import SQLALCHEMY_DATABASE_URL, engine
from fastapi_project import models

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'database_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntelligentDatabaseMigrator:
    """Migrador inteligente de base de datos para ejecución presupuestal"""
    
    def __init__(self):
        self.engine = engine
        self.inspector = inspect(self.engine)
        self.metadata = MetaData()
        
    def analyze_current_structure(self) -> Dict[str, Any]:
        """Analiza la estructura actual de la base de datos"""
        logger.info("🔍 Analizando estructura actual de la base de datos...")
        
        analysis = {
            "existing_tables": [],
            "obsolete_tables": [],
            "tables_to_update": [],
            "new_tables_needed": [],
            "data_counts": {},
            "schema_issues": [],
            "recommendations": []
        }
        
        try:
            # Obtener tablas existentes
            existing_tables = self.inspector.get_table_names()
            analysis["existing_tables"] = existing_tables
            
            # Identificar tablas obsoletas relacionadas con ejecución presupuestal
            obsolete_patterns = [
                'project_execution',  # Tabla antigua
                'budget_execution_old',  # Si existe
                'movimientos_presupuestales_old',  # Respaldos antiguos
                'ejecucion_presupuestal_old'
            ]
            
            analysis["obsolete_tables"] = [
                table for table in existing_tables 
                if any(pattern in table for pattern in obsolete_patterns)
            ]
            
            # Tablas que necesitan actualización
            update_needed = [
                'movimientos_presupuestales',
                'ejecucion_presupuestal'
            ]
            
            analysis["tables_to_update"] = [
                table for table in update_needed if table in existing_tables
            ]
            
            # Nueva tabla necesaria
            if 'datos_caracteristicos_proyectos' not in existing_tables:
                analysis["new_tables_needed"].append('datos_caracteristicos_proyectos')
            
            # Contar datos existentes
            with self.engine.connect() as connection:
                for table in existing_tables:
                    if table in ['movimientos_presupuestales', 'ejecucion_presupuestal']:
                        try:
                            result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = result.scalar()
                            analysis["data_counts"][table] = count
                            logger.info(f"📊 {table}: {count:,} registros")
                        except Exception as e:
                            logger.warning(f"⚠️ No se pudo contar {table}: {e}")
                            analysis["data_counts"][table] = -1
            
            # Verificar problemas de esquema
            analysis["schema_issues"] = self._check_schema_issues()
            
            # Generar recomendaciones
            analysis["recommendations"] = self._generate_migration_recommendations(analysis)
            
        except Exception as e:
            logger.error(f"❌ Error durante análisis: {e}")
            analysis["error"] = str(e)
        
        return analysis
    
    def _check_schema_issues(self) -> List[Dict[str, str]]:
        """Verifica problemas en el esquema actual"""
        issues = []
        
        try:
            with self.engine.connect() as connection:
                # Verificar si existe periodo_corte vs periodo
                for table_name in ['movimientos_presupuestales', 'ejecucion_presupuestal']:
                    if table_name in self.inspector.get_table_names():
                        columns = [col['name'] for col in self.inspector.get_columns(table_name)]
                        
                        if 'periodo_corte' in columns and 'periodo' not in columns:
                            issues.append({
                                'table': table_name,
                                'issue': 'periodo_corte_to_periodo',
                                'description': f'Tabla {table_name} usa periodo_corte en lugar de periodo'
                            })
                        
                        # Verificar si falta ppto_disponible en ejecucion_presupuestal
                        if table_name == 'ejecucion_presupuestal' and 'ppto_disponible' not in columns:
                            issues.append({
                                'table': table_name,
                                'issue': 'missing_ppto_disponible',
                                'description': 'Falta columna ppto_disponible en ejecucion_presupuestal'
                            })
                        
                        # Verificar si existe ppto_disponible en movimientos_presupuestales (debería eliminarse)
                        if table_name == 'movimientos_presupuestales' and 'ppto_disponible' in columns:
                            issues.append({
                                'table': table_name,
                                'issue': 'duplicate_ppto_disponible',
                                'description': 'ppto_disponible no debería estar en movimientos_presupuestales'
                            })
                
        except Exception as e:
            logger.error(f"❌ Error verificando esquema: {e}")
        
        return issues
    
    def _generate_migration_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones de migración"""
        recommendations = []
        
        if analysis["obsolete_tables"]:
            recommendations.append(f"🗑️ Eliminar {len(analysis['obsolete_tables'])} tablas obsoletas")
        
        if analysis["tables_to_update"]:
            recommendations.append(f"🔄 Actualizar {len(analysis['tables_to_update'])} tablas existentes")
        
        if analysis["new_tables_needed"]:
            recommendations.append(f"➕ Crear {len(analysis['new_tables_needed'])} nuevas tablas")
        
        if analysis["schema_issues"]:
            recommendations.append(f"🔧 Corregir {len(analysis['schema_issues'])} problemas de esquema")
        
        total_records = sum(count for count in analysis["data_counts"].values() if count > 0)
        if total_records > 0:
            recommendations.append(f"💾 Respaldar {total_records:,} registros existentes")
        
        return recommendations
    
    def backup_existing_data(self, tables: List[str]) -> Dict[str, str]:
        """Crea backup de datos existentes"""
        logger.info("💾 Creando backup de datos existentes...")
        
        backup_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_dir = f"backups_migration_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            with self.engine.connect() as connection:
                for table in tables:
                    if table in self.inspector.get_table_names():
                        try:
                            # Backup como SQL
                            sql_backup = f"{backup_dir}/{table}_backup_{timestamp}.sql"
                            
                            # Obtener estructura
                            columns = [col['name'] for col in self.inspector.get_columns(table)]
                            
                            # Obtener datos
                            result = connection.execute(text(f"SELECT * FROM {table}"))
                            rows = result.fetchall()
                            
                            # Escribir SQL
                            with open(sql_backup, 'w', encoding='utf-8') as f:
                                f.write(f"-- Backup de {table} - {timestamp}\n")
                                f.write(f"-- {len(rows)} registros\n\n")
                                
                                if rows:
                                    columns_str = ", ".join(columns)
                                    f.write(f"-- INSERT INTO {table} ({columns_str}) VALUES\n")
                                    
                                    for i, row in enumerate(rows):
                                        values = []
                                        for val in row:
                                            if val is None:
                                                values.append("NULL")
                                            elif isinstance(val, str):
                                                values.append(f"'{val.replace(chr(39), chr(39)+chr(39))}'")
                                            else:
                                                values.append(str(val))
                                        
                                        values_str = "(" + ", ".join(values) + ")"
                                        if i == len(rows) - 1:
                                            f.write(f"-- {values_str};\n")
                                        else:
                                            f.write(f"-- {values_str},\n")
                            
                            backup_files[table] = sql_backup
                            logger.info(f"✅ Backup creado: {sql_backup} ({len(rows)} registros)")
                            
                        except Exception as e:
                            logger.error(f"❌ Error creando backup de {table}: {e}")
                            
        except Exception as e:
            logger.error(f"❌ Error durante backup: {e}")
        
        return backup_files
    
    def drop_obsolete_tables(self, tables: List[str]) -> bool:
        """Elimina tablas obsoletas"""
        logger.info(f"🗑️ Eliminando {len(tables)} tablas obsoletas...")
        
        try:
            with self.engine.connect() as connection:
                with connection.begin():
                    for table in tables:
                        try:
                            connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                            logger.info(f"✅ Tabla {table} eliminada")
                        except Exception as e:
                            logger.warning(f"⚠️ Error eliminando {table}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error eliminando tablas obsoletas: {e}")
            return False
    
    def update_existing_tables(self, tables: List[str], issues: List[Dict[str, str]]) -> bool:
        """Actualiza tablas existentes con nueva estructura"""
        logger.info(f"🔄 Actualizando {len(tables)} tablas existentes...")
        
        try:
            with self.engine.connect() as connection:
                with connection.begin():
                    # Procesar problemas de esquema
                    for issue in issues:
                        table_name = issue['table']
                        issue_type = issue['issue']
                        
                        try:
                            if issue_type == 'periodo_corte_to_periodo':
                                logger.info(f"🔧 Renombrando periodo_corte a periodo en {table_name}")
                                connection.execute(text(f"""
                                    ALTER TABLE {table_name} 
                                    RENAME COLUMN periodo_corte TO periodo
                                """))
                                
                            elif issue_type == 'missing_ppto_disponible' and table_name == 'ejecucion_presupuestal':
                                logger.info(f"➕ Agregando ppto_disponible a {table_name}")
                                connection.execute(text(f"""
                                    ALTER TABLE {table_name} 
                                    ADD COLUMN IF NOT EXISTS ppto_disponible BIGINT DEFAULT 0
                                """))
                                
                            elif issue_type == 'duplicate_ppto_disponible' and table_name == 'movimientos_presupuestales':
                                logger.info(f"➖ Eliminando ppto_disponible de {table_name}")
                                connection.execute(text(f"""
                                    ALTER TABLE {table_name} 
                                    DROP COLUMN IF EXISTS ppto_disponible
                                """))
                            
                            logger.info(f"✅ {issue['description']} - corregido")
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Error corrigiendo {issue['description']}: {e}")
                    
                    # Asegurar que las claves primarias sean correctas
                    for table_name in tables:
                        try:
                            # Eliminar restricción de clave primaria existente si existe
                            connection.execute(text(f"""
                                ALTER TABLE {table_name} 
                                DROP CONSTRAINT IF EXISTS {table_name}_pkey CASCADE
                            """))
                            
                            # Recrear clave primaria con bpin y periodo
                            connection.execute(text(f"""
                                ALTER TABLE {table_name} 
                                ADD CONSTRAINT {table_name}_pkey PRIMARY KEY (bpin, periodo)
                            """))
                            
                            logger.info(f"✅ Clave primaria actualizada en {table_name}")
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Error actualizando clave primaria en {table_name}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error actualizando tablas: {e}")
            return False
    
    def create_new_tables(self) -> bool:
        """Crea nuevas tablas necesarias"""
        logger.info("➕ Creando nuevas tablas...")
        
        try:
            # Usar SQLAlchemy para crear todas las tablas
            models.Base.metadata.create_all(bind=self.engine)
            
            # Verificar que la nueva tabla se creó
            if 'datos_caracteristicos_proyectos' in self.inspector.get_table_names():
                logger.info("✅ Tabla datos_caracteristicos_proyectos creada exitosamente")
            else:
                logger.warning("⚠️ No se pudo verificar la creación de datos_caracteristicos_proyectos")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando nuevas tablas: {e}")
            return False
    
    def optimize_database(self) -> bool:
        """Optimiza la base de datos después de la migración"""
        logger.info("⚡ Optimizando base de datos...")
        
        optimization_commands = [
            "VACUUM ANALYZE movimientos_presupuestales",
            "VACUUM ANALYZE ejecucion_presupuestal", 
            "VACUUM ANALYZE datos_caracteristicos_proyectos",
            # Recrear índices importantes
            "CREATE INDEX IF NOT EXISTS idx_movimientos_bpin ON movimientos_presupuestales(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_movimientos_periodo ON movimientos_presupuestales(periodo)",
            "CREATE INDEX IF NOT EXISTS idx_ejecucion_bpin ON ejecucion_presupuestal(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_ejecucion_periodo ON ejecucion_presupuestal(periodo)",
            "CREATE INDEX IF NOT EXISTS idx_caracteristicos_bpin ON datos_caracteristicos_proyectos(bpin)",
            "CREATE INDEX IF NOT EXISTS idx_caracteristicos_sector ON datos_caracteristicos_proyectos(cod_sector)",
            "CREATE INDEX IF NOT EXISTS idx_caracteristicos_producto ON datos_caracteristicos_proyectos(cod_producto)"
        ]
        
        try:
            with self.engine.connect() as connection:
                for command in optimization_commands:
                    try:
                        connection.execute(text(command))
                        connection.commit()
                        logger.info(f"✅ {command.split()[0]} completado")
                    except Exception as e:
                        logger.warning(f"⚠️ Error en optimización {command}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante optimización: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verifica que la migración fue exitosa"""
        logger.info("🔍 Verificando migración...")
        
        try:
            with self.engine.connect() as connection:
                # Verificar que las tablas existen
                required_tables = [
                    'movimientos_presupuestales',
                    'ejecucion_presupuestal', 
                    'datos_caracteristicos_proyectos'
                ]
                
                existing_tables = self.inspector.get_table_names()
                
                for table in required_tables:
                    if table not in existing_tables:
                        logger.error(f"❌ Tabla faltante: {table}")
                        return False
                    
                    # Verificar estructura
                    columns = [col['name'] for col in self.inspector.get_columns(table)]
                    
                    if table in ['movimientos_presupuestales', 'ejecucion_presupuestal']:
                        if 'periodo' not in columns:
                            logger.error(f"❌ Columna 'periodo' faltante en {table}")
                            return False
                        if 'periodo_corte' in columns:
                            logger.error(f"❌ Columna obsoleta 'periodo_corte' encontrada en {table}")
                            return False
                    
                    if table == 'ejecucion_presupuestal' and 'ppto_disponible' not in columns:
                        logger.error(f"❌ Columna 'ppto_disponible' faltante en {table}")
                        return False
                    
                    if table == 'datos_caracteristicos_proyectos':
                        required_cols = ['bpin', 'cod_sector', 'cod_producto']
                        for col in required_cols:
                            if col not in columns:
                                logger.error(f"❌ Columna '{col}' faltante en {table}")
                                return False
                
                logger.info("✅ Estructura de tablas verificada correctamente")
                
                # Probar inserts básicos
                test_queries = [
                    "SELECT 1 FROM movimientos_presupuestales LIMIT 1",
                    "SELECT 1 FROM ejecucion_presupuestal LIMIT 1",
                    "SELECT 1 FROM datos_caracteristicos_proyectos LIMIT 1"
                ]
                
                for query in test_queries:
                    try:
                        connection.execute(text(query))
                    except Exception as e:
                        logger.error(f"❌ Error probando {query}: {e}")
                        return False
                
                logger.info("✅ Consultas de prueba ejecutadas correctamente")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error durante verificación: {e}")
            return False
    
    def run_intelligent_migration(self) -> bool:
        """Ejecuta migración inteligente completa"""
        logger.info("🚀 Iniciando migración inteligente de ejecución presupuestal")
        logger.info("=" * 70)
        
        try:
            # 1. Analizar estructura actual
            analysis = self.analyze_current_structure()
            
            logger.info("📋 ANÁLISIS COMPLETO:")
            logger.info(f"   • Tablas existentes: {len(analysis['existing_tables'])}")
            logger.info(f"   • Tablas obsoletas: {len(analysis['obsolete_tables'])}")
            logger.info(f"   • Tablas a actualizar: {len(analysis['tables_to_update'])}")
            logger.info(f"   • Nuevas tablas: {len(analysis['new_tables_needed'])}")
            logger.info(f"   • Problemas de esquema: {len(analysis['schema_issues'])}")
            
            logger.info("💡 RECOMENDACIONES:")
            for rec in analysis['recommendations']:
                logger.info(f"   • {rec}")
            
            # 2. Crear backup de datos existentes
            if analysis['tables_to_update']:
                backup_files = self.backup_existing_data(analysis['tables_to_update'])
                logger.info(f"💾 {len(backup_files)} backups creados")
            
            # 3. Eliminar tablas obsoletas
            if analysis['obsolete_tables']:
                if not self.drop_obsolete_tables(analysis['obsolete_tables']):
                    logger.error("❌ Error eliminando tablas obsoletas")
                    return False
            
            # 4. Actualizar tablas existentes
            if analysis['tables_to_update'] or analysis['schema_issues']:
                if not self.update_existing_tables(analysis['tables_to_update'], analysis['schema_issues']):
                    logger.error("❌ Error actualizando tablas existentes")
                    return False
            
            # 5. Crear nuevas tablas
            if analysis['new_tables_needed']:
                if not self.create_new_tables():
                    logger.error("❌ Error creando nuevas tablas")
                    return False
            
            # 6. Optimizar base de datos
            if not self.optimize_database():
                logger.warning("⚠️ Errores durante optimización (no críticos)")
            
            # 7. Verificar migración
            if not self.verify_migration():
                logger.error("❌ Verificación de migración falló")
                return False
            
            # 8. Reporte final
            logger.info("=" * 70)
            logger.info("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
            logger.info("=" * 70)
            logger.info("📋 RESUMEN:")
            logger.info("   ✅ Estructura actualizada para nueva data de ejecución presupuestal")
            logger.info("   ✅ Columnas renombradas: periodo_corte → periodo")
            logger.info("   ✅ Variables reorganizadas: ppto_disponible solo en ejecución")
            logger.info("   ✅ Nueva tabla: datos_caracteristicos_proyectos")
            logger.info("   ✅ Índices optimizados para rendimiento")
            logger.info("   ✅ Compatibilidad con nuevos archivos JSON")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante migración: {e}")
            return False

def main():
    """Función principal"""
    print("🏛️ API Dashboard Alcaldía de Cali - Migrador Inteligente")
    print("🔄 Migración de Ejecución Presupuestal")
    print("=" * 70)
    
    migrator = IntelligentDatabaseMigrator()
    
    start_time = time.time()
    success = migrator.run_intelligent_migration()
    end_time = time.time()
    
    print(f"\n⏱️ Tiempo total: {end_time - start_time:.2f} segundos")
    
    if success:
        print("\n🎯 PRÓXIMOS PASOS:")
        print("1. ✅ Reiniciar el servidor FastAPI")
        print("2. ✅ Probar endpoints actualizados")
        print("3. ✅ Cargar nuevos datos JSON")
        print("4. ✅ Verificar funcionalidad en frontend")
        
        sys.exit(0)
    else:
        print("\n❌ MIGRACIÓN FALLÓ - Revisar logs para detalles")
        sys.exit(1)

if __name__ == "__main__":
    main()
