"""
Pydantic schemas defining request/response contracts for FastAPI endpoints.

Keep schemas aligned with models; avoid geometry fields in attribute tables.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

# =============================================================================
# Esquemas para Tablas de Dimensiones (Catálogos)
# =============================================================================

class CentroGestor(BaseModel):
    cod_centro_gestor: int
    nombre_centro_gestor: str
    
class Programa(BaseModel):
    cod_programa: int
    nombre_programa: str
    
class AreaFuncional(BaseModel):
    cod_area_funcional: int
    nombre_area_funcional: str
    
class Proposito(BaseModel):
    cod_proposito: int
    nombre_proposito: str
    
class Reto(BaseModel):
    cod_reto: int
    nombre_reto: str
    
class MovimientoPresupuestal(BaseModel):
    bpin:int
    ppto_inicial:float
    adiciones:float
    reducciones:float
    ppto_modificado:float
    periodo_corte:str
    
class EjecucionPresupuestal(BaseModel):
    bpin:int
    ejecucion:float
    pagos:float
    saldos_cdp:float
    total_acumul_obligac:float
    total_acumulado_cdp:float
    total_acumulado_rpc:float
    periodo_corte:str

# =============================================================================
# PROYECTO: SEGUIMIENTO AL PLAN DE ACCIÓN - Esquemas Pydantic
# =============================================================================

class SeguimientoActividadPA(BaseModel):
    bpin: int
    cod_actividad: Optional[int] = None
    cod_centro_gestor: Optional[int] = None
    nombre_actividad: Optional[str] = None
    descripcion_actividad: Optional[str] = None
    periodo_corte: Optional[str] = None
    fecha_inicio_actividad: Optional[date] = None
    fecha_fin_actividad: Optional[date] = None
    ppto_inicial_actividad: Optional[float] = None
    ppto_modificado_actividad: Optional[float] = None
    ejecucion_actividad: Optional[float] = None
    obligado_actividad: Optional[float] = None
    pagos_actividad: Optional[float] = None
    avance_actividad: Optional[float] = None
    avance_real_actividad: Optional[float] = None
    avance_actividad_acumulado: Optional[float] = None
    ponderacion_actividad: Optional[float] = None
    archivo_origen: Optional[str] = None
    
    class Config:
        from_attributes = True

class SeguimientoProductoPA(BaseModel):
    bpin: int
    cod_producto: Optional[int] = None
    cod_producto_mga: Optional[int] = None
    nombre_producto: Optional[str] = None
    tipo_meta_producto: Optional[str] = None
    descripcion_avance_producto: Optional[str] = None
    periodo_corte: Optional[str] = None
    cantidad_programada_producto: Optional[float] = None
    ponderacion_producto: Optional[float] = None
    avance_producto: Optional[float] = None
    ejecucion_fisica_producto: Optional[float] = None
    avance_real_producto: Optional[float] = None
    avance_producto_acumulado: Optional[float] = None
    ejecucion_ppto_producto: Optional[float] = None
    archivo_origen: Optional[str] = None
    
    class Config:
        from_attributes = True

class SeguimientoPA(BaseModel):
    bpin: int
    cod_pd_lvl_1: Optional[int] = None
    cod_pd_lvl_2: Optional[int] = None
    cod_pd_lvl_3: Optional[int] = None
    cod_actividad: Optional[int] = None
    cod_producto: Optional[int] = None
    subdireccion_subsecretaria: Optional[str] = None
    periodo_corte: Optional[str] = None
    avance_proyecto_pa: Optional[float] = None
    ejecucion_ppto_proyecto_pa: Optional[float] = None
    archivo_origen: Optional[str] = None
    
    class Config:
        from_attributes = True

# =============================================================================
# Esquemas para Clase: PROYECTO
# =============================================================================

class UnidadProyectoInfraestructuraEquipamientos(BaseModel):
    identificador: str
    bpin: Optional[int] = None
    cod_fuente_financiamiento: Optional[str] = None
    usuarios_beneficiarios: Optional[float] = None
    dataframe: Optional[str] = None
    nickname: Optional[str] = None
    nickname_detalle: Optional[str] = None
    comuna_corregimiento: Optional[str] = None
    barrio_vereda: Optional[str] = None
    direccion: Optional[str] = None
    clase_obra: Optional[str] = None
    subclase_obra: Optional[str] = None
    tipo_intervencion: Optional[str] = None
    descripcion_intervencion: Optional[str] = None
    estado_unidad_proyecto: Optional[str] = None
    fecha_inicio_planeado: Optional[date] = None
    fecha_fin_planeado: Optional[date] = None
    fecha_inicio_real: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    es_centro_gravedad: Optional[bool] = None
    ppto_base: Optional[float] = None
    pagos_realizados: Optional[float] = None
    avance_fisico_obra: Optional[float] = None
    ejecucion_financiera_obra: Optional[float] = None
    # Removido: geom - No se incluye en los datos JSON de tabla de atributos
    
    class Config:
        from_attributes = True

class UnidadProyectoInfraestructuraVial(BaseModel):
    identificador: str
    bpin: Optional[int] = None
    id_via: Optional[str] = None
    cod_fuente_financiamiento: Optional[str] = None
    usuarios_beneficiarios: Optional[float] = None
    dataframe: Optional[str] = None
    nickname: Optional[str] = None
    nickname_detalle: Optional[str] = None
    comuna_corregimiento: Optional[str] = None
    barrio_vereda: Optional[str] = None
    direccion: Optional[str] = None
    clase_obra: Optional[str] = None
    subclase_obra: Optional[str] = None
    tipo_intervencion: Optional[str] = None
    descripcion_intervencion: Optional[str] = None
    estado_unidad_proyecto: Optional[str] = None
    unidad_medicion: Optional[str] = None
    fecha_inicio_planeado: Optional[date] = None
    fecha_fin_planeado: Optional[date] = None
    fecha_inicio_real: Optional[date] = None
    fecha_fin_real: Optional[date] = None
    es_centro_gravedad: Optional[bool] = None
    longitud_proyectada: Optional[float] = None
    longitud_ejecutada: Optional[float] = None
    ppto_base: Optional[float] = None
    pagos_realizados: Optional[float] = None
    avance_fisico_obra: Optional[float] = None
    ejecucion_financiera_obra: Optional[float] = None
    # Removido: geom - No se incluye en los datos JSON de tabla de atributos
    
    class Config:
        from_attributes = True

# =============================================================================
# Esquemas para Contratos SECOP - Sistema optimizado BPIN-centric
# =============================================================================

class Contrato(BaseModel):
    bpin: int
    cod_contrato: str
    nombre_proyecto: Optional[str] = None
    descripcion_contrato: Optional[str] = None
    estado_contrato: Optional[str] = None
    codigo_proveedor: Optional[str] = None
    proveedor: Optional[str] = None
    url_contrato: Optional[str] = None
    fecha_actualizacion: Optional[date] = None
    
    class Config:
        from_attributes = True

class ContratoValor(BaseModel):
    bpin: int
    cod_contrato: str
    valor_contrato: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

class ContratoCompleto(BaseModel):
    """Esquema para respuesta GET con información de centro gestor"""
    bpin: int
    cod_contrato: str
    nombre_proyecto: Optional[str] = None
    descripcion_contrato: Optional[str] = None
    estado_contrato: Optional[str] = None
    codigo_proveedor: Optional[str] = None
    proveedor: Optional[str] = None
    url_contrato: Optional[str] = None
    fecha_actualizacion: Optional[date] = None
    valor_contrato: Optional[Decimal] = None
    cod_centro_gestor: Optional[int] = None
    nombre_centro_gestor: Optional[str] = None
    
    class Config:
        from_attributes = True

