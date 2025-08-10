# -*- coding: utf-8 -*-
"""
Data transformation module for budget execution data processing.
Simple concatenation of all CSV files from downloaded_data directory.
"""

import os
import pandas as pd
from typing import Optional


def normalize_column_names(columns):
    """Normalize column names by converting to lowercase and removing special characters."""
    return [col.lower().strip().replace(' ', '_').replace('.', '_').replace('(', '').replace(')', '') for col in columns]


def ejecucion_presupuestal_transformer(data_directory: str = "transformation_app/app_inputs/ejecucion_presupuestal_input") -> pd.DataFrame:
    """
    Creates a unified dataframe by combining all CSV files from the downloaded_data directory.
    Simply concatenates all tables vertically without losing any data.
    
    Args:
        data_directory (str): Path to the directory containing CSV files. Defaults to "downloaded_data".
        
    Returns:
        pd.DataFrame: Consolidated dataframe with all budget execution data.
    """
    
    # Define standardized column names according to your requirements
    standard_columns = [
        'bpin', 'bp', 'cod_area_funcional', 'nombre_area_funcional', 'cod_centro_gestor', 'nombre_centro_gestor', 'cod_comuna', 
        'cod_dimension', 'nombre_dimension', 'cod_linea_estrategica', 'nombre_linea_estrategica', 'cod_actividad', 'cod_sector', 
        'cod_proposito', 'nombre_proposito', 'cod_reto', 'nombre_reto', 'cod_pospre', 'cod_programa', 'nombre_programa',
        'cod_fuente_financiamiento', 'cod_categoria_alcalde', 'nombre_proyecto_bpin', 
        'nombre_bp', 'tipo_proyecto', 'anio_inicio', 'periodo_corte', 'ppto_inicial', 
        'adiciones', 'reducciones', 'ppto_modificado', 'ejecucion', 'pagos', 
        'saldos_cdp', 'total_acumul_obligac', 'total_acumulado_cdp', 'total_acumulado_rpc'
    ]
    
    # Comprehensive mapping from various source column names to standard names
    column_mapping = {
        # Project identifiers
        'bpin': 'bpin',
        'bp': 'bp',
        'codigo_bpin': 'bpin',
        'codigo_bp': 'bp',
        'cod_bpin': 'bpin',
        'cod_bp': 'bp',
        
        # Functional codes
        'cod_area_funcional': 'cod_area_funcional',
        'codigo_area_funcional': 'cod_area_funcional',
        'area_funcional': 'cod_area_funcional',
        
        # Add mapping for nombre_area_funcional
        'nombre_area_funcional': 'nombre_area_funcional',
        'nombre_de_area_funcional': 'nombre_area_funcional',
        'nom_area_funcional': 'nombre_area_funcional',
        'area_funcional_nombre': 'nombre_area_funcional',
        'nombre_del_area_funcional': 'nombre_area_funcional',
        
        'cod_centro_gestor': 'cod_centro_gestor',
        'codigo_centro_gestor': 'cod_centro_gestor',
        'centro_gestor': 'cod_centro_gestor',
        
        # Add mapping for nombre_centro_gestor
        'nombre_centro_gestor': 'nombre_centro_gestor',
        'nombre_del_centro_gestor': 'nombre_centro_gestor',
        'nom_centro_gestor': 'nombre_centro_gestor',
        'centro_gestor_nombre': 'nombre_centro_gestor',
        
        'cod_comuna': 'cod_comuna',
        'codigo_comuna': 'cod_comuna',
        'comuna': 'cod_comuna',
        
        'cod_dimension': 'cod_dimension',
        'codigo_dimension': 'cod_dimension',
        'dimension': 'cod_dimension',
        
        # Add mapping for nombre_dimension
        'nombre_dimension': 'nombre_dimension',
        'nombre_de_dimension': 'nombre_dimension',
        'nom_dimension': 'nombre_dimension',
        'dimension_nombre': 'nombre_dimension',
        'nombre_de_la_dimension': 'nombre_dimension',
        
        'cod_linea_estrategica': 'cod_linea_estrategica',
        'codigo_linea_estrategica': 'cod_linea_estrategica',
        'linea_estrategica': 'cod_linea_estrategica',
        
        # Add mapping for nombre_linea_estrategica
        'nombre_linea_estrategica': 'nombre_linea_estrategica',
        'nombre_de_linea_estrategica': 'nombre_linea_estrategica',
        'nom_linea_estrategica': 'nombre_linea_estrategica',
        'linea_estrategica_nombre': 'nombre_linea_estrategica',
        'nombre_de_la_linea_estrategica': 'nombre_linea_estrategica',
        
        'cod_actividad': 'cod_actividad',
        'codigo_actividad': 'cod_actividad',
        'actividad': 'cod_actividad',
        
        'cod_sector': 'cod_sector',
        'codigo_sector': 'cod_sector',
        'sector': 'cod_sector',
        
        'cod_proposito': 'cod_proposito',
        'codigo_proposito': 'cod_proposito',
        'proposito': 'cod_proposito',
        'propósito': 'cod_proposito',  # Added for Spanish accent
        
        # Add mapping for nombre_proposito with various formats
        'nombre_proposito': 'nombre_proposito',
        'nombre_del_proposito': 'nombre_proposito',
        'nom_proposito': 'nombre_proposito',
        'proposito_nombre': 'nombre_proposito',
        'nombre_de_proposito': 'nombre_proposito',
        'nombre_propósito': 'nombre_proposito',  # Added for Spanish accent
        'nombre propósito': 'nombre_proposito',  # Added for space and accent
        
        'cod_reto': 'cod_reto',
        'codigo_reto': 'cod_reto',
        'reto': 'cod_reto',
        
        # Add mapping for nombre_reto
        'nombre_reto': 'nombre_reto',
        'nombre_del_reto': 'nombre_reto',
        'nom_reto': 'nombre_reto',
        'reto_nombre': 'nombre_reto',
        'nombre_de_reto': 'nombre_reto',
        
        'cod_pospre': 'cod_pospre',
        'codigo_pospre': 'cod_pospre',
        'pospre': 'cod_pospre',
        
        'cod_programa': 'cod_programa',
        'codigo_programa': 'cod_programa',
        'programa': 'cod_programa',
        
        # Add mapping for nombre_programa
        'nombre_programa': 'nombre_programa',
        'nombre_del_programa': 'nombre_programa',
        'nom_programa': 'nombre_programa',
        'programa_nombre': 'nombre_programa',
        'nombre_de_programa': 'nombre_programa',
        
        'cod_fuente_financiamiento': 'cod_fuente_financiamiento',
        'codigo_fuente_financiamiento': 'cod_fuente_financiamiento',
        'fuente_financiamiento': 'cod_fuente_financiamiento',
        
        'cod_categoria_alcalde': 'cod_categoria_alcalde',
        'codigo_categoria_alcalde': 'cod_categoria_alcalde',
        'categoria_alcalde': 'cod_categoria_alcalde',
        
        # Project names and types
        'nombre_proyecto_bpin': 'nombre_proyecto_bpin',
        'nombre_proyecto': 'nombre_proyecto_bpin',
        'proyecto_bpin': 'nombre_proyecto_bpin',
        'nombre_del_proyecto': 'nombre_proyecto_bpin',
        
        'nombre_bp': 'nombre_bp',
        'nombre_proyecto_bp': 'nombre_bp',
        'proyecto_bp': 'nombre_bp',
        'nompre_bp': 'nombre_bp',
        
        'tipo_proyecto': 'tipo_proyecto',
        'tipo': 'tipo_proyecto',
        
        'anio_inicio': 'anio_inicio',
        'año_inicio': 'anio_inicio',
        'año': 'anio_inicio',
        
        # Time period
        'periodo_corte': 'periodo_corte',
        'periodo': 'periodo_corte',
        'corte': 'periodo_corte',
        
        # Budget amounts
        'ppto_inicial': 'ppto_inicial',
        'presupuesto_inicial': 'ppto_inicial',
        'ppuesto_inicial': 'ppto_inicial',
        
        'adiciones': 'adiciones',
        'adicion': 'adiciones',
        
        'reducciones': 'reducciones',
        'reduccion': 'reducciones',
        
        'ppto_modificado': 'ppto_modificado',
        'presupuesto_modificado': 'ppto_modificado',
        'ppuesto_modificado': 'ppto_modificado',
        'ppto__modificado': 'ppto_modificado',
        
        # Execution amounts
        'ejecucion': 'ejecucion',
        'ejecutado': 'ejecucion',
        
        'pagos': 'pagos',
        'pago': 'pagos',
        
        'saldos_cdp': 'saldos_cdp',
        'saldo_cdp': 'saldos_cdp',
        
        'total_acumul_obligac': 'total_acumul_obligac',
        'total_acumulado_obligaciones': 'total_acumul_obligac',
        'acumulado_obligaciones': 'total_acumul_obligac',
        
        'total_acumulado_cdp': 'total_acumulado_cdp',
        'acumulado_cdp': 'total_acumulado_cdp',
        
        'total_acumulado_rpc': 'total_acumulado_rpc',
        'acumulado_rpc': 'total_acumulado_rpc'
    }
    
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    directory_path = os.path.join(parent_dir, data_directory)
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # List all files in the directory
    files = os.listdir(directory_path)
    
    # Filter for CSV files
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if not csv_files:
        raise ValueError(f"No CSV files found in {directory_path}")
    
    # Dictionary to store all dataframes
    dfs = {}
    
    # Load all CSV files
    print(f"Loading {len(csv_files)} CSV files from {directory_path}")
    
    for file_name in csv_files:
        file_path = os.path.join(directory_path, file_name)
        try:
            # Read CSV with semicolon delimiter and skip bad lines
            df = pd.read_csv(file_path, sep=';', on_bad_lines='skip', encoding='utf-8', low_memory=False)
            
            print(f"\nOriginal columns in '{file_name}': {list(df.columns)}")
            
            df_name = os.path.splitext(file_name)[0]
            dfs[df_name] = df
            
            print(f"Successfully loaded '{file_name}' with shape {df.shape}")
            
        except Exception as e:
            print(f"Error loading '{file_name}': {e}")
            continue
    
    if not dfs:
        raise ValueError("No CSV files could be loaded successfully")
    
    # Standardize all dataframes
    standardized_dfs = []
    
    for df_name, df in dfs.items():
        # 1. Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # 2. Normalize column names
        df.columns = normalize_column_names(df.columns)
        
        # Debug: Print column names to see what we have
        print(f"\nDataFrame {df_name} columns after normalization: {list(df.columns)}")
        
        # 3. Rename columns using the comprehensive map
        df.rename(columns=column_mapping, inplace=True)
        
        # 4. Handle potential duplicate columns after renaming
        df = df.loc[:,~df.columns.duplicated()]
        
        # 5. Remove any 'rubro' related columns
        columns_to_remove = ['rubro', 'cod_rubro', 'codigo_rubro']
        df = df.drop(columns=[col for col in columns_to_remove if col in df.columns], errors='ignore')
        
        # 6. Add year and origin metadata
        year = df_name.split('_')[-1]
        if year.isdigit():
            df['anio'] = int(year)
        elif '2024' in df_name:
            df['anio'] = 2024
        elif '2025' in df_name:
            df['anio'] = 2025
        else:
            df['anio'] = None
            
        df['dataframe_origen'] = df_name
        df['archivo_origen'] = f"{df_name}.csv"
        
        # 7. Create a new DataFrame with only the standard columns
        new_df = pd.DataFrame()
        
        # Add all standard columns to the new dataframe
        for col in standard_columns:
            if col in df.columns:
                new_df[col] = df[col]
            else:
                new_df[col] = None
        
        # Convert cod_centro_gestor to integer
        if 'cod_centro_gestor' in new_df.columns:
            try:
                # Convert to numeric, replacing non-numeric values with NaN
                new_df['cod_centro_gestor'] = pd.to_numeric(new_df['cod_centro_gestor'], errors='coerce')
                # Convert to integer, keeping NaN as NaN
                new_df['cod_centro_gestor'] = new_df['cod_centro_gestor'].astype('Int64')  # nullable integer
                print(f"Converted cod_centro_gestor to integer for {df_name}")
            except Exception as e:
                print(f"Warning: Could not convert cod_centro_gestor to integer for {df_name}: {e}")
        
        # Convert cod_area_funcional to integer
        if 'cod_area_funcional' in new_df.columns:
            try:
                # Convert to numeric, replacing non-numeric values with NaN
                new_df['cod_area_funcional'] = pd.to_numeric(new_df['cod_area_funcional'], errors='coerce')
                # Convert to integer, keeping NaN as NaN
                new_df['cod_area_funcional'] = new_df['cod_area_funcional'].astype('Int64')  # nullable integer
                print(f"Converted cod_area_funcional to integer for {df_name}")
            except Exception as e:
                print(f"Warning: Could not convert cod_area_funcional to integer for {df_name}: {e}")
        
        # Convert cod_programa to integer
        if 'cod_programa' in new_df.columns:
            try:
                # Convert to numeric, replacing non-numeric values with NaN
                new_df['cod_programa'] = pd.to_numeric(new_df['cod_programa'], errors='coerce')
                # Convert to integer, keeping NaN as NaN
                new_df['cod_programa'] = new_df['cod_programa'].astype('Int64')  # nullable integer
                print(f"Converted cod_programa to integer for {df_name}")
            except Exception as e:
                print(f"Warning: Could not convert cod_programa to integer for {df_name}: {e}")
        
        # Convert cod_linea_estrategica to integer
        if 'cod_linea_estrategica' in new_df.columns:
            try:
                # Convert to numeric, replacing non-numeric values with NaN
                new_df['cod_linea_estrategica'] = pd.to_numeric(new_df['cod_linea_estrategica'], errors='coerce')
                # Convert to integer, keeping NaN as NaN
                new_df['cod_linea_estrategica'] = new_df['cod_linea_estrategica'].astype('Int64')  # nullable integer
                print(f"Converted cod_linea_estrategica to integer for {df_name}")
            except Exception as e:
                print(f"Warning: Could not convert cod_linea_estrategica to integer for {df_name}: {e}")
        
        # Convert cod_dimension to integer
        if 'cod_dimension' in new_df.columns:
            try:
                # Convert to numeric, replacing non-numeric values with NaN
                new_df['cod_dimension'] = pd.to_numeric(new_df['cod_dimension'], errors='coerce')
                # Convert to integer, keeping NaN as NaN
                new_df['cod_dimension'] = new_df['cod_dimension'].astype('Int64')  # nullable integer
                print(f"Converted cod_dimension to integer for {df_name}")
            except Exception as e:
                print(f"Warning: Could not convert cod_dimension to integer for {df_name}: {e}")
        
        # Convert cod_proposito to integer
        if 'cod_proposito' in new_df.columns:
            try:
                # Convert to numeric, replacing non-numeric values with NaN
                new_df['cod_proposito'] = pd.to_numeric(new_df['cod_proposito'], errors='coerce')
                # Convert to integer, keeping NaN as NaN
                new_df['cod_proposito'] = new_df['cod_proposito'].astype('Int64')  # nullable integer
                print(f"Converted cod_proposito to integer for {df_name}")
            except Exception as e:
                print(f"Warning: Could not convert cod_proposito to integer for {df_name}: {e}")
                
        # Convert cod_reto to integer
        if 'cod_reto' in new_df.columns:
            try:
                # Convert to numeric, replacing non-numeric values with NaN
                new_df['cod_reto'] = pd.to_numeric(new_df['cod_reto'], errors='coerce')
                # Convert to integer, keeping NaN as NaN
                new_df['cod_reto'] = new_df['cod_reto'].astype('Int64')  # nullable integer
                print(f"Converted cod_reto to integer for {df_name}")
            except Exception as e:
                print(f"Warning: Could not convert cod_reto to integer for {df_name}: {e}")
                
        # Add metadata columns
        new_df['anio'] = df['anio']
        new_df['dataframe_origen'] = df['dataframe_origen']
        new_df['archivo_origen'] = df['archivo_origen']
        
        standardized_dfs.append(new_df)
        print(f"Standardized DataFrame {df_name} with shape {new_df.shape}")
    
    # Concatenate all standardized dataframes
    print("\nConcatenating all standardized dataframes...")
    
    try:
        df_consolidado = pd.concat(standardized_dfs, ignore_index=True, sort=False)
        print("Concatenation successful!")
    except Exception as e:
        print(f"Concatenation failed with error: {e}")
        return None
    
    print(f"\nSuccessfully created consolidated dataframe!")
    print(f"Shape: {df_consolidado.shape} (Rows: {df_consolidado.shape[0]}, Columns: {df_consolidado.shape[1]})")
    print(f"\nAll column names ({len(df_consolidado.columns)}):")
    for i, col in enumerate(df_consolidado.columns):
        print(f"{i+1:2d}. {col}")
    
    # Show head of the dataframe
    print(f"\nDataframe head():")
    print(df_consolidado.head())
    
    print(f"\nDataframe info:")
    print(f"Non-null counts by column:")
    for col in df_consolidado.columns:
        non_null_count = df_consolidado[col].notna().sum()
        print(f"  {col}: {non_null_count}/{len(df_consolidado)} ({non_null_count/len(df_consolidado)*100:.1f}%)")
    
    return df_consolidado  # Only return the consolidated dataframe


# Example usage function for testing
def main():
    """Main function for testing the transformer."""
    try:
        df_consolidado = ejecucion_presupuestal_transformer()
        print(f"\n" + "="*60)
        print(f"FINAL CONSOLIDATED DATAFRAME SUMMARY:")
        print(f"="*60)
        print(f"Rows: {df_consolidado.shape[0]:,}")
        print(f"Columns: {df_consolidado.shape[1]}")
        print(f"Memory usage: {df_consolidado.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Print all columns in df
        print(f"\n" + "="*60)
        print(f"ALL COLUMNS IN DF:")
        print(f"="*60)
        print(f"df.columns = {list(df_consolidado.columns)}")
        print(f"\nColumns numbered:")
        for i, col in enumerate(df_consolidado.columns):
            print(f"{i+1:2d}. '{col}'")
        
        # Create centros_gestores dataframe with unique values
        print(f"\n" + "="*60)
        print(f"CREATING CENTROS_GESTORES DATAFRAME:")
        print(f"="*60)
        
        # Check if the required columns exist
        if 'cod_centro_gestor' in df_consolidado.columns:
            print(f"Found 'cod_centro_gestor' column in dataframe")
            
            # Check for nombre_centro_gestor column
            nombre_centro_gestor_cols = [col for col in df_consolidado.columns if 'nombre' in col.lower() and 'centro' in col.lower() and 'gestor' in col.lower()]
            print(f"Available nombre_centro_gestor related columns: {nombre_centro_gestor_cols}")
            
            # Create the dataframe with unique combinations
            if nombre_centro_gestor_cols:
                # Use the first found nombre_centro_gestor column
                nombre_col = nombre_centro_gestor_cols[0]
                centros_gestores = df_consolidado[['cod_centro_gestor', nombre_col]].copy()
                centros_gestores.columns = ['cod_centro_gestor', 'nombre_centro_gestor']
                print(f"Using column '{nombre_col}' as nombre_centro_gestor")
            else:
                # Create dataframe with only cod_centro_gestor and set nombre to None
                centros_gestores = df_consolidado[['cod_centro_gestor']].copy()
                centros_gestores['nombre_centro_gestor'] = None
                print("Warning: No 'nombre_centro_gestor' column found, setting to None")
            
            # Remove rows where cod_centro_gestor is null
            initial_rows = len(centros_gestores)
            centros_gestores = centros_gestores.dropna(subset=['cod_centro_gestor'])
            after_dropna = len(centros_gestores)
            print(f"Removed {initial_rows - after_dropna} rows with null cod_centro_gestor")
            
            # Remove duplicates based on cod_centro_gestor
            before_dedup = len(centros_gestores)
            centros_gestores = centros_gestores.drop_duplicates(subset=['cod_centro_gestor']).reset_index(drop=True)
            after_dedup = len(centros_gestores)
            print(f"Removed {before_dedup - after_dedup} duplicate rows")
            
            # Show results
            print(f"\nCentros Gestores DataFrame:")
            print(f"Shape: {centros_gestores.shape} (Rows: {centros_gestores.shape[0]}, Columns: {centros_gestores.shape[1]})")
            print(f"Columns: {list(centros_gestores.columns)}")
            
            print(f"\nFirst 10 rows:")
            print(centros_gestores.head(10))
            
            print(f"\nData types:")
            print(centros_gestores.dtypes)
            
            print(f"\nSummary statistics:")
            print(f"  Total unique cod_centro_gestor: {centros_gestores['cod_centro_gestor'].nunique()}")
            print(f"  Total rows: {len(centros_gestores)}")
            
            # Check for non-null nombres
            if centros_gestores['nombre_centro_gestor'].notna().any():
                non_null_nombres = centros_gestores['nombre_centro_gestor'].notna().sum()
                print(f"  Rows with nombre_centro_gestor: {non_null_nombres} ({non_null_nombres/len(centros_gestores)*100:.1f}%)")
            
            # Show sample values
            print(f"\nSample cod_centro_gestor values:")
            sample_size = min(10, len(centros_gestores))
            for i in range(sample_size):
                cod = centros_gestores.iloc[i]['cod_centro_gestor']
                nombre = centros_gestores.iloc[i]['nombre_centro_gestor']
                print(f"  {i+1:2d}. {cod} -> {nombre}")
                
        else:
            print("Error: 'cod_centro_gestor' column not found in the consolidated dataframe")
            print(f"Available columns: {list(df_consolidado.columns)}")
            centros_gestores = None
        
        # Create programas dataframe with unique values
        print(f"\n" + "="*60)
        print(f"CREATING PROGRAMAS DATAFRAME:")
        print(f"="*60)
        
        # Check if the required columns exist
        if 'cod_programa' in df_consolidado.columns:
            print(f"Found 'cod_programa' column in dataframe")
            
            # Check if nombre_programa exists
            if 'nombre_programa' in df_consolidado.columns:
                print(f"Found 'nombre_programa' column in dataframe")
                programas = df_consolidado[['cod_programa', 'nombre_programa']].copy()
            else:
                print("Warning: 'nombre_programa' column not found, setting to None")
                programas = df_consolidado[['cod_programa']].copy()
                programas['nombre_programa'] = None
            
            # Convert cod_programa to integer if not already
            if programas['cod_programa'].dtype != 'Int64':
                try:
                    programas['cod_programa'] = pd.to_numeric(programas['cod_programa'], errors='coerce').astype('Int64')
                    print("Converted cod_programa to integer in programas")
                except Exception as e:
                    print(f"Warning: Could not convert cod_programa to integer: {e}")
            
            # Remove rows where cod_programa is null
            initial_rows = len(programas)
            programas = programas.dropna(subset=['cod_programa'])
            after_dropna = len(programas)
            print(f"Removed {initial_rows - after_dropna} rows with null cod_programa")
            
            # Remove duplicates based on cod_programa
            before_dedup = len(programas)
            programas = programas.drop_duplicates(subset=['cod_programa']).reset_index(drop=True)
            after_dedup = len(programas)
            print(f"Removed {before_dedup - after_dedup} duplicate rows")
            
            # Show results
            print(f"\nProgramas DataFrame:")
            print(f"Shape: {programas.shape} (Rows: {programas.shape[0]}, Columns: {programas.shape[1]})")
            print(f"Columns: {list(programas.columns)}")
            
            print(f"\nFirst 10 rows:")
            print(programas.head(10))
            
            print(f"\nData types:")
            print(programas.dtypes)
            
            print(f"\nSummary statistics:")
            print(f"  Total unique cod_programa: {programas['cod_programa'].nunique()}")
            print(f"  Total rows: {len(programas)}")
            
            # Check for non-null nombres
            if programas['nombre_programa'].notna().any():
                non_null_nombres = programas['nombre_programa'].notna().sum()
                print(f"  Rows with nombre_programa: {non_null_nombres} ({non_null_nombres/len(programas)*100:.1f}%)")
            
            # Show sample values
            print(f"\nSample cod_programa values:")
            sample_size = min(10, len(programas))
            for i in range(sample_size):
                cod = programas.iloc[i]['cod_programa']
                nombre = programas.iloc[i]['nombre_programa']
                print(f"  {i+1:2d}. {cod} -> {nombre}")
                
        else:
            print("Error: 'cod_programa' column not found in the consolidated dataframe")
            print(f"Available columns: {list(df_consolidado.columns)}")
            programas = None
        
        # Create areas_funcionales dataframe with unique values
        print(f"\n" + "="*60)
        print(f"CREATING AREAS_FUNCIONALES DATAFRAME:")
        print(f"="*60)
        
        # Check if the required columns exist
        if 'cod_area_funcional' in df_consolidado.columns:
            print(f"Found 'cod_area_funcional' column in dataframe")
            
            # Check if nombre_area_funcional exists
            if 'nombre_area_funcional' in df_consolidado.columns:
                print(f"Found 'nombre_area_funcional' column in dataframe")
                areas_funcionales = df_consolidado[['cod_area_funcional', 'nombre_area_funcional']].copy()
            else:
                print("Warning: 'nombre_area_funcional' column not found, setting to None")
                areas_funcionales = df_consolidado[['cod_area_funcional']].copy()
                areas_funcionales['nombre_area_funcional'] = None
            
            # Convert cod_area_funcional to integer if not already
            if areas_funcionales['cod_area_funcional'].dtype != 'Int64':
                try:
                    areas_funcionales['cod_area_funcional'] = pd.to_numeric(areas_funcionales['cod_area_funcional'], errors='coerce').astype('Int64')
                    print("Converted cod_area_funcional to integer in areas_funcionales")
                except Exception as e:
                    print(f"Warning: Could not convert cod_area_funcional to integer: {e}")
            
            # Remove rows where cod_area_funcional is null
            initial_rows = len(areas_funcionales)
            areas_funcionales = areas_funcionales.dropna(subset=['cod_area_funcional'])
            after_dropna = len(areas_funcionales)
            print(f"Removed {initial_rows - after_dropna} rows with null cod_area_funcional")
            
            # Remove duplicates based on cod_area_funcional
            before_dedup = len(areas_funcionales)
            areas_funcionales = areas_funcionales.drop_duplicates(subset=['cod_area_funcional']).reset_index(drop=True)
            after_dedup = len(areas_funcionales)
            print(f"Removed {before_dedup - after_dedup} duplicate rows")
            
            # Show results
            print(f"\nAreas Funcionales DataFrame:")
            print(f"Shape: {areas_funcionales.shape} (Rows: {areas_funcionales.shape[0]}, Columns: {areas_funcionales.shape[1]})")
            print(f"Columns: {list(areas_funcionales.columns)}")
            
            print(f"\nFirst 10 rows:")
            print(areas_funcionales.head(10))
            
            print(f"\nData types:")
            print(areas_funcionales.dtypes)
            
            print(f"\nSummary statistics:")
            print(f"  Total unique cod_area_funcional: {areas_funcionales['cod_area_funcional'].nunique()}")
            print(f"  Total rows: {len(areas_funcionales)}")
            
            # Check for non-null nombres
            if areas_funcionales['nombre_area_funcional'].notna().any():
                non_null_nombres = areas_funcionales['nombre_area_funcional'].notna().sum()
                print(f"  Rows with nombre_area_funcional: {non_null_nombres} ({non_null_nombres/len(areas_funcionales)*100:.1f}%)")
            
            # Show sample values
            print(f"\nSample cod_area_funcional values:")
            sample_size = min(10, len(areas_funcionales))
            for i in range(sample_size):
                cod = areas_funcionales.iloc[i]['cod_area_funcional']
                nombre = areas_funcionales.iloc[i]['nombre_area_funcional']
                print(f"  {i+1:2d}. {cod} -> {nombre}")
                
        else:
            print("Error: 'cod_area_funcional' column not found in the consolidated dataframe")
            print(f"Available columns: {list(df_consolidado.columns)}")
            areas_funcionales = None
        
        # Create retos dataframe with unique values
        print(f"\n" + "="*60)
        print(f"CREATING RETOS DATAFRAME:")
        print(f"="*60)
        
        # Check if the required columns exist
        if 'cod_reto' in df_consolidado.columns:
            print(f"Found 'cod_reto' column in dataframe")
            
            # Check if nombre_reto exists
            if 'nombre_reto' in df_consolidado.columns:
                print(f"Found 'nombre_reto' column in dataframe")
                retos = df_consolidado[['cod_reto', 'nombre_reto']].copy()
            else:
                print("Warning: 'nombre_reto' column not found, setting to None")
                retos = df_consolidado[['cod_reto']].copy()
                retos['nombre_reto'] = None
            
            # Convert cod_reto to integer if not already
            if retos['cod_reto'].dtype != 'Int64':
                try:
                    retos['cod_reto'] = pd.to_numeric(retos['cod_reto'], errors='coerce').astype('Int64')
                    print("Converted cod_reto to integer in retos")
                except Exception as e:
                    print(f"Warning: Could not convert cod_reto to integer: {e}")
            
            # Remove rows where cod_reto is null
            initial_rows = len(retos)
            retos = retos.dropna(subset=['cod_reto'])
            after_dropna = len(retos)
            print(f"Removed {initial_rows - after_dropna} rows with null cod_reto")
            
            # Remove duplicates based on cod_reto
            before_dedup = len(retos)
            retos = retos.drop_duplicates(subset=['cod_reto']).reset_index(drop=True)
            after_dedup = len(retos)
            print(f"Removed {before_dedup - after_dedup} duplicate rows")
            
            # Show results
            print(f"\nRetos DataFrame:")
            print(f"Shape: {retos.shape} (Rows: {retos.shape[0]}, Columns: {retos.shape[1]})")
            print(f"Columns: {list(retos.columns)}")
            
            print(f"\nFirst 10 rows:")
            print(retos.head(10))
            
            print(f"\nData types:")
            print(retos.dtypes)
            
            print(f"\nSummary statistics:")
            print(f"  Total unique cod_reto: {retos['cod_reto'].nunique()}")
            print(f"  Total rows: {len(retos)}")
            
            # Check for non-null nombres
            if retos['nombre_reto'].notna().any():
                non_null_nombres = retos['nombre_reto'].notna().sum()
                print(f"  Rows with nombre_reto: {non_null_nombres} ({non_null_nombres/len(retos)*100:.1f}%)")
            
            # Show sample values
            print(f"\nSample cod_reto values:")
            sample_size = min(10, len(retos))
            for i in range(sample_size):
                cod = retos.iloc[i]['cod_reto']
                nombre = retos.iloc[i]['nombre_reto']
                print(f"  {i+1:2d}. {cod} -> {nombre}")
                
        else:
            print("Error: 'cod_reto' column not found in the consolidated dataframe")
            print(f"Available columns: {list(df_consolidado.columns)}")
            retos = None
        
        # Create propositos dataframe with unique values
        print(f"\n" + "="*60)
        print(f"CREATING PROPOSITOS DATAFRAME:")
        print(f"="*60)
        
        # Check if the required columns exist
        if 'cod_proposito' in df_consolidado.columns:
            print(f"Found 'cod_proposito' column in dataframe")
            
            # Check if nombre_proposito exists
            if 'nombre_proposito' in df_consolidado.columns:
                print(f"Found 'nombre_proposito' column in dataframe")
                propositos = df_consolidado[['cod_proposito', 'nombre_proposito']].copy()
            else:
                print("Warning: 'nombre_proposito' column not found, setting to None")
                propositos = df_consolidado[['cod_proposito']].copy()
                propositos['nombre_proposito'] = None
            
            # Convert cod_proposito to integer if not already
            if propositos['cod_proposito'].dtype != 'Int64':
                try:
                    propositos['cod_proposito'] = pd.to_numeric(propositos['cod_proposito'], errors='coerce').astype('Int64')
                    print("Converted cod_proposito to integer in propositos")
                except Exception as e:
                    print(f"Warning: Could not convert cod_proposito to integer: {e}")
            
            # Remove rows where cod_proposito is null
            initial_rows = len(propositos)
            propositos = propositos.dropna(subset=['cod_proposito'])
            after_dropna = len(propositos)
            print(f"Removed {initial_rows - after_dropna} rows with null cod_proposito")
            
            # Remove duplicates based on cod_proposito
            before_dedup = len(propositos)
            propositos = propositos.drop_duplicates(subset=['cod_proposito']).reset_index(drop=True)
            after_dedup = len(propositos)
            print(f"Removed {before_dedup - after_dedup} duplicate rows")
            
            # Show results
            print(f"\nPropositos DataFrame:")
            print(f"Shape: {propositos.shape} (Rows: {propositos.shape[0]}, Columns: {propositos.shape[1]})")
            print(f"Columns: {list(propositos.columns)}")
            
            print(f"\nFirst 10 rows:")
            print(propositos.head(10))
            
            print(f"\nData types:")
            print(propositos.dtypes)
            
            print(f"\nSummary statistics:")
            print(f"  Total unique cod_proposito: {propositos['cod_proposito'].nunique()}")
            print(f"  Total rows: {len(propositos)}")
            
            # Check for non-null nombres
            if propositos['nombre_proposito'].notna().any():
                non_null_nombres = propositos['nombre_proposito'].notna().sum()
                print(f"  Rows with nombre_proposito: {non_null_nombres} ({non_null_nombres/len(propositos)*100:.1f}%)")
            
            # Show sample values
            print(f"\nSample cod_proposito values:")
            sample_size = min(10, len(propositos))
            for i in range(sample_size):
                cod = propositos.iloc[i]['cod_proposito']
                nombre = propositos.iloc[i]['nombre_proposito']
                print(f"  {i+1:2d}. {cod} -> {nombre}")
                
        else:
            print("Error: 'cod_proposito' column not found in the consolidated dataframe")
            print(f"Available columns: {list(df.columns)}")
            propositos = None
        
        # Create movimientos_presupuestales dataframe
        print(f"\n" + "="*60)
        print(f"CREATING MOVIMIENTOS_PRESUPUESTALES DATAFRAME:")
        print(f"="*60)
        
        # Check if the required columns exist
        required_cols = ['bpin', 'ppto_inicial', 'adiciones', 'reducciones', 'ppto_modificado']
        missing_cols = [col for col in required_cols if col not in df_consolidado.columns]
        
        if not missing_cols:
            print(f"Found all required columns for movimientos_presupuestales")
            
            # Start with a copy of the required columns
            movimientos_presupuestales = df_consolidado[['bpin', 'ppto_inicial', 'adiciones', 'reducciones', 'ppto_modificado', 'anio', 'dataframe_origen']].copy()
            
            # Function to clean monetary values
            def clean_monetary_value(value):
                """Clean monetary values by removing currency symbols and thousands separators, keep as float"""
                if pd.isna(value):
                    return 0.00
                
                # Convert to string first
                str_value = str(value).strip()
                
                # Handle special cases
                if str_value == '-' or str_value == '' or str_value.lower() == 'nan':
                    return 0.00
                
                # Remove currency symbols and spaces
                cleaned = str_value.replace('$', '').replace(' ', '').strip()
                
                # Handle the case where cleaned string is just "-" after cleaning
                if cleaned == '-' or cleaned == '':
                    return 0.00
                
                try:
                    # Handle different decimal formats
                    # Case 1: European format with dots as thousands separators (155.521.600)
                    if '.' in cleaned and ',' not in cleaned:
                        # Check if it's likely thousands separators (multiple dots or number after last dot > 2 digits)
                        parts = cleaned.split('.')
                        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) > 2):
                            # Treat as thousands separators, remove all dots
                            cleaned = cleaned.replace('.', '')
                        # If single dot with 1-2 digits after, treat as decimal separator
                        # Keep as is for now
                    
                    # Case 2: Mixed format with commas and dots ($224,436,000.00)
                    elif ',' in cleaned and '.' in cleaned:
                        # Assume comma is thousands separator, dot is decimal
                        cleaned = cleaned.replace(',', '')
                    
                    # Case 3: Only commas (could be thousands or decimal)
                    elif ',' in cleaned and '.' not in cleaned:
                        # Check position of comma
                        comma_pos = cleaned.rfind(',')
                        if len(cleaned) - comma_pos - 1 <= 2:
                            # Last comma has 1-2 digits after, likely decimal
                            cleaned = cleaned.replace(',', '.')
                        else:
                            # Remove commas (thousands separators)
                            cleaned = cleaned.replace(',', '')
                    
                    # Case 4: European format - if we have only dots, remove them (thousands separators)
                    if '.' in cleaned and ',' not in cleaned:
                        # For values like "155.521.600", remove all dots
                        dot_parts = cleaned.split('.')
                        if len(dot_parts) > 2:  # Multiple dots = thousands separators
                            cleaned = cleaned.replace('.', '')
                        elif len(dot_parts) == 2 and len(dot_parts[1]) > 2:  # Single dot with >2 digits after
                            cleaned = cleaned.replace('.', '')
                    
                    # Convert to float
                    result = float(cleaned)
                    return result
                    
                except (ValueError, TypeError) as e:
                    print(f"    Error cleaning '{str_value}': {e} - Setting to 0.00")
                    return 0.00
            
            # Clean monetary columns
            monetary_cols = ['ppto_inicial', 'adiciones', 'reducciones', 'ppto_modificado']
            for col in monetary_cols:
                print(f"Cleaning monetary values in column '{col}'...")
                movimientos_presupuestales[col] = movimientos_presupuestales[col].apply(clean_monetary_value)
                # Ensure exactly 2 decimal places
                movimientos_presupuestales[col] = movimientos_presupuestales[col].round(2)
                print(f"  Cleaned {col} and rounded to 2 decimal places")
            
            # Convert bpin to integer
            print("Converting bpin to integer...")
            try:
                movimientos_presupuestales['bpin'] = pd.to_numeric(movimientos_presupuestales['bpin'], errors='coerce').astype('Int64')
                print("  Converted bpin to integer")
            except Exception as e:
                print(f"  Warning: Could not convert bpin to integer: {e}")
            
            # Create periodo_corte from anio and dataframe_origen
            print("Creating periodo_corte from anio and dataframe_origen...")
            def extract_periodo_corte(row):
                """Extract period from year and dataframe_origen"""
                anio = row['anio']
                dataframe_origen = str(row['dataframe_origen']).lower()
                
                # Default to year if we can't extract month
                if pd.isna(anio):
                    return None
                
                # Try to extract month from dataframe_origen
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
                
                # Look for month in dataframe_origen
                month = '12'  # Default to December if no month found
                for month_name, month_num in month_mapping.items():
                    if month_name in dataframe_origen:
                        month = month_num
                        break
                
                # Return as YYYY-MM format
                return f"{int(anio)}-{month}"
            
            movimientos_presupuestales['periodo_corte'] = movimientos_presupuestales.apply(extract_periodo_corte, axis=1)
            print("  Created periodo_corte")
            
            # Drop auxiliary columns
            movimientos_presupuestales = movimientos_presupuestales.drop(columns=['anio', 'dataframe_origen'])
            
            # Remove rows where bpin is null
            initial_rows = len(movimientos_presupuestales)
            movimientos_presupuestales = movimientos_presupuestales.dropna(subset=['bpin'])
            after_dropna = len(movimientos_presupuestales)
            print(f"Removed {initial_rows - after_dropna} rows with null bpin")
            
            # Reset index
            movimientos_presupuestales = movimientos_presupuestales.reset_index(drop=True)
            
            # Show results
            print(f"\nMovimientos Presupuestales DataFrame:")
            print(f"Shape: {movimientos_presupuestales.shape} (Rows: {movimientos_presupuestales.shape[0]}, Columns: {movimientos_presupuestales.shape[1]})")
            print(f"Columns: {list(movimientos_presupuestales.columns)}")
            
            print(f"\nFirst 10 rows:")
            print(movimientos_presupuestales.head(10))
            
            print(f"\nData types:")
            print(movimientos_presupuestales.dtypes)
            
            print(f"\nSummary statistics:")
            print(f"  Total rows: {len(movimientos_presupuestales)}")
            print(f"  Unique BPIN count: {movimientos_presupuestales['bpin'].nunique()}")
            print(f"  Unique periods: {movimientos_presupuestales['periodo_corte'].nunique()}")
            print(f"  Period range: {movimientos_presupuestales['periodo_corte'].min()} to {movimientos_presupuestales['periodo_corte'].max()}")
            
            # Show monetary statistics
            for col in monetary_cols:
                non_null_count = movimientos_presupuestales[col].notna().sum()
                print(f"  {col}: {non_null_count}/{len(movimientos_presupuestales)} non-null ({non_null_count/len(movimientos_presupuestales)*100:.1f}%)")
                if non_null_count > 0:
                    print(f"    Min: {movimientos_presupuestales[col].min():.2f}")
                    print(f"    Max: {movimientos_presupuestales[col].max():.2f}")
                    print(f"    Mean: {movimientos_presupuestales[col].mean():.2f}")
            
            # Show sample values with exact format
            print(f"\nSample movimientos_presupuestales values:")
            sample_size = min(10, len(movimientos_presupuestales))
            for i in range(sample_size):
                row = movimientos_presupuestales.iloc[i]
                bpin = row['bpin']
                periodo = row['periodo_corte']
                inicial = row['ppto_inicial']
                adiciones = row['adiciones']
                reducciones = row['reducciones']
                modificado = row['ppto_modificado']
                print(f"  {i+1:2d}. BPIN: {bpin} | Period: {periodo} | Inicial: {inicial:.2f} | Adiciones: {adiciones:.2f} | Reducciones: {reducciones:.2f} | Modificado: {modificado:.2f}")
                
            # Create ejecucion_presupuestal dataframe
            print(f"\n" + "="*60)
            print(f"CREATING EJECUCION_PRESUPUESTAL DATAFRAME:")
            print(f"="*60)
            
            # Check if the required columns exist
            required_cols_ejecucion = ['bpin', 'ejecucion', 'pagos', 'saldos_cdp', 'total_acumul_obligac', 'total_acumulado_cdp', 'total_acumulado_rpc']
            missing_cols_ejecucion = [col for col in required_cols_ejecucion if col not in df_consolidado.columns]
            
            if not missing_cols_ejecucion:
                print(f"Found all required columns for ejecucion_presupuestal")
                
                # Start with a copy of the required columns
                ejecucion_presupuestal = df_consolidado[['bpin', 'ejecucion', 'pagos', 'saldos_cdp', 'total_acumul_obligac', 'total_acumulado_cdp', 'total_acumulado_rpc', 'anio', 'dataframe_origen']].copy()
                
                # Clean monetary columns using the same function
                monetary_cols_ejecucion = ['ejecucion', 'pagos', 'saldos_cdp', 'total_acumul_obligac', 'total_acumulado_cdp', 'total_acumulado_rpc']
                for col in monetary_cols_ejecucion:
                    print(f"Cleaning monetary values in column '{col}'...")
                    ejecucion_presupuestal[col] = ejecucion_presupuestal[col].apply(clean_monetary_value)
                    # Ensure exactly 2 decimal places
                    ejecucion_presupuestal[col] = ejecucion_presupuestal[col].round(2)
                    print(f"  Cleaned {col} and rounded to 2 decimal places")
                
                # Convert bpin to integer
                print("Converting bpin to integer...")
                try:
                    ejecucion_presupuestal['bpin'] = pd.to_numeric(ejecucion_presupuestal['bpin'], errors='coerce').astype('Int64')
                    print("  Converted bpin to integer")
                except Exception as e:
                    print(f"  Warning: Could not convert bpin to integer: {e}")
                
                # Create periodo_corte from anio and dataframe_origen (reuse the same function)
                print("Creating periodo_corte from anio and dataframe_origen...")
                ejecucion_presupuestal['periodo_corte'] = ejecucion_presupuestal.apply(extract_periodo_corte, axis=1)
                print("  Created periodo_corte")
                
                # Drop auxiliary columns
                ejecucion_presupuestal = ejecucion_presupuestal.drop(columns=['anio', 'dataframe_origen'])
                
                # Remove rows where bpin is null
                initial_rows_ejecucion = len(ejecucion_presupuestal)
                ejecucion_presupuestal = ejecucion_presupuestal.dropna(subset=['bpin'])
                after_dropna_ejecucion = len(ejecucion_presupuestal)
                print(f"Removed {initial_rows_ejecucion - after_dropna_ejecucion} rows with null bpin")
                
                # Reset index
                ejecucion_presupuestal = ejecucion_presupuestal.reset_index(drop=True)
                
                # Show results
                print(f"\nEjecucion Presupuestal DataFrame:")
                print(f"Shape: {ejecucion_presupuestal.shape} (Rows: {ejecucion_presupuestal.shape[0]}, Columns: {ejecucion_presupuestal.shape[1]})")
                print(f"Columns: {list(ejecucion_presupuestal.columns)}")
                
                print(f"\nFirst 10 rows:")
                print(ejecucion_presupuestal.head(10))
                
                print(f"\nData types:")
                print(ejecucion_presupuestal.dtypes)
                
                print(f"\nSummary statistics:")
                print(f"  Total rows: {len(ejecucion_presupuestal)}")
                print(f"  Unique BPIN count: {ejecucion_presupuestal['bpin'].nunique()}")
                print(f"  Unique periods: {ejecucion_presupuestal['periodo_corte'].nunique()}")
                print(f"  Period range: {ejecucion_presupuestal['periodo_corte'].min()} to {ejecucion_presupuestal['periodo_corte'].max()}")
                
                # Show monetary statistics
                for col in monetary_cols_ejecucion:
                    non_null_count = ejecucion_presupuestal[col].notna().sum()
                    print(f"  {col}: {non_null_count}/{len(ejecucion_presupuestal)} non-null ({non_null_count/len(ejecucion_presupuestal)*100:.1f}%)")
                    if non_null_count > 0:
                        print(f"    Min: {ejecucion_presupuestal[col].min():.2f}")
                        print(f"    Max: {ejecucion_presupuestal[col].max():.2f}")
                        print(f"    Mean: {ejecucion_presupuestal[col].mean():.2f}")
                
                # Show sample values with exact format
                print(f"\nSample ejecucion_presupuestal values:")
                sample_size = min(10, len(ejecucion_presupuestal))
                for i in range(sample_size):
                    row = ejecucion_presupuestal.iloc[i]
                    bpin = row['bpin']
                    periodo = row['periodo_corte']
                    ejecucion_val = row['ejecucion']
                    pagos_val = row['pagos']
                    saldos_val = row['saldos_cdp']
                    obligac_val = row['total_acumul_obligac']
                    cdp_val = row['total_acumulado_cdp']
                    rpc_val = row['total_acumulado_rpc']
                    print(f"  {i+1:2d}. BPIN: {bpin} | Period: {periodo}")
                    print(f"      Ejecución: {ejecucion_val:.2f} | Pagos: {pagos_val:.2f} | Saldos CDP: {saldos_val:.2f}")
                    print(f"      Acum Obligac: {obligac_val:.2f} | Acum CDP: {cdp_val:.2f} | Acum RPC: {rpc_val:.2f}")
                    print()
                
            else:
                print(f"Error: Missing required columns for ejecucion_presupuestal: {missing_cols_ejecucion}")
                print(f"Available columns: {list(df_consolidado.columns)}")
                ejecucion_presupuestal = None
                
        else:
            print(f"Error: Missing required columns for movimientos_presupuestales: {missing_cols}")
            print(f"Available columns: {list(df_consolidado.columns)}")
            movimientos_presupuestales = None
            ejecucion_presupuestal = None
        
        # Save all dataframes to JSON files
        print(f"\n" + "="*60)
        print(f"SAVING DATAFRAMES TO JSON FILES:")
        print(f"="*60)
        
        # Define output directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "app_outputs", "ejecucion_presupuestal_outputs")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        print(f"Output directory: {output_dir}")
        
        # List of dataframes to save
        dataframes_to_save = [
            ("df_consolidado", df_consolidado),
            ("centros_gestores", centros_gestores),
            ("programas", programas),
            ("areas_funcionales", areas_funcionales),
            ("retos", retos),
            ("propositos", propositos),
            ("movimientos_presupuestales", movimientos_presupuestales),
            ("ejecucion_presupuestal", ejecucion_presupuestal)
        ]
        
        saved_files = []
        failed_files = []
        
        for df_name, dataframe in dataframes_to_save:
            if dataframe is not None:
                try:
                    # Convert Int64 columns to regular int for JSON compatibility
                    df_copy = dataframe.copy()
                    
                    # Handle nullable integer columns
                    for col in df_copy.columns:
                        if df_copy[col].dtype == 'Int64':
                            # Convert Int64 to float first (to handle NaN), then to object for JSON
                            df_copy[col] = df_copy[col].astype('float64').where(df_copy[col].notna(), None)
                            # Convert non-null values back to int
                            df_copy[col] = df_copy[col].apply(lambda x: int(x) if pd.notna(x) else None)
                    
                    # Save to JSON with proper formatting
                    json_filename = f"{df_name}.json"
                    json_filepath = os.path.join(output_dir, json_filename)
                    
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
                print(f"⚠ Skipped {df_name}: DataFrame is None")
                failed_files.append(df_name)
        
        # Summary
        print(f"\n" + "="*60)
        print(f"SAVE SUMMARY:")
        print(f"="*60)
        print(f"Successfully saved: {len(saved_files)} files")
        for filename in saved_files:
            print(f"  ✓ {filename}")
        
        if failed_files:
            print(f"\nFailed to save: {len(failed_files)} files")
            for df_name in failed_files:
                print(f"  ✗ {df_name}")
        
        print(f"\nOutput directory: {output_dir}")
        print(f"Total files in directory: {len(os.listdir(output_dir))}")
        
        # Show file details
        print(f"\nFile details:")
        for filename in os.listdir(output_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(output_dir, filename)
                file_size = os.path.getsize(filepath) / 1024  # Size in KB
                print(f"  {filename}: {file_size:.1f} KB")
        
        return df_consolidado, centros_gestores, programas, areas_funcionales, retos, propositos, movimientos_presupuestales, ejecucion_presupuestal
        
    except Exception as e:
        print(f"Error in transformation: {e}")
        return None, None, None, None, None, None, None, None


if __name__ == "__main__":
    df_consolidado, centros_gestores, programas, areas_funcionales, retos, propositos, movimientos_presupuestales, ejecucion_presupuestal = main()