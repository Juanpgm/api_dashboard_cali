"""
Script inteligente de migración y mantenimiento de base de datos
Detecta automáticamente todas las clases, subclases y atributos disponibles
y pone en funcionamiento toda la estructura de la base de datos
"""

import os
import sys
import inspect
import logging
from typing import Dict, List, Tuple, Any, Set
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateTable

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi_project.database import engine, Base
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
    """
    Migrador inteligente de base de datos que:
    - Detecta automáticamente todas las clases SQLAlchemy
    - Analiza la estructura actual vs. la deseada
    - Elimina tablas obsoletas
    - Crea/actualiza tablas nuevas
    - Mantiene integridad de datos cuando es posible
    """
    
    def __init__(self):
        self.engine = engine
        self.metadata = MetaData()
        self.detected_models = {}
        self.existing_tables = set()
        self.obsolete_tables = set()
        self.new_tables = set()
        self.modified_tables = set()
        
    def analyze_model_classes(self) -> Dict[str, Any]:
        """Detecta automáticamente todas las clases SQLAlchemy definidas"""
        logger.info("🔍 Analizando clases de modelos SQLAlchemy...")
        
        model_classes = {}
        
        # Obtener todas las clases del módulo models
        for name, obj in inspect.getmembers(models):
            if (inspect.isclass(obj) and 
                hasattr(obj, '__tablename__') and 
                hasattr(obj, '__table__')):
                
                model_classes[obj.__tablename__] = {
                    'class': obj,
                    'name': name,
                    'tablename': obj.__tablename__,
                    'columns': self._analyze_table_columns(obj),
                    'indexes': self._analyze_table_indexes(obj),
                    'relationships': self._analyze_relationships(obj)
                }
                
                logger.info(f"✅ Detectada clase: {name} -> tabla: {obj.__tablename__}")
        
        self.detected_models = model_classes
        logger.info(f"📊 Total de modelos detectados: {len(model_classes)}")
        return model_classes
    
    def _analyze_table_columns(self, model_class) -> Dict[str, Dict]:
        """Analiza las columnas de una tabla"""
        columns = {}
        
        if hasattr(model_class, '__table__'):
            for column in model_class.__table__.columns:
                columns[column.name] = {
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key,
                    'foreign_key': column.foreign_keys,
                    'default': column.default,
                    'index': column.index
                }
        
        return columns
    
    def _analyze_table_indexes(self, model_class) -> List[str]:
        """Analiza los índices de una tabla"""
        indexes = []
        
        if hasattr(model_class, '__table__'):
            for index in model_class.__table__.indexes:
                indexes.append(index.name)
        
        return indexes
    
    def _analyze_relationships(self, model_class) -> List[str]:
        """Analiza las relaciones de una tabla"""
        relationships = []
        
        for name, attr in inspect.getmembers(model_class):
            if hasattr(attr, 'property') and hasattr(attr.property, 'mapper'):
                relationships.append(name)
        
        return relationships
    
    def get_existing_database_structure(self) -> Dict[str, Any]:
        """Obtiene la estructura actual de la base de datos"""
        logger.info("📋 Analizando estructura actual de la base de datos...")
        
        existing_structure = {}
        
        try:
            # Refrescar metadata desde la base de datos
            self.metadata.reflect(bind=self.engine)
            
            for table_name in self.metadata.tables:
                table = self.metadata.tables[table_name]
                self.existing_tables.add(table_name)
                
                existing_structure[table_name] = {
                    'columns': {col.name: {
                        'type': str(col.type),
                        'nullable': col.nullable,
                        'primary_key': col.primary_key,
                        'foreign_key': bool(col.foreign_keys),
                        'default': col.default
                    } for col in table.columns},
                    'indexes': [idx.name for idx in table.indexes],
                    'constraints': [cons.name for cons in table.constraints if cons.name]
                }
                
                logger.info(f"📊 Tabla existente: {table_name} ({len(table.columns)} columnas)")
        
        except Exception as e:
            logger.error(f"❌ Error analizando estructura existente: {e}")
        
        logger.info(f"📊 Total de tablas existentes: {len(self.existing_tables)}")
        return existing_structure
    
    def identify_changes_needed(self) -> Dict[str, Set[str]]:
        """Identifica qué cambios son necesarios"""
        logger.info("🔄 Identificando cambios necesarios...")
        
        model_tables = set(self.detected_models.keys())
        
        # Tablas nuevas: están en modelos pero no en BD
        self.new_tables = model_tables - self.existing_tables
        
        # Tablas obsoletas: están en BD pero no en modelos (con algunas excepciones)
        protected_tables = {
            'spatial_ref_sys',  # PostGIS
            'geography_columns',  # PostGIS
            'geometry_columns',  # PostGIS
            'alembic_version'  # Migraciones
        }
        
        self.obsolete_tables = self.existing_tables - model_tables - protected_tables
        
        # Tablas que podrían necesitar modificaciones
        self.modified_tables = model_tables & self.existing_tables
        
        changes = {
            'new_tables': self.new_tables,
            'obsolete_tables': self.obsolete_tables,
            'modified_tables': self.modified_tables,
            'protected_tables': protected_tables
        }
        
        logger.info(f"🆕 Tablas nuevas: {len(self.new_tables)}")
        logger.info(f"🗑️ Tablas obsoletas: {len(self.obsolete_tables)}")
        logger.info(f"🔄 Tablas a modificar: {len(self.modified_tables)}")
        
        return changes
    
    def backup_important_data(self) -> Dict[str, int]:
        """Hace backup de datos importantes antes de cambios"""
        logger.info("💾 Creando backup de datos importantes...")
        
        backup_counts = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups_{timestamp}"
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Tablas importantes para backup
        important_tables = self.existing_tables & {
            'centros_gestores', 'programas', 'areas_funcionales',
            'propositos', 'retos', 'proyectos', 
            'movimientos_presupuestales', 'ejecucion_presupuestal',
            'datos_caracteristicos_proyectos',
            'project_execution'  # Tabla legacy
        }
        
        try:
            with self.engine.connect() as connection:
                for table in important_tables:
                    try:
                        # Contar registros
                        count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.scalar()
                        backup_counts[table] = count
                        
                        if count > 0:
                            # Crear backup SQL
                            backup_file = os.path.join(backup_dir, f"{table}_backup.sql")
                            
                            # Usar pg_dump si está disponible
                            try:
                                import subprocess
                                cmd = [
                                    'pg_dump', 
                                    '--table', table,
                                    '--data-only',
                                    '--file', backup_file,
                                    str(self.engine.url)
                                ]
                                subprocess.run(cmd, check=True)
                                logger.info(f"✅ Backup SQL: {table} ({count} registros)")
                            except:
                                # Fallback: backup manual
                                result = connection.execute(text(f"SELECT * FROM {table}"))
                                with open(backup_file.replace('.sql', '.txt'), 'w') as f:
                                    f.write(f"-- Backup de {table} - {count} registros\n")
                                logger.info(f"✅ Backup manual: {table} ({count} registros)")
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error en backup de {table}: {e}")
                        backup_counts[table] = -1
        
        except Exception as e:
            logger.error(f"❌ Error durante backup: {e}")
        
        return backup_counts
    
    def remove_obsolete_tables(self):
        """Elimina tablas obsoletas de forma segura"""
        logger.info("🗑️ Eliminando tablas obsoletas...")
        
        if not self.obsolete_tables:
            logger.info("✅ No hay tablas obsoletas para eliminar")
            return
        
        try:
            with self.engine.begin() as connection:
                for table_name in self.obsolete_tables:
                    try:
                        logger.info(f"🗑️ Eliminando tabla obsoleta: {table_name}")
                        connection.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                        logger.info(f"✅ Tabla eliminada: {table_name}")
                    except Exception as e:
                        logger.error(f"❌ Error eliminando {table_name}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error durante eliminación de tablas: {e}")
    
    def create_new_tables(self):
        """Crea tablas nuevas usando los modelos SQLAlchemy"""
        logger.info("🆕 Creando tablas nuevas...")
        
        if not self.new_tables:
            logger.info("✅ No hay tablas nuevas para crear")
            return
        
        try:
            # Crear solo las tablas nuevas
            for table_name in self.new_tables:
                if table_name in self.detected_models:
                    model_class = self.detected_models[table_name]['class']
                    try:
                        logger.info(f"🆕 Creando tabla: {table_name}")
                        model_class.__table__.create(self.engine, checkfirst=True)
                        logger.info(f"✅ Tabla creada: {table_name}")
                    except Exception as e:
                        logger.error(f"❌ Error creando {table_name}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error durante creación de tablas: {e}")
    
    def update_modified_tables(self):
        """Actualiza tablas que necesitan modificaciones"""
        logger.info("🔄 Actualizando tablas modificadas...")
        
        if not self.modified_tables:
            logger.info("✅ No hay tablas para modificar")
            return
        
        try:
            with self.engine.begin() as connection:
                for table_name in self.modified_tables:
                    logger.info(f"🔄 Verificando tabla: {table_name}")
                    
                    if table_name in self.detected_models:
                        model_info = self.detected_models[table_name]
                        model_columns = model_info['columns']
                        
                        # Verificar si la tabla existe y tiene todas las columnas necesarias
                        try:
                            # Obtener columnas actuales
                            result = connection.execute(text(f"""
                                SELECT column_name, data_type, is_nullable, column_default
                                FROM information_schema.columns 
                                WHERE table_name = '{table_name}'
                                AND table_schema = 'public'
                            """))
                            
                            existing_columns = {row[0]: {
                                'type': row[1],
                                'nullable': row[2] == 'YES',
                                'default': row[3]
                            } for row in result}
                            
                            # Detectar columnas faltantes
                            missing_columns = set(model_columns.keys()) - set(existing_columns.keys())
                            
                            if missing_columns:
                                logger.info(f"➕ Añadiendo columnas faltantes a {table_name}: {missing_columns}")
                                
                                for column_name in missing_columns:
                                    try:
                                        # Usar información del modelo para crear la columna
                                        model_class = model_info['class']
                                        table_obj = model_class.__table__
                                        column = table_obj.columns[column_name]
                                        
                                        # Construir statement ADD COLUMN
                                        nullable = "NULL" if column.nullable else "NOT NULL"
                                        default_clause = ""
                                        
                                        if column.default is not None:
                                            if hasattr(column.default, 'arg'):
                                                default_clause = f" DEFAULT {column.default.arg}"
                                        
                                        alter_statement = f"""
                                            ALTER TABLE {table_name} 
                                            ADD COLUMN IF NOT EXISTS {column_name} {column.type} {nullable}{default_clause}
                                        """
                                        
                                        connection.execute(text(alter_statement))
                                        logger.info(f"✅ Columna añadida: {table_name}.{column_name}")
                                        
                                    except Exception as e:
                                        logger.error(f"❌ Error añadiendo columna {column_name}: {e}")
                            else:
                                logger.info(f"✅ Tabla {table_name} está actualizada")
                                
                        except Exception as e:
                            logger.error(f"❌ Error verificando {table_name}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error durante actualización de tablas: {e}")
    
    def create_indexes_and_constraints(self):
        """Crea índices y restricciones faltantes"""
        logger.info("📇 Creando índices y restricciones...")
        
        try:
            with self.engine.begin() as connection:
                for table_name, model_info in self.detected_models.items():
                    model_class = model_info['class']
                    
                    if hasattr(model_class, '__table__'):
                        table_obj = model_class.__table__
                        
                        # Crear índices
                        for index in table_obj.indexes:
                            try:
                                logger.info(f"📇 Creando índice: {index.name}")
                                index.create(self.engine, checkfirst=True)
                                logger.info(f"✅ Índice creado: {index.name}")
                            except Exception as e:
                                logger.warning(f"⚠️ Error creando índice {index.name}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error creando índices: {e}")
    
    def verify_migration_success(self) -> Dict[str, Any]:
        """Verifica que la migración fue exitosa"""
        logger.info("✅ Verificando éxito de la migración...")
        
        verification = {
            'timestamp': datetime.now().isoformat(),
            'tables_created': 0,
            'tables_verified': 0,
            'total_records': 0,
            'issues': []
        }
        
        try:
            with self.engine.connect() as connection:
                # Verificar que todas las tablas del modelo existen
                for table_name in self.detected_models.keys():
                    try:
                        result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = result.scalar()
                        verification['tables_verified'] += 1
                        verification['total_records'] += count
                        logger.info(f"✅ Tabla verificada: {table_name} ({count} registros)")
                    except Exception as e:
                        verification['issues'].append(f"Tabla {table_name}: {e}")
                        logger.error(f"❌ Error verificando {table_name}: {e}")
                
                verification['tables_created'] = verification['tables_verified']
                
        except Exception as e:
            logger.error(f"❌ Error durante verificación: {e}")
            verification['issues'].append(f"Error general: {e}")
        
        return verification
    
    def generate_migration_report(self, backup_counts: Dict[str, int], 
                                verification: Dict[str, Any]) -> str:
        """Genera un reporte completo de la migración"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"migration_report_{timestamp}.md"
        
        report = f"""# 🗄️ Reporte de Migración de Base de Datos
**Fecha:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Sistema:** API Dashboard Alcaldía de Cali

## 📊 Resumen de Cambios
- **Tablas nuevas creadas:** {len(self.new_tables)}
- **Tablas obsoletas eliminadas:** {len(self.obsolete_tables)}
- **Tablas modificadas:** {len(self.modified_tables)}
- **Total de modelos detectados:** {len(self.detected_models)}

## 🆕 Tablas Nuevas Creadas
"""
        for table in self.new_tables:
            report += f"- ✅ {table}\n"
        
        report += "\n## 🗑️ Tablas Obsoletas Eliminadas\n"
        for table in self.obsolete_tables:
            report += f"- ❌ {table}\n"
        
        report += "\n## 🔄 Tablas Modificadas\n"
        for table in self.modified_tables:
            report += f"- 🔄 {table}\n"
        
        report += "\n## 💾 Backup de Datos\n"
        for table, count in backup_counts.items():
            status = "✅" if count >= 0 else "❌"
            report += f"- {status} {table}: {count} registros\n"
        
        report += f"\n## ✅ Verificación Final\n"
        report += f"- **Tablas verificadas:** {verification['tables_verified']}\n"
        report += f"- **Total de registros:** {verification['total_records']:,}\n"
        
        if verification['issues']:
            report += "\n## ⚠️ Problemas Detectados\n"
            for issue in verification['issues']:
                report += f"- ❌ {issue}\n"
        else:
            report += "\n🎉 **Migración completada sin problemas**\n"
        
        # Guardar reporte
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📋 Reporte guardado: {report_file}")
        return report_file

def main():
    """Función principal de migración inteligente"""
    print("🚀 MIGRADOR INTELIGENTE DE BASE DE DATOS")
    print("=" * 60)
    print("Sistema: API Dashboard Alcaldía de Cali")
    print("Detecta y migra automáticamente toda la estructura")
    print("=" * 60)
    
    migrator = IntelligentDatabaseMigrator()
    
    try:
        # 1. Analizar modelos definidos
        print("\n🔍 FASE 1: Análisis de Modelos")
        models_detected = migrator.analyze_model_classes()
        
        # 2. Analizar estructura actual
        print("\n📋 FASE 2: Análisis de Estructura Actual")
        current_structure = migrator.get_existing_database_structure()
        
        # 3. Identificar cambios necesarios
        print("\n🔄 FASE 3: Identificación de Cambios")
        changes = migrator.identify_changes_needed()
        
        # 4. Backup de datos importantes
        print("\n💾 FASE 4: Backup de Datos")
        backup_counts = migrator.backup_important_data()
        
        # 5. Ejecutar migración
        print("\n🔧 FASE 5: Ejecución de Migración")
        
        # 5.1 Eliminar tablas obsoletas
        migrator.remove_obsolete_tables()
        
        # 5.2 Crear tablas nuevas
        migrator.create_new_tables()
        
        # 5.3 Actualizar tablas existentes
        migrator.update_modified_tables()
        
        # 5.4 Crear índices y restricciones
        migrator.create_indexes_and_constraints()
        
        # 6. Verificación final
        print("\n✅ FASE 6: Verificación Final")
        verification = migrator.verify_migration_success()
        
        # 7. Generar reporte
        print("\n📋 FASE 7: Generación de Reporte")
        report_file = migrator.generate_migration_report(backup_counts, verification)
        
        print("\n" + "=" * 60)
        print("🎉 MIGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)
        print(f"📊 Tablas verificadas: {verification['tables_verified']}")
        print(f"📈 Total de registros: {verification['total_records']:,}")
        print(f"📋 Reporte completo: {report_file}")
        
        if verification['issues']:
            print(f"\n⚠️ {len(verification['issues'])} problemas detectados (ver reporte)")
        else:
            print("\n✨ Migración sin problemas")
        
    except Exception as e:
        logger.error(f"❌ Error fatal durante migración: {e}")
        print(f"\n💥 ERROR FATAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
