# -*- coding: utf-8 -*-
"""
Módulo de transformación de datos para procesamiento de contratos.
Usa fuentes BPIN como datos primarios e integra con datos SECOP II y PAA.
"""

import os
import pandas as pd
import json
from typing import Optional, Dict, Tuple, List
import re
from tqdm import tqdm
import time
import numpy as np


def normalize_column_names(df):
    """
    Normaliza nombres de columnas convirtiéndolas a minúsculas y eliminando caracteres especiales.
    """
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('ñ', 'n').str.replace('ó', 'o').str.replace('ú', 'u').str.replace('í', 'i').str.replace('é', 'e').str.replace('á', 'a')
    return df


def clean_numeric_value(value):
    """
    Limpia y convierte valores numéricos, manejando varios formatos.
    """
    if pd.isna(value) or value is None:
        return None
    
    try:
        str_value = str(value).strip()
        if str_value.lower() in ['', 'nan', 'none', 'null', 'no definido']:
            return None
            
        # Eliminar símbolos de moneda, comas y espacios
        cleaned = re.sub(r'[^\d.-]', '', str_value)
        if cleaned == '' or cleaned == '-':
            return None
            
        result = float(cleaned)
        # Verificar si el resultado es NaN o infinito
        if np.isnan(result) or np.isinf(result):
            return None
            
        return result
    except:
        return None


def clean_date_value(value):
    """
    Limpia y estandariza valores de fecha.
    """
    if pd.isna(value) or value is None:
        return None
    
    try:
        str_value = str(value).strip()
        if str_value.lower() in ['', 'nan', 'none', 'null']:
            return None
        
        date_obj = pd.to_datetime(str_value, errors='coerce')
        if pd.isna(date_obj):
            return None
            
        return date_obj.strftime('%Y-%m-%d')
    except:
        return None


def clean_integer_value(value):
    """
    Limpia y convierte a entero, asegurando que no haya decimales.
    """
    if pd.isna(value) or value is None:
        return None
    
    try:
        # Manejar valores de texto
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ['', 'nan', 'none', 'null', 'no definido']:
                return None
        
        # Convertir a float primero, luego a int
        float_val = float(value)
        if pd.isna(float_val) or np.isnan(float_val) or np.isinf(float_val):
            return None
            
        return int(float_val)
    except:
        return None


def clean_nan_values(obj):
    """
    Limpia recursivamente todos los valores NaN, None y strings vacíos de un objeto.
    Convierte NaN a None para compatibilidad con JSON.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            cleaned_value = clean_nan_values(value)
            if cleaned_value is not None and cleaned_value != "" and not (isinstance(cleaned_value, float) and np.isnan(cleaned_value)):
                cleaned[key] = cleaned_value
        return cleaned
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj if item is not None and item != "" and not (isinstance(item, float) and np.isnan(item))]
    elif pd.isna(obj) or obj is None or obj == "" or (isinstance(obj, float) and np.isnan(obj)):
        return None
    elif isinstance(obj, str) and obj.lower().strip() in ['nan', 'none', 'null', 'no definido', '']:
        return None
    else:
        return obj


def clean_record_for_json(record):
    """
    Limpia un registro individual para exportación JSON, eliminando valores problemáticos y redundancias.
    """
    cleaned_record = {}
    
    # Campos que queremos eliminar (duplicados y no deseados)
    campos_a_eliminar = {
        'CodigoBPIN', 'Proveedor', 'Fuente', 'FechaActualizacionFuentePlaneacion', 
        'FechaActualizacionFuenteComprasPublicas', 'EstadoContrato', 'MonedaContrato', 
        'NombreProyecto', 'CodigoProceso', 'CodigoContrato', 'DescripcionContrato', 
        'UrlContrato', 'cod_centro_gestor'
    }
    
    # Valores comunes que podemos omitir si son estándar
    valores_comunes = {
        'fuente': 'Dpto. Administrativo de Planeación y Contratación Pública - Alcaldía de Santiago de Cali',
        'moneda_contrato': 'COP',
        'moneda': 'COP'
    }
    
    for key, value in record.items():
        # Saltar campos que queremos eliminar
        if key in campos_a_eliminar:
            continue
            
        # Limpiar valores NaN y None
        if pd.isna(value) or value is None:
            continue  # Omitir campos con valores nulos
        
        # Limpiar strings vacíos o problemáticos
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ['nan', 'none', 'null', 'no definido', '']:
                continue  # Omitir campos vacíos
        
        # Optimizar campos con valores comunes (solo incluir si son diferentes)
        if key in valores_comunes and str(value) == valores_comunes[key]:
            continue  # Omitir valores estándar para reducir tamaño
        
        # Limpiar valores numéricos problemáticos
        if isinstance(value, float):
            if np.isnan(value) or np.isinf(value):
                continue  # Omitir NaN o infinitos
            # Convertir floats enteros a int
            if value.is_integer():
                value = int(value)
        
        # Optimizar códigos duplicados: si cod_contrato == cod_proceso, solo guardar uno
        if key == 'cod_proceso' and 'cod_contrato' in record and str(record['cod_contrato']) == str(value):
            continue  # Omitir cod_proceso si es igual a cod_contrato
        
        cleaned_record[key] = value
    
    return cleaned_record


def optimize_record_structure(record):
    """
    Optimiza la estructura del registro para reducir redundancias manteniendo integridad.
    """
    optimized = record.copy()
    
    # Si fecha_actualizacion_planeacion == fecha_actualizacion_compras, solo mantener una
    if ('fecha_actualizacion_planeacion' in optimized and 
        'fecha_actualizacion_compras' in optimized and
        optimized['fecha_actualizacion_planeacion'] == optimized['fecha_actualizacion_compras']):
        optimized['fecha_actualizacion'] = optimized['fecha_actualizacion_planeacion']
        del optimized['fecha_actualizacion_planeacion']
        del optimized['fecha_actualizacion_compras']
    
    # Consolidar monedas: si todas son COP, asumir COP por defecto
    if optimized.get('moneda_contrato') == 'COP':
        del optimized['moneda_contrato']
    if optimized.get('moneda') == 'COP':
        del optimized['moneda']
    
    return optimized


def load_primary_bpin_data(data_directory: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carga fuentes de datos BPIN primarios.
    """
    print("📥 Cargando fuentes de datos BPIN primarios...")
    
    with tqdm(total=2, desc="🔄 Cargando archivos BPIN", unit="archivo") as pbar:
        # Cargar contratos BPIN
        contratos_bpin_path = os.path.join(data_directory, "DatosAbiertosContratosXProyectosInv.csv")
        df_contratos_bpin = pd.read_csv(contratos_bpin_path, encoding='utf-8')
        pbar.set_postfix_str(f"Contratos BPIN: {len(df_contratos_bpin):,} registros")
        pbar.update(1)
        time.sleep(0.1)  # Pequeña pausa para ver la barra
        
        # Cargar procesos BPIN  
        procesos_bpin_path = os.path.join(data_directory, "DatosAbiertosProcesosXProyectosInv.csv")
        df_procesos_bpin = pd.read_csv(procesos_bpin_path, encoding='utf-8')
        pbar.set_postfix_str(f"Procesos BPIN: {len(df_procesos_bpin):,} registros")
        pbar.update(1)
        time.sleep(0.1)
    
    print(f"✅ Contratos BPIN cargados: {len(df_contratos_bpin):,} registros")
    print(f"✅ Procesos BPIN cargados: {len(df_procesos_bpin):,} registros")
    
    return df_contratos_bpin, df_procesos_bpin


def load_secondary_data(data_directory: str) -> pd.DataFrame:
    """
    Carga fuentes de datos secundarios para enriquecimiento (solo PAA).
    """
    print("\n📥 Cargando fuente de datos secundarios...")
    
    with tqdm(total=1, desc="🔄 Cargando archivo PAA", unit="archivo") as pbar:
        # Cargar datos PAA
        paa_path = os.path.join(data_directory, "DACP W-31 PAA BD.xlsx")
        df_paa = pd.read_excel(paa_path)
        df_paa = normalize_column_names(df_paa)
        pbar.set_postfix_str(f"PAA: {len(df_paa):,} registros")
        pbar.update(1)
        time.sleep(0.1)
    
    print(f"✅ PAA cargado: {len(df_paa):,} registros")
    
    return df_paa


def create_integration_mappings(df_paa: pd.DataFrame) -> Dict[str, Dict]:
    """
    Crea mapeos para integración de datos usando solo PAA.
    """
    print("\n🔗 Creando mapeos de integración...")
    
    mappings = {
        'paa_by_codigo': {},
        'paa_by_nombre': {}
    }
    
    # Mapeos PAA
    print("📋 Procesando mapeos PAA...")
    with tqdm(total=len(df_paa), desc="🔄 Procesando PAA", unit="registro") as pbar:
        for _, row in df_paa.iterrows():
            # Por código (si existe)
            codigo_cols = [col for col in df_paa.columns if 'codigo' in col.lower()]
            for col in codigo_cols:
                if pd.notna(row[col]):
                    mappings['paa_by_codigo'][str(row[col])] = row.to_dict()
            
            # Por nombre proyecto (si existe)
            nombre_cols = [col for col in df_paa.columns if 'nombre' in col.lower() or 'proyecto' in col.lower()]
            for col in nombre_cols:
                if pd.notna(row[col]):
                    mappings['paa_by_nombre'][str(row[col]).lower()] = row.to_dict()
            
            pbar.update(1)
    
    print(f"✅ Creados {len(mappings['paa_by_codigo']):,} mapeos de código PAA")
    print(f"✅ Creados {len(mappings['paa_by_nombre']):,} mapeos de nombre PAA")
    
    return mappings


def enrich_contract_data(contract_row: dict, mappings: Dict[str, Dict]) -> dict:
    """
    Enriquece datos de contrato con información de fuentes PAA.
    """
    enriched = contract_row.copy()
    
    # Intentar encontrar datos PAA por coincidencia de nombre de proyecto
    if 'NombreProyecto' in contract_row:
        nombre_proyecto = str(contract_row['NombreProyecto']).lower()
        paa_data = mappings['paa_by_nombre'].get(nombre_proyecto)
        
        if paa_data:
            # Añadir campos PAA
            paa_fields = {}
            for col, value in paa_data.items():
                if value is not None and pd.notna(value):
                    paa_fields[f'paa_{col}'] = value
            
            enriched.update(paa_fields)
    
    return enriched


def contratos_transformer(data_directory: str = "transformation_app/app_inputs/contratos_secop_input") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transforma datos de contratos usando fuentes BPIN como datos primarios.
    
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: contratos, contratos_valores
    """
    
    try:
        print("=" * 70)
        print("🏗️  TRANSFORMACIÓN DE CONTRATOS CON BPIN COMO FUENTE PRIMARIA")
        print("=" * 70)
        
        # Cargar datos BPIN primarios
        df_contratos_bpin, df_procesos_bpin = load_primary_bpin_data(data_directory)
        
        # Cargar datos secundarios (solo PAA)
        df_paa = load_secondary_data(data_directory)
        
        # Crear mapeos de integración
        mappings = create_integration_mappings(df_paa)
        
        print("\n🔄 Procesando datos de contratos...")
        
        # Combinar fuentes de datos BPIN
        contratos_data = []
        valores_data = []
        
        # Procesar datos de contratos BPIN
        print("📋 Procesando registros de contratos BPIN...")
        with tqdm(total=len(df_contratos_bpin), desc="🔄 Contratos BPIN", unit="contrato") as pbar:
            for _, row in df_contratos_bpin.iterrows():
                # Asegurar BPIN válido
                bpin = clean_integer_value(row.get('CodigoBPIN'))
                if bpin is None:
                    pbar.update(1)
                    continue
                
                # Crear registro base de contrato
                contract_record = {
                    'bpin': bpin,
                    'cod_contrato': str(row.get('CodigoContrato', '')),
                    'cod_proceso': str(row.get('CodigoProceso', '')),
                    'nombre_proyecto': row.get('NombreProyecto', ''),
                    'descripcion_contrato': row.get('DescripcionContrato', ''),
                    'estado_contrato': row.get('EstadoContrato', ''),
                    'moneda_contrato': row.get('MonedaContrato', ''),
                    'codigo_proveedor': str(row.get('CodigoProveedor', '')),
                    'proveedor': row.get('Proveedor', ''),
                    'url_contrato': row.get('UrlContrato', ''),
                    'fuente': row.get('Fuente', ''),
                    'fecha_actualizacion_planeacion': clean_date_value(row.get('FechaActualizacionFuentePlaneacion')),
                    'fecha_actualizacion_compras': clean_date_value(row.get('FechaActualizacionFuenteComprasPublicas'))
                }
                
                # Enriquecer con datos secundarios
                enriched_contract = enrich_contract_data(row.to_dict(), mappings)
                
                # Solo añadir campos PAA del enriquecimiento
                for k, v in enriched_contract.items():
                    if k.startswith('paa_') and k not in contract_record:
                        contract_record[k] = v
                
                contratos_data.append(contract_record)
                
                # Crear registro de valores
                valor_record = {
                    'bpin': bpin,
                    'cod_contrato': contract_record['cod_contrato'],
                    'valor_contrato': clean_numeric_value(row.get('ValorContrato')),
                    'moneda': row.get('MonedaContrato', 'COP')
                }
                
                valores_data.append(valor_record)
                pbar.update(1)
        
        # Procesar datos de procesos BPIN (para proyectos adicionales no en contratos)
        print("📋 Procesando registros de procesos BPIN...")
        existing_bpins = {record['bpin'] for record in contratos_data}
        
        with tqdm(total=len(df_procesos_bpin), desc="🔄 Procesos BPIN", unit="proceso") as pbar:
            for _, row in df_procesos_bpin.iterrows():
                # Asegurar BPIN válido
                bpin = clean_integer_value(row.get('CodigoBPIN'))
                if bpin is None or bpin in existing_bpins:
                    pbar.update(1)
                    continue
                
                # Crear registro base de proyecto
                project_record = {
                    'bpin': bpin,
                    'cod_contrato': None,
                    'cod_proceso': str(row.get('CodigoProceso', '')),
                    'nombre_proyecto': row.get('NombreProyecto', ''),
                    'descripcion_proyecto': row.get('DescripcionProyecto', ''),
                    'entidad_ejecutora': row.get('EntidadEjecutora', ''),
                    'fecha_inicio': clean_date_value(row.get('FechaInicio')),
                    'fecha_fin': clean_date_value(row.get('FechaFin')),
                    'fuente': row.get('Fuente', ''),
                    'fecha_actualizacion': clean_date_value(row.get('FechaActualizacion'))
                }
                
                # Enriquecer con datos secundarios
                enriched_project = enrich_contract_data(row.to_dict(), mappings)
                
                # Solo añadir campos PAA del enriquecimiento
                for k, v in enriched_project.items():
                    if k.startswith('paa_') and k not in project_record:
                        project_record[k] = v
                
                contratos_data.append(project_record)
                
                # Crear registro de valores
                valor_record = {
                    'bpin': bpin,
                    'cod_contrato': None,
                    'valor_proyecto': clean_numeric_value(row.get('ValorProyecto')),
                    'presupuesto': clean_numeric_value(row.get('Presupuesto')),
                    'moneda': 'COP'
                }
                
                valores_data.append(valor_record)
                pbar.update(1)
        
        # Crear DataFrames
        print("\n📊 Creando DataFrames finales...")
        contratos_df = pd.DataFrame(contratos_data)
        valores_df = pd.DataFrame(valores_data)
        
        # Eliminar duplicados por BPIN
        contratos_df = contratos_df.drop_duplicates(subset=['bpin'], keep='first')
        valores_df = valores_df.drop_duplicates(subset=['bpin'], keep='first')
        
        print(f"\n✅ DataFrame contratos creado: {len(contratos_df):,} registros")
        print(f"✅ DataFrame valores creado: {len(valores_df):,} registros")
        
        # Imprimir resumen
        valid_bpins = contratos_df['bpin'].notna().sum()
        
        print("\n" + "=" * 70)
        print("📈 RESUMEN DE TRANSFORMACIÓN")
        print("=" * 70)
        print(f"📝 Total de registros procesados: {len(contratos_df):,}")
        print(f"🎯 Registros con BPIN válido: {valid_bpins:,} (100%)")
        print(f"🔢 BPINs únicos: {contratos_df['bpin'].nunique():,}")
        print("=" * 70)
        
        return contratos_df, valores_df
        
    except Exception as e:
        print(f"❌ Error en transformación: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def save_dataframes_to_json(contratos_df, valores_df, output_directory: str = "transformation_app/app_outputs/contratos_secop_output"):
    """
    Guarda los dataframes como archivos JSON.
    """
    try:
        os.makedirs(output_directory, exist_ok=True)
        
        print("\n💾 Guardando archivos JSON...")
        
        # Convertir DataFrames a formato de registros para JSON
        contratos_records = contratos_df.to_dict('records')
        valores_records = valores_df.to_dict('records')
        
        # Limpiar campos enteros y valores problemáticos
        print("🔧 Optimizando y limpiando datos para exportación JSON...")
        cleaned_contratos = []
        with tqdm(total=len(contratos_records), desc="🔄 Optimizando contratos", unit="registro") as pbar:
            for record in contratos_records:
                # Limpiar el registro completo
                cleaned_record = clean_record_for_json(record)
                
                # Optimizar estructura
                optimized_record = optimize_record_structure(cleaned_record)
                
                # Asegurar que campos específicos sean enteros si existen
                if 'bpin' in optimized_record and optimized_record['bpin'] is not None:
                    optimized_record['bpin'] = clean_integer_value(optimized_record['bpin'])
                
                cleaned_contratos.append(optimized_record)
                pbar.update(1)
        
        cleaned_valores = []
        with tqdm(total=len(valores_records), desc="🔄 Optimizando valores", unit="registro") as pbar:
            for record in valores_records:
                # Limpiar el registro completo
                cleaned_record = clean_record_for_json(record)
                
                # Optimizar estructura
                optimized_record = optimize_record_structure(cleaned_record)
                
                # Asegurar que BPIN sea entero si existe
                if 'bpin' in optimized_record and optimized_record['bpin'] is not None:
                    optimized_record['bpin'] = clean_integer_value(optimized_record['bpin'])
                
                cleaned_valores.append(optimized_record)
                pbar.update(1)
        
        # Guardar archivos
        files_saved = []
        
        # Crear metadata para documentar optimizaciones
        metadata = {
            "_metadata": {
                "version": "2.0",
                "optimized": True,
                "fecha_generacion": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_registros": len(cleaned_contratos),
                "optimizaciones": [
                    "Eliminados valores NaN/null",
                    "Removidos campos duplicados", 
                    "Consolidadas fechas de actualización",
                    "Omitida moneda COP por defecto",
                    "Eliminados cod_proceso duplicados"
                ],
                "nota": "Moneda por defecto: COP. cod_proceso omitido cuando == cod_contrato"
            }
        }
        
        print("💾 Guardando archivos optimizados...")
        with tqdm(total=2, desc="🔄 Guardando", unit="archivo") as pbar:
            contratos_path = os.path.join(output_directory, "contratos.json")
            with open(contratos_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_contratos, f, ensure_ascii=False, indent=2, default=str, allow_nan=False)
            files_saved.append("contratos.json")
            pbar.set_postfix_str("contratos.json")
            pbar.update(1)
            
            valores_path = os.path.join(output_directory, "contratos_valores.json")
            with open(valores_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_valores, f, ensure_ascii=False, indent=2, default=str, allow_nan=False)
            files_saved.append("contratos_valores.json")
            pbar.set_postfix_str("contratos_valores.json")
            pbar.update(1)
            
            # ❌ ELIMINADO: contratos_unified.json es redundante con contratos.json
            # Se optimizó para evitar duplicación de datos
        
        print(f"\n✅ Se guardaron exitosamente {len(files_saved)} archivos en: {output_directory}")
        for file in files_saved:
            file_path = os.path.join(output_directory, file)
            size_kb = os.path.getsize(file_path) / 1024
            print(f"  📄 {file} ({size_kb:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error guardando archivos: {e}")
        import traceback
        traceback.print_exc()
        return False


def extract_cod_centro_gestor(referencia):
    """
    Extract cod_centro_gestor from first 4 digits of referencia_del_proceso.
    Returns integer without decimals.
    """
    if pd.isna(referencia):
        return None
    
    ref_str = str(referencia).strip()
    # Extract first 4 numeric digits
    match = re.match(r'^(\d{4})', ref_str)
    if match:
        return int(match.group(1))
    return None


def create_bpin_mapping(df_contratos_bpin, df_procesos_bpin) -> Dict[str, int]:
    """
    Create a comprehensive BPIN mapping from both BPIN sources.
    Returns dictionary mapping process/contract codes to BPIN values.
    """
    bpin_mapping = {}
    
    # Process contratos BPIN file
    if df_contratos_bpin is not None:
        print(f"Processing contratos BPIN file with {len(df_contratos_bpin)} records")
        
        # Map CodigoProceso -> CodigoBPIN
        for _, row in df_contratos_bpin.iterrows():
            codigo_proceso = str(row['CodigoProceso']).strip()
            codigo_contrato = str(row['CodigoContrato']).strip()
            codigo_bpin = row['CodigoBPIN']
            
            # Ensure BPIN is integer
            try:
                bpin_int = int(codigo_bpin)
                bpin_mapping[codigo_proceso] = bpin_int
                bpin_mapping[codigo_contrato] = bpin_int
            except:
                continue
    
    # Process procesos BPIN file
    if df_procesos_bpin is not None:
        print(f"Processing procesos BPIN file with {len(df_procesos_bpin)} records")
        
        # Map CodigoProceso -> CodigoBPIN
        for _, row in df_procesos_bpin.iterrows():
            codigo_proceso = str(row['CodigoProceso']).strip()
            codigo_bpin = row['CodigoBPIN']
            
            # Ensure BPIN is integer
            try:
                bpin_int = int(codigo_bpin)
                bpin_mapping[codigo_proceso] = bpin_int
            except:
                continue
    
    print(f"Created BPIN mapping with {len(bpin_mapping)} entries")
    return bpin_mapping


def map_bpin_to_contracts(df_main, bpin_mapping) -> pd.DataFrame:
    """
    Map BPIN values to contracts using multiple strategies.
    """
    df_result = df_main.copy()
    df_result['bpin'] = None
    
    total_mapped = 0
    
    # Strategy 1: Use id_del_portafolio
    if 'id_del_portafolio' in df_result.columns:
        for idx, row in df_result.iterrows():
            portafolio = str(row['id_del_portafolio']).strip()
            if portafolio in bpin_mapping:
                df_result.at[idx, 'bpin'] = bpin_mapping[portafolio]
                total_mapped += 1
    
    # Strategy 2: Use id_del_proceso
    if 'id_del_proceso' in df_result.columns:
        for idx, row in df_result.iterrows():
            if pd.isna(df_result.at[idx, 'bpin']):  # Only if not already mapped
                proceso = str(row['id_del_proceso']).strip()
                if proceso in bpin_mapping:
                    df_result.at[idx, 'bpin'] = bpin_mapping[proceso]
                    total_mapped += 1
    
    # Strategy 3: Use referencia_del_proceso
    if 'referencia_del_proceso' in df_result.columns:
        for idx, row in df_result.iterrows():
            if pd.isna(df_result.at[idx, 'bpin']):  # Only if not already mapped
                referencia = str(row['referencia_del_proceso']).strip()
                if referencia in bpin_mapping:
                    df_result.at[idx, 'bpin'] = bpin_mapping[referencia]
                    total_mapped += 1
    
    print(f"Successfully mapped BPIN to {total_mapped} contracts")
    return df_result


def contratos_secop_transformer(data_directory: str = "transformation_app/app_inputs/contratos_secop_input") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Transform SECOP contracts data integrating with BPIN mapping sources.
    
    Args:
        data_directory (str): Path to the directory containing input files
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: contratos, contratos_valores, contratos_fechas
    """
    
    try:
        print("=" * 60)
        print("SECOP CONTRACTS TRANSFORMATION WITH INTEGRATED BPIN MAPPING")
        print("=" * 60)
        
        # Load main SECOP CSV file
        main_csv_path = os.path.join(data_directory, "SECOP_II_-_Procesos_de_Contrataci_n_20250811.csv")
        print(f"Loading main SECOP file: {main_csv_path}")
        df_main = pd.read_csv(main_csv_path, encoding='utf-8')
        df_main = normalize_column_names(df_main)
        print(f"Loaded main file with {len(df_main)} contracts")
        
        # Load BPIN mapping files
        contratos_bpin_path = os.path.join(data_directory, "DatosAbiertosContratosXProyectosInv.csv")
        procesos_bpin_path = os.path.join(data_directory, "DatosAbiertosProcesosXProyectosInv.csv")
        
        df_contratos_bpin = None
        df_procesos_bpin = None
        
        if os.path.exists(contratos_bpin_path):
            print(f"Loading contratos BPIN file: {contratos_bpin_path}")
            df_contratos_bpin = pd.read_csv(contratos_bpin_path, encoding='utf-8')
            print(f"Loaded contratos BPIN file with {len(df_contratos_bpin)} records")
        
        if os.path.exists(procesos_bpin_path):
            print(f"Loading procesos BPIN file: {procesos_bpin_path}")
            df_procesos_bpin = pd.read_csv(procesos_bpin_path, encoding='utf-8')
            print(f"Loaded procesos BPIN file with {len(df_procesos_bpin)} records")
        
        # Create comprehensive BPIN mapping
        print("\nCreating comprehensive BPIN mapping...")
        bpin_mapping = create_bpin_mapping(df_contratos_bpin, df_procesos_bpin)
        
        # Map BPIN to contracts
        print("\nMapping BPIN to contracts...")
        df_main = map_bpin_to_contracts(df_main, bpin_mapping)
        
        # Extract cod_centro_gestor
        print("\nExtracting cod_centro_gestor...")
        df_main['cod_centro_gestor'] = df_main['referencia_del_proceso'].apply(extract_cod_centro_gestor)
        
        # Create cod_contrato from referencia_del_proceso
        df_main['cod_contrato'] = df_main['referencia_del_proceso'].astype(str)
        
        print(f"Processing {len(df_main)} contracts...")
        
        # CREATE CONTRATOS DATAFRAME
        print("\nCreating contratos dataframe...")
        contratos_data = []
        for _, row in df_main.iterrows():
            contrato = {
                'cod_contrato': row.get('cod_contrato'),
                'bpin': int(row['bpin']) if pd.notna(row['bpin']) else None,
                'cod_centro_gestor': int(row['cod_centro_gestor']) if pd.notna(row['cod_centro_gestor']) else None,
                'cod_proceso_de_compra': row.get('id_del_proceso'),
                'duracion_contrato': clean_numeric_value(row.get('duracion')),
                'dias_adicionados': None,
                'estado_contrato': row.get('estado_del_procedimiento'),
                'objeto_contrato': row.get('nombre_del_procedimiento'),
                'tipo_contrato': row.get('tipo_de_contrato'),
                'descripcion_proceso': row.get('descripcion_del_procedimiento'),
                'modalidad_contratacion': row.get('modalidad_de_contratacion'),
                'justificacion_modalidad_contratacion': row.get('justificacion_modalidad_de_contratacion'),
                'condiciones_entrega': None,
                'origen_recursos': None,
                'destino_gasto': None,
                'estado_bpin': None,
                'entidad_contratante': row.get('entidad'),
                'nit_entidad': clean_numeric_value(row.get('nit_entidad')),
                'departamento_entidad': row.get('departamento_entidad'),
                'ciudad_entidad': row.get('ciudad_entidad'),
                'unidad_contratacion': row.get('nombre_de_la_unidad_de_contratacion'),
                'ciudad_unidad_contratacion': row.get('ciudad_de_la_unidad_de_contratacion'),
                'fase': row.get('fase'),
                'numero_lotes': clean_numeric_value(row.get('numero_de_lotes')),
                'adjudicado': row.get('adjudicado'),
                'nombre_adjudicador': row.get('nombre_del_adjudicador'),
                'nombre_proveedor': row.get('nombre_del_proveedor_adjudicado'),
                'nit_proveedor': row.get('nit_del_proveedor_adjudicado'),
                'codigo_categoria': row.get('codigo_principal_de_categoria'),
                'subtipo_contrato': row.get('subtipo_de_contrato'),
                'urlproceso': row.get('urlproceso')
            }
            contratos_data.append(contrato)
        
        contratos_df = pd.DataFrame(contratos_data)
        print(f"Created contratos dataframe with {len(contratos_df)} records")
        
        # CREATE CONTRATOS_VALORES DATAFRAME
        print("\nCreating contratos_valores dataframe...")
        valores_data = []
        for _, row in df_main.iterrows():
            valor = {
                'cod_contrato': row.get('cod_contrato'),
                'valor_contrato': clean_numeric_value(row.get('precio_base')),
                'valor_pago_adelantado': None,
                'valor_facturado': None,
                'valor_pagado': None,
                'valor_amortizacion_pago_adelantado': None,
                'valor_pendiente_pago': None,
                'valor_pendiente_amortizacion': None,
                'valor_factura_pagada': None,
                'valor_total_pagos': None,
                'porcentaje_avance_fisico': None,
                'porcentaje_avance_financiero': None,
                'recursos_publicos': None,
                'recursos_propios_alcaldia': None,
                'recursos_credito': None,
                'recursos_propios': None,
                'valor_adjudicado': clean_numeric_value(row.get('valor_total_adjudicacion')),
                'precio_base': clean_numeric_value(row.get('precio_base'))
            }
            valores_data.append(valor)
        
        valores_df = pd.DataFrame(valores_data)
        print(f"Created contratos_valores dataframe with {len(valores_df)} records")
        
        # CREATE CONTRATOS_FECHAS DATAFRAME
        print("\nCreating contratos_fechas dataframe...")
        fechas_data = []
        for _, row in df_main.iterrows():
            fecha = {
                'bpin': row.get('bpin'),  # ✅ BPIN incluido en contratos_fechas
                'cod_contrato': row.get('cod_contrato'),
                'fecha_firma_contrato': clean_date_value(row.get('fecha_adjudicacion')),
                'fecha_inicio_contrato': None,
                'fecha_fin_contrato': None,
                'fecha_inicio_ejecucion': None,
                'fecha_fin_ejecucion': None,
                'fecha_liquidacion': None,
                'fecha_publicacion_proceso': clean_date_value(row.get('fecha_de_publicacion_del_proceso')),
                'fecha_recepcion_respuestas': clean_date_value(row.get('fecha_de_recepcion_de_respuestas')),
                'fecha_adjudicacion': clean_date_value(row.get('fecha_adjudicacion'))
            }
            fechas_data.append(fecha)
        
        fechas_df = pd.DataFrame(fechas_data)
        print(f"Created contratos_fechas dataframe with {len(fechas_df)} records")
        
        # Print summary
        bpin_count = contratos_df['bpin'].notna().sum()
        centro_gestor_count = contratos_df['cod_centro_gestor'].notna().sum()
        
        print("\n" + "=" * 60)
        print("TRANSFORMATION SUMMARY")
        print("=" * 60)
        print(f"Total contracts processed: {len(contratos_df):,}")
        print(f"Contracts with valid BPIN: {bpin_count:,} ({bpin_count/len(contratos_df)*100:.1f}%)")
        print(f"Contracts with cod_centro_gestor: {centro_gestor_count:,} ({centro_gestor_count/len(contratos_df)*100:.1f}%)")
        print(f"Unique BPINs found: {contratos_df['bpin'].nunique()}")
        print("=" * 60)
        
        return contratos_df, valores_df, fechas_df
        
    except Exception as e:
        print(f"Error in transformation: {e}")
        return None, None, None


if __name__ == "__main__":
    # Ejecutar transformación
    print("🚀 Iniciando transformación de contratos con BPIN como fuente primaria...")
    print("⏱️  Tiempo de inicio:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    start_time = time.time()
    
    contratos_df, valores_df = contratos_transformer()
    
    if contratos_df is not None and valores_df is not None:
        # Guardar en archivos JSON
        save_dataframes_to_json(contratos_df, valores_df)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n🎉 ¡Transformación completada exitosamente!")
        print(f"⏱️  Tiempo total de ejecución: {execution_time:.2f} segundos")
        print(f"📊 Rendimiento: {len(contratos_df)/execution_time:.1f} registros/segundo")
    else:
        print("\n❌ ¡Transformación falló!")
