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

