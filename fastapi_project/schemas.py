from pydantic import BaseModel
from typing import Optional
from datetime import date

class ProjectExecutionBase(BaseModel):
    bpin: Optional[str] = None
    adiciones: Optional[float] = None
    anio: Optional[int] = None
    aplazamiento: Optional[float] = None
    area_funcional: Optional[str] = None
    bp: Optional[str] = None
    centro_gestor: Optional[str] = None
    clasificacion_fondo: Optional[str] = None
    comuna: Optional[str] = None
    contracreditos: Optional[float] = None
    creditos: Optional[float] = None
    dataframe_origen: Optional[str] = None
    desaplazamiento: Optional[float] = None
    dimension: Optional[str] = None
    ejecucion: Optional[float] = None
    fondo: Optional[str] = None
    linea_estrategica: Optional[str] = None
    nombre_actividad: Optional[str] = None
    nombre_area_funcional: Optional[str] = None
    nombre_centro_gestor: Optional[str] = None
    nombre_dimension: Optional[str] = None
    nombre_fondo: Optional[str] = None
    nombre_linea_estrategica: Optional[str] = None
    nombre_pospre: Optional[str] = None
    nombre_programa: Optional[str] = None
    nombre_proyecto: Optional[str] = None
    organismo: Optional[str] = None
    origen: Optional[str] = None
    pagos: Optional[float] = None
    periodo: Optional[date] = None
    pospre: Optional[str] = None
    ppto_disponible: Optional[float] = None
    ppto_inicial: Optional[float] = None
    ppto_modificado: Optional[float] = None
    programa_presupuestal: Optional[str] = None
    reducciones: Optional[float] = None
    saldos_cdp: Optional[float] = None
    tipo_gasto: Optional[str] = None
    total_acumul_obligac: Optional[float] = None
    total_acumulado_cdp: Optional[float] = None
    total_acumulado_rpc: Optional[float] = None
    vigencia: Optional[int] = None

class ProjectExecutionCreate(ProjectExecutionBase):
    pass

class ProjectExecution(ProjectExecutionBase):
    id: int

    class Config:
        from_attributes = True
