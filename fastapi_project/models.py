"""
SQLAlchemy ORM models for the API Dashboard.

Notes:
- PostgreSQL is the target database; types reflect production schema.
- Geometries are kept as Text placeholders here (GeoJSON), not Geometry, to
    decouple spatial storage from attribute tables and simplify deployments.
- Relationships are minimized to avoid unnecessary joins until needed.
"""

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Text, DECIMAL, SmallInteger, ForeignKey, UniqueConstraint, TIMESTAMP, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
# from geoalchemy2 import Geometry  # Comentado temporalmente, usando Text para geometrías
from fastapi_project.database import Base

# =============================================================================
class CentroGestor(Base):
    __tablename__ = "centros_gestores"

    cod_centro_gestor = Column(Integer, primary_key=True, index=True)
    nombre_centro_gestor = Column(Text, nullable=False)
    
class Programa(Base):
    __tablename__ = "programas"

    cod_programa = Column(Integer, primary_key=True, index=True)
    nombre_programa = Column(Text, nullable=False)

class AreaFuncional(Base):
    __tablename__ = "areas_funcionales"

    cod_area_funcional = Column(Integer, primary_key=True, index=True)
    nombre_area_funcional = Column(Text, nullable=False)

class Proposito(Base):
    __tablename__ = "propositos"

    cod_proposito = Column(Integer, primary_key=True, index=True)
    nombre_proposito = Column(Text, nullable=False)

class Reto(Base):
    __tablename__ = "retos"

    cod_reto = Column(Integer, primary_key=True, index=True)
    nombre_reto = Column(Text, nullable=False)
       
class MovimientoPresupuestal(Base):
    __tablename__ = "movimientos_presupuestales"

    bpin = Column(BigInteger, primary_key=True, index=True)
    periodo_corte = Column(String, primary_key=True, nullable=False)
    ppto_inicial = Column(Float, nullable=False)
    adiciones = Column(Float, nullable=False)
    reducciones = Column(Float, nullable=False)
    ppto_modificado = Column(Float, nullable=False)

class EjecucionPresupuestal(Base):
    __tablename__ = "ejecucion_presupuestal"

    bpin = Column(BigInteger, primary_key=True, index=True)
    periodo_corte = Column(String, primary_key=True, nullable=False)
    ejecucion = Column(Float, nullable=False)
    pagos = Column(Float, nullable=False)
    saldos_cdp = Column(Float, nullable=False)
    total_acumul_obligac = Column(Float, nullable=False)
    total_acumulado_cdp = Column(Float, nullable=False)
    total_acumulado_rpc = Column(Float, nullable=False)
 
# =============================================================================
# Clase: PROYECTO
# =============================================================================

class Proyecto(Base):
    __tablename__ = "proyectos"
    
    bpin = Column(String(50), primary_key=True)
    nombre_proyecto_bpin = Column(String(500), nullable=False)
    nombre_bp = Column(String(255))
    tipo_proyecto = Column(String(100))
    anio_inicio = Column(SmallInteger)
    anio_fin = Column(SmallInteger)
    urlproyecto = Column(Text)
    
    # Foreign Keys - Solo mantener las que tienen clases/tablas definidas
    cod_programa = Column(String(50), ForeignKey("programas.cod_programa"))
    cod_proposito = Column(String(50), ForeignKey("propositos.cod_proposito"))
    cod_reto = Column(String(50), ForeignKey("retos.cod_reto"))
    cod_area_funcional = Column(String(50), ForeignKey("areas_funcionales.cod_area_funcional"))
    cod_centro_gestor = Column(String(50), ForeignKey("centros_gestores.cod_centro_gestor"))
    
    # Campos que serán simples columnas por ahora (sin FK hasta que se definan las tablas)
    cod_linea_estrategica = Column(String(50))
    cod_dimension = Column(String(50))
    cod_sector = Column(String(50))
    cod_fuente_financiamiento = Column(String(50))
    cod_categoria_alcalde = Column(String(50))
    cod_pospre = Column(String(50))
    bp = Column(String(50))
    cod_comuna = Column(String(50))
    cod_actividad = Column(String(50))
    
    # Relaciones - Solo mantener las que tienen clases definidas
    programa = relationship("Programa")
    proposito = relationship("Proposito")
    reto = relationship("Reto")
    area_funcional = relationship("AreaFuncional")
    centro_gestor = relationship("CentroGestor")
    
    # Relaciones comentadas hasta que se definan las clases correspondientes
    # linea_estrategica = relationship("LineaEstrategica", back_populates="proyectos")
    # dimension = relationship("Dimension", back_populates="proyectos")
    # sector = relationship("Sector", back_populates="proyectos")
    # fuente_financiamiento = relationship("FuenteFinanciamiento", back_populates="proyectos")
    # categoria_alcalde = relationship("CategoriaAlcalde", back_populates="proyectos")
    # pospre = relationship("Pospre", back_populates="proyectos")
    # bp_ref = relationship("BP", back_populates="proyectos")
    
    # Relaciones con otras tablas (comentadas temporalmente para simplificar)
    # movimientos_presupuestales = relationship("MovimientoPresupuestal", back_populates="proyecto")
    # ejecucion_presupuestal = relationship("EjecucionPresupuestal", back_populates="proyecto")
    # seguimiento_pa = relationship("SeguimientoPA", back_populates="proyecto")
    # unidades_proyecto = relationship("UnidadProyecto", back_populates="proyecto")
    # contratos = relationship("Contrato", back_populates="proyecto")

class SeguimientoPA(Base):
    __tablename__ = "seguimiento_pa"
    
    id_seguimiento_pa = Column(Integer, primary_key=True, autoincrement=True)
    bpin = Column(BigInteger, nullable=False, index=True)
    cod_actividad = Column(BigInteger, nullable=False)
    cod_producto = Column(BigInteger)  # Permitir nulo
    periodo_corte = Column(String(7), nullable=False)  # YYYY-MM format
    cod_pd_lvl_1 = Column(Integer)
    cod_pd_lvl_2 = Column(Integer)
    cod_pd_lvl_3 = Column(Integer)
    subdireccion_subsecretaria = Column(String(255))
    avance_proyecto_pa = Column(DECIMAL(8, 4))
    ejecucion_ppto_proyecto_pa = Column(DECIMAL(15, 2))
    archivo_origen = Column(String(255))

class SeguimientoActividadPA(Base):
    __tablename__ = "seguimiento_actividades_pa"
    
    id_seguimiento_actividad = Column(Integer, primary_key=True, autoincrement=True)
    bpin = Column(BigInteger, nullable=False, index=True)
    cod_actividad = Column(BigInteger)
    cod_centro_gestor = Column(Integer)
    nombre_actividad = Column(Text)
    descripcion_actividad = Column(Text)
    periodo_corte = Column(String(7), nullable=False)  # YYYY-MM format
    fecha_inicio_actividad = Column(Date)
    fecha_fin_actividad = Column(Date)
    ppto_inicial_actividad = Column(DECIMAL(18, 2))
    ppto_modificado_actividad = Column(DECIMAL(18, 2))
    ejecucion_actividad = Column(DECIMAL(18, 2))
    obligado_actividad = Column(DECIMAL(18, 2))
    pagos_actividad = Column(DECIMAL(18, 2))
    avance_actividad = Column(DECIMAL(5, 2))
    avance_real_actividad = Column(DECIMAL(5, 2))
    avance_actividad_acumulado = Column(DECIMAL(5, 2))
    ponderacion_actividad = Column(DECIMAL(5, 2))
    archivo_origen = Column(String(255))
    
    __table_args__ = (
        UniqueConstraint('bpin', 'cod_actividad', 'periodo_corte', name='uq_seguimiento_actividades_pa_key'),
    )

class SeguimientoProductoPA(Base):
    __tablename__ = "seguimiento_productos_pa"
    
    bpin = Column(BigInteger, primary_key=True, nullable=False, index=True)
    cod_producto = Column(BigInteger, primary_key=True, nullable=False)
    periodo_corte = Column(String(7), primary_key=True, nullable=False)  # YYYY-MM format
    cod_producto_mga = Column(BigInteger)
    nombre_producto = Column(String(500))
    tipo_meta_producto = Column(String(50))
    descripcion_avance_producto = Column(Text)
    cantidad_programada_producto = Column(DECIMAL(15, 2))
    ponderacion_producto = Column(DECIMAL(8, 4))
    avance_producto = Column(DECIMAL(15, 2))
    ejecucion_fisica_producto = Column(DECIMAL(8, 4))
    avance_real_producto = Column(DECIMAL(8, 4))
    avance_producto_acumulado = Column(DECIMAL(8, 4))
    ejecucion_ppto_producto = Column(DECIMAL(15, 2))
    archivo_origen = Column(String(255))

class UnidadProyecto(Base):
    __tablename__ = "unidades_proyecto"
    
    identificador = Column(Integer, primary_key=True, autoincrement=True)
    bpin = Column(String(50), ForeignKey("proyectos.bpin"), nullable=False)
    nickname = Column(String(100))
    nickname_detalle = Column(String(255))
    tipo_proyecto = Column(String(100))
    tipo_unidad_proyecto = Column(String(100))
    clase_obra = Column(String(100))
    subclase_obra = Column(String(100))
    tipo_intervencion = Column(String(100))
    descripcion_intervencion = Column(Text)
    estado_unidad_proyecto = Column(String(50))
    fecha_inicio_planeado = Column(Date)
    fecha_fin_planeado = Column(Date)
    fecha_inicio_real = Column(Date)
    fecha_fin_real = Column(Date)
    es_centro_gravedad = Column(Boolean)
    ppto_base = Column(DECIMAL(18, 2))
    pagos_realizados = Column(DECIMAL(18, 2))
    geom = Column(Text)  # Geometry('POINT', srid=4326) - Cambiado temporalmente a Text
    
    # Relaciones (comentadas temporalmente)
    # proyecto = relationship("Proyecto", back_populates="unidades_proyecto")

class UnidadProyectoInfraestructuraEquipamientos(Base):
    __tablename__ = "unidades_proyecto_infraestructura_equipamientos"
    
    bpin = Column(BigInteger, primary_key=True, index=True)
    identificador = Column(String(255), nullable=False)
    cod_fuente_financiamiento = Column(String(50))
    usuarios_beneficiarios = Column(Float)
    dataframe = Column(Text)
    nickname = Column(String(100))
    nickname_detalle = Column(String(255))
    comuna_corregimiento = Column(String(100))
    barrio_vereda = Column(String(100))
    direccion = Column(String(255))
    clase_obra = Column(String(100))
    subclase_obra = Column(String(100))
    tipo_intervencion = Column(String(100))
    descripcion_intervencion = Column(Text)
    estado_unidad_proyecto = Column(String(50))
    fecha_inicio_planeado = Column(Date)
    fecha_fin_planeado = Column(Date)
    fecha_inicio_real = Column(Date)
    fecha_fin_real = Column(Date)
    es_centro_gravedad = Column(Boolean)
    ppto_base = Column(Float)
    pagos_realizados = Column(Float)
    avance_fisico_obra = Column(Float)
    ejecucion_financiera_obra = Column(Float)
    # Removido: geom - No se almacena en la tabla de atributos

class UnidadProyectoInfraestructuraVial(Base):
    __tablename__ = "unidades_proyecto_infraestructura_vial"
    
    bpin = Column(BigInteger, primary_key=True, index=True)
    identificador = Column(String(255), nullable=False)
    id_via = Column(String(50))
    cod_fuente_financiamiento = Column(String(50))
    usuarios_beneficiarios = Column(Float)
    dataframe = Column(Text)
    nickname = Column(String(100))
    nickname_detalle = Column(String(255))
    comuna_corregimiento = Column(String(100))
    barrio_vereda = Column(String(100))
    direccion = Column(String(255))
    clase_obra = Column(String(100))
    subclase_obra = Column(String(100))
    tipo_intervencion = Column(String(100))
    descripcion_intervencion = Column(Text)
    estado_unidad_proyecto = Column(String(50))
    unidad_medicion = Column(String(50))
    fecha_inicio_planeado = Column(Date)
    fecha_fin_planeado = Column(Date)
    fecha_inicio_real = Column(Date)
    fecha_fin_real = Column(Date)
    es_centro_gravedad = Column(Boolean)
    longitud_proyectada = Column(Float)
    longitud_ejecutada = Column(Float)
    ppto_base = Column(Float)
    pagos_realizados = Column(Float)
    avance_fisico_obra = Column(Float)
    ejecucion_financiera_obra = Column(Float)
    # Removido: geom - No se almacena en la tabla de atributos

# =============================================================================
# Clase: CONTRATO
# =============================================================================

class OrdenadorGasto(Base):
    __tablename__ = "ordenadores_gasto"
    
    cod_ordenador_gasto = Column(String(50), primary_key=True)
    n_documento_ordenador = Column(String(50))
    nombre_ordenador = Column(String(255))

class Supervisor(Base):
    __tablename__ = "supervisores"
    
    cod_supervisor = Column(String(50), primary_key=True)
    n_documento_supervisor = Column(String(50))
    nombre_supervisor = Column(String(255))

# =============================================================================
# Clase: CARTOGRAFIA_BASE
# =============================================================================

class Corregimiento(Base):
    __tablename__ = "corregimientos"
    
    id_corregimiento = Column(String(50), primary_key=True)
    nombre_corregimiento = Column(String(100), nullable=False)
    geom = Column(Text)  # Geometry('MULTIPOLYGON', srid=4326) - Cambiado temporalmente a Text

class Comuna(Base):
    __tablename__ = "comunas"
    
    id_comuna = Column(String(50), primary_key=True)
    nombre_comuna = Column(String(100), nullable=False)
    geom = Column(Text)  # Geometry('MULTIPOLYGON', srid=4326) - Cambiado temporalmente a Text

class Vereda(Base):
    __tablename__ = "veredas"
    
    id_vereda = Column(String(50), primary_key=True)
    nombre_vereda = Column(String(100), nullable=False)
    geom = Column(Text)  # Geometry('MULTIPOLYGON', srid=4326) - Cambiado temporalmente a Text

class Barrio(Base):
    __tablename__ = "barrios"
    
    id_barrio = Column(String(50), primary_key=True)
    nombre_barrio = Column(String(100), nullable=False)
    estrato_barrio = Column(SmallInteger)
    geom = Column(Text)  # Geometry('MULTIPOLYGON', srid=4326) - Cambiado temporalmente a Text

class Equipamiento(Base):
    __tablename__ = "equipamientos"
    
    id_equipamiento = Column(String(50), primary_key=True)
    nombre_equipamiento = Column(String(255), nullable=False)
    servicio_equipamiento = Column(String(100))
    escala_equipamiento = Column(String(100))
    geom = Column(Text)  # Geometry('POINT', srid=4326) - Cambiado temporalmente a Text

class Via(Base):
    __tablename__ = "vias"
    
    id_via = Column(String(50), primary_key=True)
    nombre_via = Column(String(255))
    longitud_via = Column(DECIMAL(10, 2))
    geom = Column(Text)  # Geometry('MULTILINESTRING', srid=4326) - Cambiado temporalmente a Text

# =============================================================================
# Mantener el modelo original para compatibilidad hacia atrás
# =============================================================================

class ProjectExecution(Base):
    __tablename__ = "project_execution"

    id = Column(Integer, primary_key=True, index=True)
    bpin = Column(String, index=True)
    adiciones = Column(Float)
    anio = Column(Integer)
    aplazamiento = Column(Float)
    area_funcional = Column(String)
    bp = Column(String)
    centro_gestor = Column(String)
    clasificacion_fondo = Column(String)
    comuna = Column(String)
    contracreditos = Column(Float)
    creditos = Column(Float)
    dataframe_origen = Column(String)
    desaplazamiento = Column(Float)
    dimension = Column(String)
    ejecucion = Column(Float)
    fondo = Column(String)
    linea_estrategica = Column(String)
    nombre_actividad = Column(String)
    nombre_area_funcional = Column(String)
    nombre_centro_gestor = Column(String)
    nombre_dimension = Column(String)
    nombre_fondo = Column(String)
    nombre_linea_estrategica = Column(String)
    nombre_pospre = Column(String)
    nombre_programa = Column(String)
    nombre_proyecto = Column(String)
    organismo = Column(String)
    origen = Column(String)
    pagos = Column(Float)
    periodo = Column(Date)
    pospre = Column(String)
    ppto_disponible = Column(Float)
    ppto_inicial = Column(Float)
    ppto_modificado = Column(Float)
    programa_presupuestal = Column(String)
    reducciones = Column(Float)
    saldos_cdp = Column(Float)
    tipo_gasto = Column(String)
    total_acumul_obligac = Column(Float)
    total_acumulado_cdp = Column(Float)
    total_acumulado_rpc = Column(Float)
    vigencia = Column(Integer)

# =============================================================================
# CONTRATOS SECOP - Sistema optimizado con arquitectura BPIN-centric
# =============================================================================

class Contrato(Base):
    __tablename__ = "contratos"

    bpin = Column(BigInteger, primary_key=True, index=True, doc="Código BPIN del proyecto")
    cod_contrato = Column(String(100), primary_key=True, index=True, doc="Código único del contrato")
    nombre_proyecto = Column(Text, nullable=True, doc="Nombre completo del proyecto")
    descripcion_contrato = Column(Text, nullable=True, doc="Descripción del objeto contractual")
    estado_contrato = Column(String(50), nullable=True, doc="Estado actual del contrato")
    codigo_proveedor = Column(String(50), nullable=True, doc="Código de identificación del proveedor")
    proveedor = Column(Text, nullable=True, doc="Nombre completo del proveedor/contratista")
    url_contrato = Column(Text, nullable=True, doc="URL del contrato en el sistema SECOP")
    fecha_actualizacion = Column(Date, nullable=True, doc="Fecha de última actualización de datos")

class ContratoValor(Base):
    __tablename__ = "contratos_valores"

    bpin = Column(BigInteger, primary_key=True, index=True, doc="Código BPIN del proyecto")
    cod_contrato = Column(String(100), primary_key=True, index=True, doc="Código único del contrato")
    valor_contrato = Column(DECIMAL(15, 2), nullable=True, doc="Valor total del contrato en pesos colombianos")
