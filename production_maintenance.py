"""
Script de verificación y mantenimiento para el API Dashboard en producción.
Realiza chequeos de salud, optimizaciones y mantenimiento de la base de datos.
"""

import logging
import sys
import os
import time
from datetime import datetime
from sqlalchemy import create_engine, text
from typing import Dict, List, Any
import json

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi_project.database import engine, get_database_info
from database_initializer import DatabaseInitializer

# Configurar logging para mantenimiento
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'maintenance_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProductionMaintenance:
    """Clase para mantenimiento y verificación en producción"""
    
    def __init__(self):
        self.engine = engine
        self.db_info = get_database_info()
        self.initializer = DatabaseInitializer()
        
    def run_health_checks(self) -> Dict[str, Any]:
        """Ejecuta chequeos de salud completos"""
        logger.info("🏥 Ejecutando chequeos de salud del sistema...")
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "database_connection": False,
            "schema_integrity": False,
            "table_counts": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
        try:
            # 1. Verificar conexión a la base de datos
            health_report["database_connection"] = self.initializer.check_database_connection()
            
            # 2. Verificar integridad del esquema
            health_report["schema_integrity"] = self.initializer.verify_final_schema()
            
            # 3. Obtener conteos de tablas
            health_report["table_counts"] = self._get_table_counts()
            
            # 4. Métricas de rendimiento
            health_report["performance_metrics"] = self._get_performance_metrics()
            
            # 5. Generar recomendaciones
            health_report["recommendations"] = self._generate_recommendations(health_report)
            
            # 6. Estado general
            health_report["overall_status"] = (
                "HEALTHY" if health_report["database_connection"] and health_report["schema_integrity"]
                else "NEEDS_ATTENTION"
            )
            
        except Exception as e:
            logger.error(f"❌ Error durante chequeos de salud: {e}")
            health_report["error"] = str(e)
            health_report["overall_status"] = "ERROR"
        
        return health_report
    
    def _get_table_counts(self) -> Dict[str, int]:
        """Obtiene conteos de registros por tabla"""
        table_counts = {}
        important_tables = [
            'centros_gestores', 'programas', 'areas_funcionales',
            'propositos', 'retos', 'movimientos_presupuestales', 
            'ejecucion_presupuestal'
        ]
        
        try:
            with self.engine.connect() as connection:
                for table in important_tables:
                    try:
                        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        table_counts[table] = count
                        logger.info(f"📊 {table}: {count:,} registros")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo contar {table}: {e}")
                        table_counts[table] = -1
        except Exception as e:
            logger.error(f"❌ Error obteniendo conteos: {e}")
        
        return table_counts
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento de la base de datos"""
        metrics = {}
        
        try:
            with self.engine.connect() as connection:
                # Métricas de conexión
                metrics["pool_status"] = {
                    "size": self.engine.pool.size(),
                    "checked_in": self.engine.pool.checkedin(),
                    "checked_out": self.engine.pool.checkedout(),
                    "overflow": self.engine.pool.overflow(),
                    "max_overflow": self.engine.pool._max_overflow
                }
                
                # Métricas de PostgreSQL
                pg_stats_query = text("""
                    SELECT 
                        current_database() as database_name,
                        pg_size_pretty(pg_database_size(current_database())) as database_size,
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT count(*) FROM pg_stat_activity) as total_connections
                """)
                
                result = connection.execute(pg_stats_query)
                pg_stats = result.fetchone()
                
                metrics["database_stats"] = {
                    "database_name": pg_stats[0],
                    "database_size": pg_stats[1],
                    "active_connections": pg_stats[2],
                    "total_connections": pg_stats[3]
                }
                
                # Tiempo de respuesta de una consulta simple
                start_time = time.time()
                connection.execute(text("SELECT 1"))
                response_time = time.time() - start_time
                metrics["response_time_ms"] = round(response_time * 1000, 2)
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo métricas: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _generate_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el estado del sistema"""
        recommendations = []
        
        # Verificar conexión
        if not health_report.get("database_connection", False):
            recommendations.append("🔴 CRÍTICO: Verificar conexión a la base de datos")
        
        # Verificar esquema
        if not health_report.get("schema_integrity", False):
            recommendations.append("🟡 ATENCIÓN: Ejecutar inicializador de base de datos")
        
        # Verificar datos
        table_counts = health_report.get("table_counts", {})
        for table, count in table_counts.items():
            if count == 0:
                recommendations.append(f"🟡 DATOS: Tabla {table} está vacía")
            elif count == -1:
                recommendations.append(f"🔴 ERROR: No se puede acceder a tabla {table}")
        
        # Verificar rendimiento
        metrics = health_report.get("performance_metrics", {})
        response_time = metrics.get("response_time_ms", 0)
        if response_time > 1000:
            recommendations.append(f"🟡 RENDIMIENTO: Tiempo de respuesta alto ({response_time}ms)")
        
        # Verificar pool de conexiones
        pool_status = metrics.get("pool_status", {})
        if pool_status.get("checked_out", 0) > pool_status.get("size", 0) * 0.8:
            recommendations.append("🟡 CONEXIONES: Pool de conexiones cerca del límite")
        
        if not recommendations:
            recommendations.append("✅ Sistema funcionando correctamente")
        
        return recommendations
    
    def optimize_database(self):
        """Ejecuta optimizaciones de base de datos"""
        logger.info("⚡ Ejecutando optimizaciones de base de datos...")
        
        optimizations = [
            "VACUUM ANALYZE centros_gestores",
            "VACUUM ANALYZE programas", 
            "VACUUM ANALYZE areas_funcionales",
            "VACUUM ANALYZE propositos",
            "VACUUM ANALYZE retos",
            "VACUUM ANALYZE movimientos_presupuestales",
            "VACUUM ANALYZE ejecucion_presupuestal",
            "REINDEX DATABASE CONCURRENTLY"  # Solo si no hay tráfico
        ]
        
        try:
            with self.engine.connect() as connection:
                for optimization in optimizations[:-1]:  # Excluir REINDEX por ahora
                    try:
                        logger.info(f"🔧 Ejecutando: {optimization}")
                        connection.execute(text(optimization))
                        connection.commit()
                        logger.info(f"✅ Completado: {optimization}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error en optimización {optimization}: {e}")
            
            logger.info("✅ Optimizaciones completadas")
            
        except Exception as e:
            logger.error(f"❌ Error durante optimizaciones: {e}")
    
    def backup_critical_data(self, output_dir: str = "backups"):
        """Crea backup de datos críticos"""
        logger.info("💾 Creando backup de datos críticos...")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        tables_to_backup = [
            'centros_gestores', 'programas', 'areas_funcionales',
            'propositos', 'retos'
        ]
        
        try:
            with self.engine.connect() as connection:
                for table in tables_to_backup:
                    try:
                        query = text(f"SELECT * FROM {table}")
                        result = connection.execute(query)
                        rows = result.fetchall()
                        columns = result.keys()
                        
                        # Convertir a formato JSON
                        data = [dict(zip(columns, row)) for row in rows]
                        
                        backup_file = os.path.join(output_dir, f"{table}_backup_{timestamp}.json")
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                        
                        logger.info(f"✅ Backup creado: {backup_file} ({len(data)} registros)")
                        
                    except Exception as e:
                        logger.error(f"❌ Error creando backup de {table}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error durante backup: {e}")
    
    def generate_maintenance_report(self) -> str:
        """Genera reporte completo de mantenimiento"""
        logger.info("📋 Generando reporte de mantenimiento...")
        
        health_report = self.run_health_checks()
        
        report = f"""
# 🏛️ API Dashboard Alcaldía de Cali - Reporte de Mantenimiento
**Fecha:** {health_report['timestamp']}
**Estado General:** {health_report.get('overall_status', 'UNKNOWN')}

## 🔍 Estado del Sistema
- **Conexión BD:** {'✅' if health_report.get('database_connection') else '❌'}
- **Integridad Esquema:** {'✅' if health_report.get('schema_integrity') else '❌'}
- **Tiempo Respuesta:** {health_report.get('performance_metrics', {}).get('response_time_ms', 'N/A')} ms

## 📊 Conteo de Datos
"""
        
        for table, count in health_report.get('table_counts', {}).items():
            status = '✅' if count > 0 else ('❌' if count == -1 else '⚠️')
            report += f"- **{table}:** {status} {count:,} registros\n"
        
        report += "\n## 💡 Recomendaciones\n"
        for rec in health_report.get('recommendations', []):
            report += f"- {rec}\n"
        
        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"maintenance_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📋 Reporte guardado: {report_file}")
        return report_file

def main():
    """Función principal para mantenimiento"""
    print("🔧 API Dashboard - Sistema de Mantenimiento de Producción")
    print("=" * 60)
    
    maintenance = ProductionMaintenance()
    
    try:
        # Ejecutar chequeos de salud
        health_report = maintenance.run_health_checks()
        
        print(f"\n📊 Estado General: {health_report.get('overall_status', 'UNKNOWN')}")
        
        # Mostrar recomendaciones
        recommendations = health_report.get('recommendations', [])
        if recommendations:
            print("\n💡 Recomendaciones:")
            for rec in recommendations:
                print(f"  {rec}")
        
        # Generar reporte
        report_file = maintenance.generate_maintenance_report()
        print(f"\n📋 Reporte completo: {report_file}")
        
        # Opciones adicionales
        if "--optimize" in sys.argv:
            maintenance.optimize_database()
        
        if "--backup" in sys.argv:
            maintenance.backup_critical_data()
        
        print("\n✅ Mantenimiento completado")
        
    except Exception as e:
        logger.error(f"❌ Error durante mantenimiento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
