# -*- coding: utf-8 -*-
"""
Transformación optimizada de datos de ejecución presupuestal
Basado en el patrón del integrador_ejecucion_presupuestal.py
Procesa múltiples archivos CSV y genera 3 archivos JSON optimizados:
1. Datos característicos de proyectos (master data)
2. Movimientos presupuestales 
3. Ejecución presupuestal
"""

import os
import pandas as pd
import numpy as np
import re
import unicodedata
import time
import psutil
from tqdm import tqdm
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
from dateutil.relativedelta import relativedelta


def normalize_column_names(columns: List[str]) -> List[str]:
    """Normaliza nombres de columnas eliminando espacios, acentos y conectores"""
    normalized_cols = []
    for col in columns:
        # Convert to lowercase
        col = col.lower()
        # Replace spaces with underscores
        col = col.replace(' ', '_')
        # Remove leading/trailing underscores
        col = col.strip('_')
        # Remove accents (tildes)
        col = unicodedata.normalize('NFD', col).encode('ascii', 'ignore').decode('utf-8')
        # Replace 'ñ' with 'n'
        col = col.replace('ñ', 'n')
        normalized_cols.append(col)
    return normalized_cols


def clean_monetary_value(value: Union[str, float, int]) -> int:
    """Limpia valores monetarios removiendo caracteres no numéricos y devuelve entero puro"""
    if pd.isna(value) or value == '':
        return 0
    
    if isinstance(value, (int, float)):
        # Si ya es numérico, convertir a entero
        return int(value) if not pd.isna(value) and not np.isinf(value) else 0
    
    if isinstance(value, str):
        # Remover TODOS los caracteres que no sean dígitos
        # Esto preserva todos los números y elimina puntos, comas, espacios, símbolos, etc.
        cleaned = re.sub(r'[^\d]', '', str(value).strip())
        
        try:
            return int(cleaned) if cleaned else 0
        except ValueError:
            return 0
    
    return 0


def is_program_column(column: pd.Series) -> bool:
    """Verifica si una columna contiene códigos de programa (valor inicial 4599)"""
    first_value = column.dropna().iloc[0] if not column.dropna().empty else None
    return first_value is not None and (str(first_value) == '4599' or (isinstance(first_value, (int, float)) and first_value == 4599))


def load_csv_files(input_dir: str) -> Dict[str, pd.DataFrame]:
    """Carga todos los archivos CSV del directorio de entrada"""
    print(f"Cargando archivos CSV desde {input_dir}")
    
    files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    dfs = {}
    
    for file_name in tqdm(files, desc="Cargando archivos CSV"):
        file_path = os.path.join(input_dir, file_name)
        try:
            # Try different separators and encodings
            df = None
            separators = [',', ';', '\t']
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        df = pd.read_csv(file_path, sep=sep, encoding=encoding, on_bad_lines='skip')
                        if df.shape[1] > 1:  # Check if we have multiple columns
                            break
                    except:
                        continue
                if df is not None and df.shape[1] > 1:
                    break
            
            if df is None or df.shape[1] == 1:
                # Last resort: try automatic detection
                df = pd.read_csv(file_path, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            
            df_name = os.path.splitext(file_name)[0]
            dfs[df_name] = df
            print(f"Cargado exitosamente '{file_name}' con forma {df.shape}")
            print(f"Columnas originales en '{file_name}': {df.columns.tolist()[:10]}...")  # Show first 10 columns
            
        except Exception as e:
            print(f"Error cargando '{file_name}': {e}")
    
    return dfs


def preprocess_dataframes(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Preprocesa los DataFrames eliminando columnas innecesarias"""
    print("Preprocesando DataFrames...")
    
    # Eliminar columna RUBRO donde corresponda
    for df_name in tqdm(dfs.keys(), desc="Eliminando columnas innecesarias"):
        df = dfs[df_name]
        if 'RUBRO' in df.columns:
            dfs[df_name] = df.drop(columns=['RUBRO'])
            print(f"Columna 'RUBRO' eliminada de '{df_name}'")
    
    return dfs


def normalize_dataframes(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Normaliza nombres de columnas y aplica transformaciones específicas"""
    print("Normalizando nombres de columnas...")
    
    for df_name, df in tqdm(dfs.items(), desc="Normalizando DataFrames"):
        # Normalizar nombres de columnas
        df.columns = normalize_column_names(df.columns)
        
        # Renombrar columnas específicas con códigos de programa
        columns_to_rename = {}
        for col in df.columns:
            if 'programa' in col.lower().replace(" ", "") and is_program_column(df[col]):
                columns_to_rename[col] = 'cod_programa'
        
        if columns_to_rename:
            df = df.rename(columns=columns_to_rename)
        
        dfs[df_name] = df
    
    return dfs


def apply_column_mappings(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Aplica mapeos específicos de columnas"""
    print("Aplicando mapeos de columnas...")
    
    # Definir mapeos de columnas
    column_mappings = {
        'programa': 'programa_presupuestal',
        'nombre_de_la_actividad': 'nombre_actividad',
        'nombre_de_fondo': 'nombre_fondo',
        'nombre_del_area_funcional': 'nombre_area_funcional',
        'nombre_de_linea_estrategica': 'nombre_linea_estrategica',
        'nombre_del_proyecto': 'nombre_proyecto',
        'tipo_de_gasto': 'tipo_gasto',
        'clasificacion_del_fondo': 'clasificacion_fondo',
        'ppto._disponible': 'ppto_disponible',
        'ppto._modificado': 'ppto_modificado',
        'fondo_1': 'fondo',
        'clasificacion_del_fondo_1': 'clasificacion_fondo',
        'pospre_1': 'pospre',
        'pospre_1.1': 'nombre_pospre',
        'nombre_de_dimension': 'nombre_dimension',
        'nombre_bp': 'nombre_proyecto',
        'nompre_bp': 'nombre_proyecto',
        'nombre_de_programa': 'nombre_programa',
        'sector': 'cod_sector',
        'producto': 'cod_producto'
    }
    
    for df_name, df in tqdm(dfs.items(), desc="Aplicando mapeos"):
        # Aplicar renombramientos
        for old_name, new_name in column_mappings.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        dfs[df_name] = df
    
    return dfs


def remove_unnecessary_columns(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Elimina columnas innecesarias"""
    print("Eliminando columnas innecesarias...")
    
    columns_to_drop = [
        'producto_1', 'programa.1', 'cod_programa', 
        'validador_cuipo', 'producto_cuipo', 'producto_mga', 'nombre_reto', 
        'proposito', 'nombre_proposito', 'reto', 'nombre_producto_mga', 
        'codigo_producto_mga'
    ]
    
    for df_name in tqdm(dfs.keys(), desc="Eliminando columnas específicas"):
        df = dfs[df_name]
        for col in columns_to_drop:
            if col in df.columns:
                dfs[df_name] = df.drop(columns=[col])
    
    return dfs


def fill_missing_columns_with_reference(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Completa columnas faltantes usando DataFrames de referencia"""
    print("Completando columnas faltantes...")
    
    # Simplificado: no completar columnas faltantes automáticamente
    # Solo normalizar las existentes
    print("Saltando completado automático de columnas para evitar errores")
    
    return dfs


def add_operational_data(dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """Añade datos operacionales (año, origen, período)"""
    print("Añadiendo datos operacionales...")
    
    # Mapear años basado en el nombre del archivo
    year_mapping = {
        'EJECUCION_ENERO_2024': 2024, 'EJECUCION_FEBRERO_2024': 2024, 'EJECUCION_MARZO_2024': 2024,
        'EJECUCION_ABRIL_2024': 2024, 'EJECUCION_MAYO_2024': 2024, 'EJECUCION_JUNIO_2024': 2024,
        'EJECUCION_JULIO_2024': 2024, 'EJECUCION_AGOSTO_2024': 2024, 'EJECUCION_SEPTIEMBRE_2024': 2024,
        'EJECUCION_OCTUBRE_2024': 2024, 'EJECUCION_NOVIEMBRE_2024': 2024, 'EJECUCION_DICIEMBRE_2024': 2024,
        'EJECUCION_ENERO_2025': 2025, 'EJECUCION_FEBRERO_2025': 2025, 'EJECUCION_MARZO_2025': 2025,
        'EJECUCION_ABRIL_2025': 2025, 'EJECUCION_MAYO_2025': 2025, 'EJECUCION_JUNIO_2025': 2025
    }
    
    for df_name in tqdm(dfs.keys(), desc="Añadiendo datos operacionales"):
        df = dfs[df_name]
        # Añadir año
        if df_name in year_mapping:
            df['anio'] = year_mapping[df_name]
        
        # Añadir dataframe_origen
        df['dataframe_origen'] = df_name
        df['archivo_origen'] = f"{df_name}.csv"
        
        dfs[df_name] = df
    
    return dfs


def create_period_column(df: pd.DataFrame) -> pd.DataFrame:
    """Crea columna de período en formato ISO 8601"""
    
    def obtener_fecha_fin_mes_desde_dataframe_origen_iso(df_origen, anio):
        """Extrae el mes y crea fecha del último día del mes en formato ISO 8601"""
        if pd.isna(df_origen) or pd.isna(anio):
            return None

        partes = df_origen.split('_')
        if len(partes) > 1:
            mes_str = partes[1]
            mes_map = {
                'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
                'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
                'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
            }
            mes = mes_map.get(mes_str.upper())

            if mes is not None:
                try:
                    first_day_of_month = datetime(int(anio), mes, 1)
                    last_day_of_month = first_day_of_month + relativedelta(months=1) - relativedelta(days=1)
                    return last_day_of_month.strftime('%Y-%m-%d')
                except ValueError:
                    return None
        return None
    
    if 'anio' in df.columns:
        df['anio'] = pd.to_numeric(df['anio'], errors='coerce').astype('Int64')
        df['periodo'] = df.apply(
            lambda row: obtener_fecha_fin_mes_desde_dataframe_origen_iso(row['dataframe_origen'], row['anio']),
            axis=1
        )
    
    return df


def consolidate_dataframes(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Consolida todos los DataFrames en uno solo"""
    print("Consolidando DataFrames...")
    
    # Identificar columnas principales
    numeric_cols = ['bp', 'bpin']
    proyecto_col = 'nombre_proyecto'
    
    # Obtener todas las columnas únicas (sin duplicados)
    all_columns = set()
    for df in dfs.values():
        all_columns.update(df.columns)
    
    print(f"Columnas disponibles en total: {len(all_columns)}")
    print(f"Muestra de columnas: {sorted(list(all_columns))[:20]}")
    
    other_cols_order = sorted([col for col in all_columns if col not in numeric_cols + [proyecto_col]])
    
    # Preparar DataFrames para concatenación
    all_dfs_list = []
    for df_name, df in tqdm(dfs.items(), desc="Preparando DataFrames"):
        # Eliminar columnas duplicadas si existen
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Asegurar que todas las columnas necesarias existen
        required_cols = [col for col in numeric_cols + [proyecto_col] + other_cols_order if col not in df.columns]
        
        for col in required_cols:
            df[col] = None
        
        # Reordenar columnas disponibles solamente
        available_cols = [col for col in numeric_cols + [proyecto_col] + other_cols_order if col in df.columns]
        df = df[available_cols]
        
        all_dfs_list.append(df)
    
    # Concatenar todos los DataFrames
    df_consolidado = pd.concat(all_dfs_list, ignore_index=True, sort=False)
    
    # Mostrar columnas finales
    print(f"Columnas en DataFrame consolcdidado: {df_consolidado.columns.tolist()}")
    
    # Crear columna de período
    df_consolidado = create_period_column(df_consolidado)
    
    # Limpiar filas con más del 80% de valores nulos
    null_percentage_per_row = df_consolidado.isnull().sum(axis=1) / df_consolidado.shape[1]
    rows_to_drop_mask = null_percentage_per_row > 0.8
    df_consolidado = df_consolidado[~rows_to_drop_mask].copy()
    
    print(f"Se eliminaron {rows_to_drop_mask.sum()} filas con más del 80% de valores nulos")
    
    return df_consolidado


def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte tipos de datos apropiados"""
    print("Convirtiendo tipos de datos...")
    
    # Columnas de códigos que deben ser enteros
    codigo_columns = [col for col in df.columns if col.startswith('cod_') or col in ['bp', 'bpin']]
    
    for col in tqdm(codigo_columns, desc="Convirtiendo códigos a enteros"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    
    # Columnas monetarias - convertir a enteros puros
    monetary_columns = [
        'ppto_inicial', 'reducciones', 'adiciones', 'contracreditos', 'creditos',
        'aplazamiento', 'desaplazamiento', 'ppto_modificado', 'total_acumulado_cdp',
        'total_acumulado_rpc', 'total_acumul_obligac', 'pagos', 'ejecucion',
        'saldos_cdp', 'ppto_disponible'
    ]
    
    for col in tqdm(monetary_columns, desc="Convirtiendo valores monetarios"):
        if col in df.columns:
            df[col] = df[col].apply(clean_monetary_value)
    
    return df


def create_master_data(df: pd.DataFrame) -> pd.DataFrame:
    """Crea el DataFrame de datos maestros (características de proyectos)"""
    print("Creando datos maestros de proyectos...")
    
    # Columnas características de proyectos (datos que no cambian frecuentemente)
    master_columns = [
        'bpin', 'bp', 'nombre_proyecto', 'nombre_actividad', 'programa_presupuestal',
        'cod_centro_gestor', 'nombre_centro_gestor', 'cod_area_funcional', 'nombre_area_funcional',
        'cod_fondo', 'nombre_fondo', 'clasificacion_fondo', 'cod_pospre', 'nombre_pospre',
        'cod_dimension', 'nombre_dimension', 'cod_linea_estrategica', 'nombre_linea_estrategica',
        'cod_programa', 'nombre_programa', 'cod_comuna', 'origen', 'anio', 'tipo_gasto',
        'cod_sector', 'cod_producto', 'validador_cuipo'  # Cambiado sector y producto por cod_sector y cod_producto
    ]
    
    # Filtrar columnas que existen en el DataFrame
    available_columns = [col for col in master_columns if col in df.columns]
    
    # Si no hay suficientes columnas, usar todas las columnas disponibles excepto las de movimientos/ejecución
    if len(available_columns) < 5:
        exclude_columns = [
            'ppto_inicial', 'reducciones', 'adiciones', 'contracreditos', 'creditos',
            'aplazamiento', 'desaplazamiento', 'ppto_modificado', 'total_acumulado_cdp',
            'total_acumulado_rpc', 'total_acumul_obligac', 'pagos', 'ejecucion',
            'saldos_cdp', 'ppto_disponible', 'periodo', 'dataframe_origen', 'archivo_origen'
        ]
        available_columns = [col for col in df.columns if col not in exclude_columns]
    
    # Crear DataFrame de datos maestros eliminando duplicados por bpin
    if 'bpin' in available_columns:
        print("Eliminando duplicados por BPIN...")
        master_df = df[available_columns].drop_duplicates(subset=['bpin']).reset_index(drop=True)
    else:
        print("Eliminando duplicados generales...")
        master_df = df[available_columns].drop_duplicates().reset_index(drop=True)
    
    print(f"Datos maestros creados con {len(master_df)} registros únicos")
    print(f"Columnas incluidas: {available_columns}")
    return master_df


def create_movimientos_presupuestales(df: pd.DataFrame) -> pd.DataFrame:
    """Crea el DataFrame de movimientos presupuestales agrupados por BPIN y período"""
    print("Creando movimientos presupuestales...")
    
    # Verificar columnas disponibles
    print(f"Columnas disponibles en DataFrame: {df.columns.tolist()}")
    
    # Columnas de movimientos presupuestales EXACTAS (sin ppto_disponible)
    base_columns = ['bpin', 'periodo']
    monetary_columns = [
        'ppto_inicial', 'reducciones', 'adiciones', 'contracreditos', 'creditos',
        'aplazamiento', 'desaplazamiento', 'ppto_modificado'
    ]
    info_columns = ['dataframe_origen', 'archivo_origen']
    
    # Buscar solo columnas específicas de movimientos (EXCLUIR ppto_disponible y columnas de ejecución)
    excluded_keywords = ['disponible', 'cdp', 'rpc', 'obligac', 'pagos', 'ejecucion', 'saldos', 'acumulado', 'total']
    found_monetary = []
    for col in df.columns:
        col_lower = col.lower()
        # Solo incluir si contiene palabras de movimientos Y NO contiene palabras de ejecución
        is_movement = any(keyword in col_lower for keyword in ['ppto', 'presupuesto', 'inicial', 'modificado', 'adicion', 'reduccion', 'credito', 'aplazamiento'])
        is_execution = any(keyword in col_lower for keyword in excluded_keywords)
        
        if is_movement and not is_execution:
            found_monetary.append(col)
    
    print(f"Columnas monetarias encontradas: {found_monetary}")
    
    # Construir lista de columnas disponibles
    available_columns = []
    
    # Añadir columnas base
    for col in base_columns:
        if col in df.columns:
            available_columns.append(col)
    
    # Añadir columnas monetarias encontradas
    available_columns.extend(found_monetary)
    
    # Añadir columnas de información
    for col in info_columns:
        if col in df.columns:
            available_columns.append(col)
    
    # Eliminar duplicados manteniendo orden
    available_columns = list(dict.fromkeys(available_columns))
    
    print(f"Columnas seleccionadas para movimientos: {available_columns}")
    
    # Si no tenemos BPIN, usar una clave alternativa
    key_column = 'bpin' if 'bpin' in df.columns else df.columns[0]
    
    print(f"Filtrando registros válidos por {key_column}...")
    movimientos_df = df[available_columns].dropna(subset=[key_column, 'periodo']).reset_index(drop=True)
    
    # Identificar columnas realmente monetarias para filtro
    actual_monetary = [col for col in found_monetary if col in movimientos_df.columns]
    
    if actual_monetary:
        print(f"Filtrando registros con valores monetarios significativos en: {actual_monetary}")
        # Mantener filas que tienen al menos un valor monetario > 0
        monetary_mask = (movimientos_df[actual_monetary] != 0).any(axis=1)
        movimientos_df = movimientos_df[monetary_mask].reset_index(drop=True)
        print(f"Registros después del filtro monetario: {len(movimientos_df)}")
    
    # Agrupar por BPIN y período, sumando los valores monetarios
    print("Agrupando datos por BPIN y período...")
    group_columns = ['bpin', 'periodo']
    
    # Columnas de información (tomar el primer valor no nulo)
    info_cols_available = [col for col in info_columns if col in movimientos_df.columns]
    
    # Realizar la agrupación
    agg_dict = {}
    
    # Sumar valores monetarios
    for col in actual_monetary:
        agg_dict[col] = 'sum'
    
    # Tomar primer valor para columnas informativas
    for col in info_cols_available:
        agg_dict[col] = 'first'
    
    print(f"Configuración de agregación: {agg_dict}")
    
    movimientos_df_grouped = movimientos_df.groupby(group_columns, as_index=False).agg(agg_dict)
    
    print(f"Movimientos presupuestales creados con {len(movimientos_df_grouped)} registros agrupados")
    print(f"Registros originales: {len(movimientos_df)} -> Registros agrupados: {len(movimientos_df_grouped)}")
    print(f"Columnas finales: {movimientos_df_grouped.columns.tolist()}")
    return movimientos_df_grouped


def create_ejecucion_presupuestal(df: pd.DataFrame) -> pd.DataFrame:
    """Crea el DataFrame de ejecución presupuestal agrupado por BPIN y período"""
    print("Creando ejecución presupuestal...")
    
    # Verificar columnas disponibles
    print(f"Columnas disponibles en DataFrame: {df.columns.tolist()}")
    
    # Columnas base
    base_columns = ['bpin', 'periodo']
    
    # Buscar SOLO columnas de ejecución (incluir ppto_disponible aquí)
    execution_keywords = [
        'cdp', 'rpc', 'obligac', 'pagos', 'ejecucion', 'saldos', 'disponible',
        'acumulado', 'total'
    ]
    
    found_execution = []
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in execution_keywords):
            found_execution.append(col)
    
    # Asegurar que ppto_disponible esté incluido si existe
    if 'ppto_disponible' in df.columns and 'ppto_disponible' not in found_execution:
        found_execution.append('ppto_disponible')
    
    print(f"Columnas de ejecución encontradas: {found_execution}")
    
    info_columns = ['dataframe_origen', 'archivo_origen']
    
    # Construir lista de columnas disponibles
    available_columns = []
    
    # Añadir columnas base
    for col in base_columns:
        if col in df.columns:
            available_columns.append(col)
    
    # Añadir columnas de ejecución encontradas
    available_columns.extend(found_execution)
    
    # Añadir columnas de información
    for col in info_columns:
        if col in df.columns:
            available_columns.append(col)
    
    # Eliminar duplicados manteniendo orden
    available_columns = list(dict.fromkeys(available_columns))
    
    print(f"Columnas seleccionadas para ejecución: {available_columns}")
    
    # Si no tenemos BPIN, usar una clave alternativa
    key_column = 'bpin' if 'bpin' in df.columns else df.columns[0]
    
    print(f"Filtrando registros válidos por {key_column}...")
    ejecucion_df = df[available_columns].dropna(subset=[key_column, 'periodo']).reset_index(drop=True)
    
    # Identificar columnas realmente de ejecución para filtro
    actual_execution = [col for col in found_execution if col in ejecucion_df.columns]
    
    if actual_execution:
        print(f"Filtrando registros con valores de ejecución significativos en: {actual_execution}")
        # Mantener filas que tienen al menos un valor de ejecución > 0
        execution_mask = (ejecucion_df[actual_execution] != 0).any(axis=1)
        ejecucion_df = ejecucion_df[execution_mask].reset_index(drop=True)
        print(f"Registros después del filtro de ejecución: {len(ejecucion_df)}")
    
    # Agrupar por BPIN y período, sumando los valores de ejecución
    print("Agrupando datos por BPIN y período...")
    group_columns = ['bpin', 'periodo']
    
    # Columnas de información (tomar el primer valor no nulo)
    info_cols_available = [col for col in info_columns if col in ejecucion_df.columns]
    
    # Realizar la agrupación
    agg_dict = {}
    
    # Sumar valores de ejecución
    for col in actual_execution:
        agg_dict[col] = 'sum'
    
    # Tomar primer valor para columnas informativas
    for col in info_cols_available:
        agg_dict[col] = 'first'
    
    print(f"Configuración de agregación: {agg_dict}")
    
    ejecucion_df_grouped = ejecucion_df.groupby(group_columns, as_index=False).agg(agg_dict)
    
    print(f"Ejecución presupuestal creada con {len(ejecucion_df_grouped)} registros agrupados")
    print(f"Registros originales: {len(ejecucion_df)} -> Registros agrupados: {len(ejecucion_df_grouped)}")
    print(f"Columnas finales: {ejecucion_df_grouped.columns.tolist()}")
    return ejecucion_df_grouped


def save_json_files(master_df: pd.DataFrame, movimientos_df: pd.DataFrame, 
                   ejecucion_df: pd.DataFrame, output_dir: str) -> None:
    """Guarda los DataFrames en archivos JSON"""
    print("Guardando archivos JSON...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Guardar archivos JSON con barra de progreso
    files_to_save = [
        (master_df, 'datos_caracteristicos_proyectos.json'),
        (movimientos_df, 'movimientos_presupuestales.json'),
        (ejecucion_df, 'ejecucion_presupuestal.json')
    ]
    
    for df, filename in tqdm(files_to_save, desc="Guardando archivos JSON"):
        file_path = os.path.join(output_dir, filename)
        df.to_json(file_path, orient='records', indent=2, force_ascii=False)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"✓ Guardado {filename}: {len(df)} filas, {file_size_mb:.1f} MB")


def print_performance_metrics(start_time: float, df_consolidado: pd.DataFrame) -> None:
    """Imprime métricas de desempeño"""
    end_time = time.time()
    execution_time = end_time - start_time
    
    process = psutil.Process()
    memory_usage = process.memory_info().rss / (1024 * 1024)  # MB
    
    print("\n" + "="*60)
    print("MÉTRICAS DE DESEMPEÑO:")
    print("="*60)
    print(f"Tiempo total de ejecución: {execution_time:.2f} segundos")
    print(f"Total de filas procesadas: {len(df_consolidado):,}")
    print(f"Total de columnas: {len(df_consolidado.columns)}")
    print(f"Memoria utilizada: {memory_usage:.2f} MB")
    print("="*60)


def main():
    """Función principal"""
    start_time = time.time()
    
    print("Iniciando transformación optimizada de datos de ejecución presupuestal...")
    
    # Configurar directorios
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(current_dir, "app_inputs", "ejecucion_presupuestal_input")
    output_dir = os.path.join(current_dir, "app_outputs", "ejecucion_presupuestal_outputs")
    
    try:
        # 1. Cargar archivos CSV
        dfs = load_csv_files(input_dir)
        
        # 2. Preprocesar DataFrames
        dfs = preprocess_dataframes(dfs)
        
        # 3. Normalizar nombres de columnas
        dfs = normalize_dataframes(dfs)
        
        # 4. Aplicar mapeos de columnas
        dfs = apply_column_mappings(dfs)
        
        # 5. Eliminar columnas innecesarias
        dfs = remove_unnecessary_columns(dfs)
        
        # 6. Completar columnas faltantes
        dfs = fill_missing_columns_with_reference(dfs)
        
        # 7. Añadir datos operacionales
        dfs = add_operational_data(dfs)
        
        # 8. Consolidar DataFrames
        df_consolidado = consolidate_dataframes(dfs)
        
        # 9. Convertir tipos de datos
        df_consolidado = convert_data_types(df_consolidado)
        
        # 10. Crear DataFrames especializados
        master_df = create_master_data(df_consolidado)
        movimientos_df = create_movimientos_presupuestales(df_consolidado)
        ejecucion_df = create_ejecucion_presupuestal(df_consolidado)
        
        # 11. Guardar archivos JSON
        save_json_files(master_df, movimientos_df, ejecucion_df, output_dir)
        
        # 12. Imprimir métricas
        print_performance_metrics(start_time, df_consolidado)
        
        print(f"\n¡Transformación completada exitosamente!")
        print(f"Archivos guardados en: {output_dir}")
        print(f"- Datos característicos: {len(master_df)} registros")
        print(f"- Movimientos presupuestales: {len(movimientos_df)} registros")
        print(f"- Ejecución presupuestal: {len(ejecucion_df)} registros")
        
    except Exception as e:
        print(f"Error durante la transformación: {e}")
        raise


if __name__ == "__main__":
    main()
