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

