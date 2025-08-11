# -*- coding: utf-8 -*-
"""
Data transformation module for project monitoring (seguimiento PA) data processing.
Processes Excel files from seguimiento_pa_input directory and generates standardized JSON outputs.
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import json


def normalize_column_names(columns):
    """Normalize column names by converting to lowercase and removing special characters."""
    normalized = []
    for col in columns:
        if pd.isna(col):
            normalized.append('unnamed_column')
        else:
            # Convert to string and normalize
            col_str = str(col).lower().strip()
            # Replace common separators and special characters
            col_str = (col_str.replace(' ', '_')
                      .replace('.', '_')
                      .replace('(', '')
                      .replace(')', '')
                      .replace('%', 'pct')
                      .replace('ó', 'o')
                      .replace('á', 'a')
                      .replace('é', 'e')
                      .replace('í', 'i')
                      .replace('ú', 'u')
                      .replace('ñ', 'n')
                      .replace('/', '_')
                      .replace('-', '_')
                      .replace('\n', '_')
                      .replace('\r', ''))
            # Remove multiple underscores
            while '__' in col_str:
                col_str = col_str.replace('__', '_')
            # Remove leading/trailing underscores
            col_str = col_str.strip('_')
            normalized.append(col_str)
    return normalized


def clean_numeric_value(value) -> float:
    """Clean numeric values by removing formatting symbols while preserving original numbers."""
    if pd.isna(value):
        return 0.00
    
    # Convert to string first
    str_value = str(value).strip()
    
    # Handle special cases
    if str_value in ['-', '', 'nan', 'NaN', 'None']:
        return 0.00
    
    # If already a number, return it rounded to 2 decimals
    try:
        if isinstance(value, (int, float)) and not pd.isna(value):
            return round(float(value), 2)
    except:
        pass
    
    # Handle percentage values - keep the percentage number, don't divide by 100
    if '%' in str_value:
        try:
            # Remove % symbol but keep the number as is
            cleaned = str_value.replace('%', '').strip()
            # Handle comma as decimal separator
            if ',' in cleaned and cleaned.count(',') == 1:
                cleaned = cleaned.replace(',', '.')
            # Remove thousand separators (dots when there are multiple or when comma is decimal separator)
            if '.' in cleaned and ',' in str_value:
                # Comma was decimal separator, dots are thousand separators
                parts = cleaned.split('.')
                if len(parts) > 2:  # Multiple dots = thousand separators
                    cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
            return round(float(cleaned), 2)
        except (ValueError, TypeError):
            print(f"Warning: Could not convert percentage '{str_value}' to numeric - Setting to 0.00")
            return 0.00
    
    # Clean monetary and numeric values
    cleaned = str_value
    
    # Remove currency symbols
    cleaned = cleaned.replace('$', '').replace(' ', '').strip()
    
    # Handle different number formats
    # Check if comma is used as decimal separator (European format)
    if ',' in cleaned and '.' in cleaned:
        # Both comma and dot present - determine which is decimal separator
        last_comma = cleaned.rfind(',')
        last_dot = cleaned.rfind('.')
        
        if last_comma > last_dot:
            # Comma is decimal separator, dots are thousand separators
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # Dot is decimal separator, commas are thousand separators
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # Only comma present - check if it's decimal separator
        comma_pos = cleaned.rfind(',')
        after_comma = cleaned[comma_pos + 1:]
        if len(after_comma) <= 2 and after_comma.isdigit():
            # Comma is decimal separator
            cleaned = cleaned.replace(',', '.')
        else:
            # Comma is thousand separator
            cleaned = cleaned.replace(',', '')
    elif '.' in cleaned:
        # Only dots present - check if they are thousand separators
        dot_count = cleaned.count('.')
        if dot_count > 1:
            # Multiple dots = thousand separators, keep only the last one as decimal
            parts = cleaned.split('.')
            cleaned = ''.join(parts[:-1]) + '.' + parts[-1]
        else:
            # Single dot - check if it's decimal separator
            dot_pos = cleaned.rfind('.')
            after_dot = cleaned[dot_pos + 1:]
            if len(after_dot) > 2:
                # More than 2 digits after dot = thousand separator
                cleaned = cleaned.replace('.', '')
    
    # Remove any remaining non-numeric characters except decimal point and minus sign
    import re
    cleaned = re.sub(r'[^\d.-]', '', cleaned)
    
    # Handle the case where cleaned string is just "-" after cleaning
    if cleaned in ['-', '']:
        return 0.00
    
    try:
        return round(float(cleaned), 2)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert '{str_value}' to numeric - Setting to 0.00")
        return 0.00


def clean_integer_value(value) -> Optional[int]:
    """Clean integer values by removing formatting and converting to int."""
    if pd.isna(value):
        return None
    
    # Convert to string first
    str_value = str(value).strip()
    
    # Handle special cases
    if str_value in ['-', '', 'nan', 'NaN', 'None']:
        return None
    
    # If already a number, return it
    try:
        if isinstance(value, (int, float)) and not pd.isna(value):
            return int(value)
    except:
        pass
    
    # Remove non-numeric characters
    cleaned = ''.join(c for c in str_value if c.isdigit())
    
    if not cleaned:
        return None
    
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert '{str_value}' to integer - Setting to None")
        return None


def clean_date_value(value) -> Optional[str]:
    """Clean date values and convert to ISO format string."""
    if pd.isna(value):
        return None
    
    try:
        # If it's already a datetime
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d')
        
        # If it's a string, try to parse it
        if isinstance(value, str):
            # Try different date formats
            date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(value.strip(), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        # Try pandas to_datetime as last resort
        parsed_date = pd.to_datetime(value)
        if not pd.isna(parsed_date):
            return parsed_date.strftime('%Y-%m-%d')
            
    except Exception as e:
        print(f"Warning: Could not parse date '{value}': {e}")
    
    return None


def extract_periodo_from_filename(filename: str) -> str:
    """Extract period from filename."""
    filename_lower = filename.lower()
    
    # Month mapping
    month_mapping = {
        'enero': '01', 'jan': '01', 'january': '01',
        'febrero': '02', 'feb': '02', 'february': '02',
        'marzo': '03', 'mar': '03', 'march': '03',
        'abril': '04', 'abr': '04', 'apr': '04', 'april': '04',
        'mayo': '05', 'may': '05',
        'junio': '06', 'jun': '06', 'june': '06',
        'julio': '07', 'jul': '07', 'july': '07',
        'agosto': '08', 'ago': '08', 'aug': '08', 'august': '08',
        'septiembre': '09', 'sep': '09', 'september': '09',
        'octubre': '10', 'oct': '10', 'october': '10',
        'noviembre': '11', 'nov': '11', 'november': '11',
        'diciembre': '12', 'dic': '12', 'dec': '12', 'december': '12'
    }
    
    # Quarter mapping
    quarter_mapping = {
        'i trimestre': '03', 'primer trimestre': '03', '1 trimestre': '03',
        'ii trimestre': '06', 'segundo trimestre': '06', '2 trimestre': '06',
        'iii trimestre': '09', 'tercer trimestre': '09', '3 trimestre': '09',
        'iv trimestre': '12', 'cuarto trimestre': '12', '4 trimestre': '12'
    }
    
    # Extract year (look for 4-digit year)
    year = '2024'  # default
    import re
    year_match = re.search(r'(20\d{2})', filename)
    if year_match:
        year = year_match.group(1)
    
    # Look for quarter first
    for quarter_text, month in quarter_mapping.items():
        if quarter_text in filename_lower:
            return f"{year}-{month}"
    
    # Look for month
    for month_name, month_num in month_mapping.items():
        if month_name in filename_lower:
            return f"{year}-{month_num}"
    
    # Default to December of the year
    return f"{year}-12"


def read_excel_file(file_path: str) -> Tuple[Optional[pd.DataFrame], str]:
    """Read Excel file and return DataFrame with periodo."""
    filename = os.path.basename(file_path)
    periodo_corte = extract_periodo_from_filename(filename)
    
    try:
        # First check if it's a detailed file or summary file
        # Try to detect by checking if there are many columns and specific headers
        df_test = pd.read_excel(file_path, sheet_name=0, header=8, nrows=5)
        
        if len(df_test.columns) > 30 and any('BPIN' in str(col) for col in df_test.columns):
            # This is a detailed file
            print(f"Processing detailed file: {filename}")
            df = pd.read_excel(file_path, sheet_name=0, header=8)
        else:
            # This might be a summary file, try to find the right header
            print(f"Processing summary file: {filename}")
            # For summary files, look for header containing "Código" or "Organismo"
            for header_row in range(15):
                try:
                    df_test = pd.read_excel(file_path, sheet_name=0, header=header_row, nrows=3)
                    if any('Código' in str(col) or 'Organismo' in str(col) for col in df_test.columns):
                        df = pd.read_excel(file_path, sheet_name=0, header=header_row)
                        break
                except:
                    continue
            else:
                # If no proper header found, read with header=None and process manually
                df = pd.read_excel(file_path, sheet_name=0, header=None)
        
        print(f"Successfully read {filename}: {df.shape}")
        return df, periodo_corte
        
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None, periodo_corte


def process_detailed_file(df: pd.DataFrame, periodo_corte: str, filename: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Process detailed Excel file and extract activities, products, and summary data."""
    
    # Normalize column names
    df.columns = normalize_column_names(df.columns)
    
    print(f"Normalized columns for {filename}: {list(df.columns)[:10]}...")
    
    # Column mapping for detailed files
    column_mapping = {
        'cod_centro_gestor': ['cod_centro_gestor', 'codigo_centro_gestor', 'centro_gestor'],
        'bpin': ['cod_bpin', 'codigo_bpin', 'bpin'],
        'cod_pd_lvl_1': ['nivel_1_pd_cod', 'cod_nivel_1', 'nivel1_cod'],
        'cod_pd_lvl_2': ['nivel_2_pd_cod', 'cod_nivel_2', 'nivel2_cod'],
        'cod_pd_lvl_3': ['nivel_3_pd_cod', 'cod_nivel_3', 'nivel3_cod'],
        'cod_actividad': ['cod_actividad', 'codigo_actividad'],
        'nombre_actividad': ['nombre_actividad'],
        'cod_producto': ['cod_producto_mga', 'codigo_producto_mga', 'cod_producto'],
        'nombre_producto': ['nombre_producto_mga', 'nombre_producto'],
        'subdireccion_subsecretaria': ['subdireccion___subsecretaria', 'subdireccion_subsecretaria'],
        'ponderacion_actividad': ['ponderacion_de_actividad', 'ponderacion_actividad'],
        'avance_actividad': ['pct_de_avance_actividad_trimestre_i', 'avance_actividad_trim_1'],
        'avance_real_actividad': ['pct_de_avance_actividad_trimestre_ii', 'avance_actividad_trim_2'],
        'avance_actividad_acumulado': ['pct_avance_proyecto', 'avance_proyecto'],
        'cantidad_programada_producto': ['cantidad_programada_producto'],
        'ponderacion_producto': ['ponderacion_producto'],
        'avance_producto': ['ejecucion_fisica_trimestre_i', 'avance_producto_trim_1'],
        'ejecucion_fisica_producto': ['ejecucion_fisica_trimestre_ii', 'avance_producto_trim_2'],
        'avance_real_producto': ['pct_de_avance_producto', 'avance_producto'],
        'avance_producto_acumulado': ['pct_de_avance_producto_1', 'avance_producto_acum'],
        'ejecucion_ppto_producto': ['ejecucion', 'ejecucion_presupuestal'],
        'ppto_inicial_actividad': ['presupuesto_inicial'],
        'ppto_modificado_actividad': ['presupuesto_modificado'],
        'ejecucion_actividad': ['ejecucion'],
        'obligado_actividad': ['obligado'],
        'pagos_actividad': ['pagos'],
        'fecha_inicio_actividad': ['fecha_inicio'],
        'fecha_fin_actividad': ['fecha_fin'],
        'tipo_meta_producto': ['meta_pd', 'denominacion_meta_pd'],
        'descripcion_avance_producto': ['explicacion_producto_trim_i'],
        'descripcion_actividad': ['explicacion_actividad_trim_i']
    }
    
    # Create standardized dataframes
    activities_data = []
    products_data = []
    summary_data = []
    
    # Process each row
    for _, row in df.iterrows():
        # Skip rows where BPIN is missing
        bpin_val = None
        for col in df.columns:
            if any(keyword in col for keyword in ['bpin', 'cod_bpin']):
                bpin_val = clean_integer_value(row[col])
                break
        
        if bpin_val is None:
            continue
        
        # Extract common fields
        cod_centro_gestor = None
        for col in df.columns:
            if any(keyword in col for keyword in ['cod_centro_gestor', 'centro_gestor']):
                cod_centro_gestor = clean_integer_value(row[col])
                break
        
        cod_actividad = None
        for col in df.columns:
            if 'cod_actividad' in col:
                cod_actividad = clean_integer_value(row[col])
                break
        
        cod_producto = None
        for col in df.columns:
            if any(keyword in col for keyword in ['cod_producto', 'producto_mga']):
                cod_producto = clean_integer_value(row[col])
                break
        
        # Extract level codes
        cod_pd_lvl_1 = None
        cod_pd_lvl_2 = None
        cod_pd_lvl_3 = None
        for col in df.columns:
            if 'nivel_1_pd_cod' in col:
                cod_pd_lvl_1 = clean_integer_value(row[col])
            elif 'nivel_2_pd_cod' in col:
                cod_pd_lvl_2 = clean_integer_value(row[col])
            elif 'nivel_3_pd_cod' in col:
                cod_pd_lvl_3 = clean_integer_value(row[col])
        
        subdireccion = None
        for col in df.columns:
            if 'subdireccion' in col or 'subsecretaria' in col:
                subdireccion = str(row[col]) if pd.notna(row[col]) else None
                break
        
        # Create activities record
        if cod_actividad is not None:
            nombre_actividad = None
            for col in df.columns:
                if 'nombre_actividad' in col:
                    nombre_actividad = str(row[col]) if pd.notna(row[col]) else None
                    break
            
            descripcion_actividad = None
            for col in df.columns:
                if 'explicacion_actividad' in col:
                    descripcion_actividad = str(row[col]) if pd.notna(row[col]) else None
                    break
            
            # Extract activity financial data
            ppto_inicial_actividad = 0.0
            ppto_modificado_actividad = 0.0
            ejecucion_actividad = 0.0
            obligado_actividad = 0.0
            pagos_actividad = 0.0
            
            for col in df.columns:
                if 'presupuesto_inicial' in col:
                    ppto_inicial_actividad = clean_numeric_value(row[col])
                elif 'presupuesto_modificado' in col:
                    ppto_modificado_actividad = clean_numeric_value(row[col])
                elif col == 'ejecucion':
                    ejecucion_actividad = clean_numeric_value(row[col])
                elif col == 'obligado':
                    obligado_actividad = clean_numeric_value(row[col])
                elif col == 'pagos':
                    pagos_actividad = clean_numeric_value(row[col])
            
            # Extract activity progress data
            avance_actividad = 0.0
            avance_real_actividad = 0.0
            avance_actividad_acumulado = 0.0
            ponderacion_actividad = 0.0
            
            for col in df.columns:
                if 'ponderacion_de_actividad' in col:
                    ponderacion_actividad = clean_numeric_value(row[col])
                elif 'pct_de_avance_actividad_trimestre_i' in col:
                    avance_actividad = clean_numeric_value(row[col])
                elif 'pct_de_avance_actividad_trimestre_ii' in col:
                    avance_real_actividad = clean_numeric_value(row[col])
                elif 'pct_avance_proyecto' in col:
                    avance_actividad_acumulado = clean_numeric_value(row[col])
            
            # Extract dates
            fecha_inicio_actividad = None
            fecha_fin_actividad = None
            for col in df.columns:
                if 'fecha_inicio' in col:
                    fecha_inicio_actividad = clean_date_value(row[col])
                elif 'fecha_fin' in col:
                    fecha_fin_actividad = clean_date_value(row[col])
            
            activities_data.append({
                'bpin': bpin_val,
                'cod_actividad': cod_actividad,
                'cod_centro_gestor': cod_centro_gestor,
                'nombre_actividad': nombre_actividad,
                'descripcion_actividad': descripcion_actividad,
                'periodo_corte': periodo_corte,
                'fecha_inicio_actividad': fecha_inicio_actividad,
                'fecha_fin_actividad': fecha_fin_actividad,
                'ppto_inicial_actividad': ppto_inicial_actividad,
                'ppto_modificado_actividad': ppto_modificado_actividad,
                'ejecucion_actividad': ejecucion_actividad,
                'obligado_actividad': obligado_actividad,
                'pagos_actividad': pagos_actividad,
                'avance_actividad': avance_actividad,
                'avance_real_actividad': avance_real_actividad,
                'avance_actividad_acumulado': avance_actividad_acumulado,
                'ponderacion_actividad': ponderacion_actividad
            })
        
        # Create products record
        if cod_producto is not None:
            nombre_producto = None
            for col in df.columns:
                if 'nombre_producto' in col:
                    nombre_producto = str(row[col]) if pd.notna(row[col]) else None
                    break
            
            tipo_meta_producto = None
            for col in df.columns:
                if 'meta_pd' in col or 'denominacion_meta' in col:
                    tipo_meta_producto = str(row[col]) if pd.notna(row[col]) else None
                    break
            
            descripcion_avance_producto = None
            for col in df.columns:
                if 'explicacion_producto' in col:
                    descripcion_avance_producto = str(row[col]) if pd.notna(row[col]) else None
                    break
            
            # Extract product metrics
            cantidad_programada_producto = 0.0
            ponderacion_producto = 0.0
            avance_producto = 0.0
            ejecucion_fisica_producto = 0.0
            avance_real_producto = 0.0
            avance_producto_acumulado = 0.0
            ejecucion_ppto_producto = 0.0
            
            for col in df.columns:
                if 'cantidad_programada_producto' in col:
                    cantidad_programada_producto = clean_numeric_value(row[col])
                elif 'ponderacion_producto' in col:
                    ponderacion_producto = clean_numeric_value(row[col])
                elif 'ejecucion_fisica_trimestre_i' in col:
                    avance_producto = clean_numeric_value(row[col])
                elif 'ejecucion_fisica_trimestre_ii' in col:
                    ejecucion_fisica_producto = clean_numeric_value(row[col])
                elif 'pct_de_avance_producto' in col and 'pct_de_avance_producto_' not in col:
                    avance_real_producto = clean_numeric_value(row[col])
                elif 'pct_de_avance_producto_1' in col:
                    avance_producto_acumulado = clean_numeric_value(row[col])
                elif col == 'ejecucion':
                    ejecucion_ppto_producto = clean_numeric_value(row[col])
            
            products_data.append({
                'bpin': bpin_val,
                'cod_producto': cod_producto,
                'cod_producto_mga': cod_producto,  # Same value
                'nombre_producto': nombre_producto,
                'tipo_meta_producto': tipo_meta_producto,
                'descripcion_avance_producto': descripcion_avance_producto,
                'periodo_corte': periodo_corte,
                'cantidad_programada_producto': cantidad_programada_producto,
                'ponderacion_producto': ponderacion_producto,
                'avance_producto': avance_producto,
                'ejecucion_fisica_producto': ejecucion_fisica_producto,
                'avance_real_producto': avance_real_producto,
                'avance_producto_acumulado': avance_producto_acumulado,
                'ejecucion_ppto_producto': ejecucion_ppto_producto
            })
        
        # Create summary record
        avance_proyecto_pa = 0.0
        ejecucion_ppto_proyecto_pa = 0.0
        
        for col in df.columns:
            if 'pct_avance_proyecto' in col:
                avance_proyecto_pa = clean_numeric_value(row[col])
            elif col == 'ejecucion':
                ejecucion_ppto_proyecto_pa = clean_numeric_value(row[col])
        
        summary_data.append({
            'bpin': bpin_val,
            'cod_pd_lvl_1': cod_pd_lvl_1,
            'cod_pd_lvl_2': cod_pd_lvl_2,
            'cod_pd_lvl_3': cod_pd_lvl_3,
            'cod_actividad': cod_actividad,
            'cod_producto': cod_producto,
            'subdireccion_subsecretaria': subdireccion,
            'periodo_corte': periodo_corte,
            'avance_proyecto_pa': avance_proyecto_pa,
            'ejecucion_ppto_proyecto_pa': ejecucion_ppto_proyecto_pa
        })
    
    # Convert to DataFrames
    df_activities = pd.DataFrame(activities_data) if activities_data else pd.DataFrame()
    df_products = pd.DataFrame(products_data) if products_data else pd.DataFrame()
    df_summary = pd.DataFrame(summary_data) if summary_data else pd.DataFrame()
    
    return df_activities, df_products, df_summary


def seguimiento_pa_transformer(data_directory: str = "transformation_app/app_inputs/seguimiento_pa_input") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Transform project monitoring data from Excel files into standardized DataFrames.
    
    Args:
        data_directory (str): Path to the directory containing Excel files.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: Activities, Products, and Summary DataFrames.
    """
    
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    directory_path = os.path.join(parent_dir, data_directory)
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # List all files in the directory
    files = os.listdir(directory_path)
    
    # Filter for Excel files
    excel_files = [f for f in files if f.endswith(('.xlsx', '.xls'))]
    
    if not excel_files:
        raise ValueError(f"No Excel files found in {directory_path}")
    
    print(f"Loading {len(excel_files)} Excel files from {directory_path}")
    
    # Lists to store all dataframes
    all_activities = []
    all_products = []
    all_summary = []
    
    # Process each Excel file
    for file_name in excel_files:
        file_path = os.path.join(directory_path, file_name)
        print(f"\nProcessing: {file_name}")
        
        df, periodo_corte = read_excel_file(file_path)
        
        if df is not None:
            try:
                df_activities, df_products, df_summary = process_detailed_file(df, periodo_corte, file_name)
                
                if not df_activities.empty:
                    df_activities['archivo_origen'] = file_name
                    all_activities.append(df_activities)
                    print(f"  ✓ Activities: {len(df_activities)} records")
                
                if not df_products.empty:
                    df_products['archivo_origen'] = file_name
                    all_products.append(df_products)
                    print(f"  ✓ Products: {len(df_products)} records")
                
                if not df_summary.empty:
                    df_summary['archivo_origen'] = file_name
                    all_summary.append(df_summary)
                    print(f"  ✓ Summary: {len(df_summary)} records")
                    
            except Exception as e:
                print(f"  ✗ Error processing {file_name}: {e}")
                continue
        else:
            print(f"  ✗ Could not read {file_name}")
    
    # Concatenate all dataframes
    print(f"\nConcatenating all processed data...")
    
    df_consolidated_activities = pd.concat(all_activities, ignore_index=True) if all_activities else pd.DataFrame()
    df_consolidated_products = pd.concat(all_products, ignore_index=True) if all_products else pd.DataFrame()
    df_consolidated_summary = pd.concat(all_summary, ignore_index=True) if all_summary else pd.DataFrame()
    
    # Remove duplicates based on key columns
    if not df_consolidated_activities.empty:
        df_consolidated_activities = df_consolidated_activities.drop_duplicates(
            subset=['bpin', 'cod_actividad', 'periodo_corte'], keep='last'
        ).reset_index(drop=True)
    
    if not df_consolidated_products.empty:
        df_consolidated_products = df_consolidated_products.drop_duplicates(
            subset=['bpin', 'cod_producto', 'periodo_corte'], keep='last'
        ).reset_index(drop=True)
    
    if not df_consolidated_summary.empty:
        df_consolidated_summary = df_consolidated_summary.drop_duplicates(
            subset=['bpin', 'periodo_corte'], keep='last'
        ).reset_index(drop=True)
    
    print(f"Final consolidated data:")
    print(f"  Activities: {len(df_consolidated_activities)} records")
    print(f"  Products: {len(df_consolidated_products)} records")
    print(f"  Summary: {len(df_consolidated_summary)} records")
    
    return df_consolidated_activities, df_consolidated_products, df_consolidated_summary


def save_to_json(dataframes: Dict[str, pd.DataFrame], output_directory: str):
    """Save dataframes to JSON files."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    print(f"Output directory: {output_directory}")
    
    saved_files = []
    failed_files = []
    
    for df_name, dataframe in dataframes.items():
        if dataframe is not None and not dataframe.empty:
            try:
                # Convert nullable integer columns to regular int for JSON compatibility
                df_copy = dataframe.copy()
                
                # Handle different data types for JSON compatibility
                for col in df_copy.columns:
                    if df_copy[col].dtype == 'Int64':
                        # Convert Int64 to float first (to handle NaN), then to object for JSON
                        df_copy[col] = df_copy[col].astype('float64').where(df_copy[col].notna(), None)
                        # Convert non-null values back to int
                        df_copy[col] = df_copy[col].apply(lambda x: int(x) if pd.notna(x) else None)
                    elif df_copy[col].dtype == 'float64':
                        # Round float values to 2 decimal places
                        df_copy[col] = df_copy[col].round(2)
                
                # Save to JSON with proper formatting
                json_filename = f"{df_name}.json"
                json_filepath = os.path.join(output_directory, json_filename)
                
                # Convert to JSON with orient='records' for API compatibility
                df_copy.to_json(
                    json_filepath, 
                    orient='records', 
                    indent=2,
                    force_ascii=False,
                    date_format='iso'
                )
                
                file_size = os.path.getsize(json_filepath) / 1024  # Size in KB
                print(f"✓ Saved {df_name}: {json_filename} ({len(dataframe)} rows, {file_size:.1f} KB)")
                saved_files.append(json_filename)
                
            except Exception as e:
                print(f"✗ Failed to save {df_name}: {e}")
                failed_files.append(df_name)
        else:
            print(f"⚠ Skipped {df_name}: DataFrame is empty or None")
            failed_files.append(df_name)
    
    # Summary
    print(f"\nSave Summary:")
    print(f"Successfully saved: {len(saved_files)} files")
    if failed_files:
        print(f"Failed to save: {len(failed_files)} files")
    
    return saved_files, failed_files


def main():
    """Main function for testing the transformer."""
    try:
        print("="*80)
        print("SEGUIMIENTO PA DATA TRANSFORMATION")
        print("="*80)
        
        # Transform the data
        df_activities, df_products, df_summary = seguimiento_pa_transformer()
        
        print(f"\n" + "="*60)
        print(f"TRANSFORMATION SUMMARY:")
        print(f"="*60)
        
        # Display summary for each dataframe
        dataframes_info = [
            ("Activities (seguimiento_actividades_pa)", df_activities),
            ("Products (seguimiento_productos_pa)", df_products),
            ("Summary (seguimiento_pa)", df_summary)
        ]
        
        for name, df in dataframes_info:
            if df.empty:
                print(f"\n{name}: EMPTY")
            else:
                print(f"\n{name}:")
                print(f"  Rows: {len(df):,}")
                print(f"  Columns: {len(df.columns)}")
                print(f"  Unique BPINs: {df['bpin'].nunique() if 'bpin' in df.columns else 'N/A'}")
                print(f"  Period range: {df['periodo_corte'].min()} to {df['periodo_corte'].max()}" if 'periodo_corte' in df.columns else "")
                print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
                
                # Show sample data
                if len(df) > 0:
                    print(f"  Sample columns: {list(df.columns)[:8]}")
                    print(f"  First row sample:")
                    first_row = df.iloc[0]
                    for col in df.columns[:5]:
                        print(f"    {col}: {first_row[col]}")
        
        # Define output directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "app_outputs", "seguimiento_pa_outputs")
        
        # Save dataframes to JSON files
        print(f"\n" + "="*60)
        print(f"SAVING TO JSON FILES:")
        print(f"="*60)
        
        dataframes_to_save = {
            "seguimiento_actividades_pa": df_activities,
            "seguimiento_productos_pa": df_products,
            "seguimiento_pa": df_summary
        }
        
        saved_files, failed_files = save_to_json(dataframes_to_save, output_dir)
        
        print(f"\nOutput directory: {output_dir}")
        print(f"Total files created: {len(saved_files)}")
        
        # Show file details
        if saved_files:
            print(f"\nCreated files:")
            for filename in saved_files:
                filepath = os.path.join(output_dir, filename)
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath) / 1024  # Size in KB
                    print(f"  {filename}: {file_size:.1f} KB")
        
        return df_activities, df_products, df_summary
        
    except Exception as e:
        print(f"Error in transformation: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


if __name__ == "__main__":
    df_activities, df_products, df_summary = main()
