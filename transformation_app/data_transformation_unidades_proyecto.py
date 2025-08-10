# -*- coding: utf-8 -*-
"""
Data transformation module for project units (unidades de proyecto) with geospatial data processing.
Optimized for FastAPI compatibility, scalability, and map visualization.
"""

import os
import pandas as pd
import json
import numpy as np
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime


def normalize_column_names(columns):
    """Normalize column names by converting to lowercase and removing special characters."""
    return [col.lower().strip().replace(' ', '_').replace('.', '_').replace('(', '').replace(')', '') for col in columns]


def clean_monetary_value(value):
    """Clean monetary values by removing currency symbols and thousands separators."""
    if pd.isna(value) or value is None:
        return None
    
    # Convert to string first
    str_value = str(value).strip()
    
    # Handle special cases
    if str_value == '-' or str_value == '' or str_value.lower() == 'nan' or str_value.lower() == 'null':
        return None
    
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
        
        # Convert to float
        result = float(cleaned)
        return round(result, 2)  # Always return with 2 decimal places
        
    except (ValueError, TypeError) as e:
        print(f"    Error cleaning '{str_value}': {e} - Setting to 0.00")
        return 0.00


def parse_geojson_geometry(geom_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse GeoJSON geometry string and validate format.
    
    Args:
        geom_str: String containing GeoJSON geometry
        
    Returns:
        Dict containing parsed geometry or None if invalid
    """
    if pd.isna(geom_str) or not geom_str:
        return None
    
    try:
        geom_obj = json.loads(geom_str)
        
        # Validate required fields
        if 'type' not in geom_obj or 'coordinates' not in geom_obj:
            return None
        
        # Validate geometry type
        valid_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon']
        if geom_obj['type'] not in valid_types:
            return None
        
        return geom_obj
    
    except (json.JSONDecodeError, TypeError):
        return None


def extract_coordinates_info(geom_obj: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[Dict]]:
    """
    Extract coordinate information from geometry object.
    
    Args:
        geom_obj: Parsed GeoJSON geometry object
        
    Returns:
        Tuple of (longitude, latitude, coordinate_bounds) for the geometry centroid/representative point
    """
    if not geom_obj or 'coordinates' not in geom_obj:
        return None, None, None
    
    geom_type = geom_obj['type']
    coords = geom_obj['coordinates']
    
    try:
        if geom_type == 'Point':
            # For Point: coordinates are [lon, lat] or [lat, lon, elevation]
            lon, lat = coords[0], coords[1]
            bounds = {'min_lon': lon, 'max_lon': lon, 'min_lat': lat, 'max_lat': lat}
            return lon, lat, bounds
        
        elif geom_type == 'LineString':
            # For LineString: coordinates are [[lon1, lat1], [lon2, lat2], ...]
            if coords:
                lons = [coord[0] for coord in coords]
                lats = [coord[1] for coord in coords]
                
                # Calculate centroid
                center_lon = sum(lons) / len(lons)
                center_lat = sum(lats) / len(lats)
                
                # Calculate bounds
                bounds = {
                    'min_lon': min(lons),
                    'max_lon': max(lons),
                    'min_lat': min(lats),
                    'max_lat': max(lats)
                }
                
                return center_lon, center_lat, bounds
        
        elif geom_type == 'Polygon':
            # For Polygon: coordinates are [[[lon1, lat1], [lon2, lat2], ...]]
            if coords and coords[0]:
                exterior_ring = coords[0]
                lons = [coord[0] for coord in exterior_ring]
                lats = [coord[1] for coord in exterior_ring]
                
                # Calculate centroid
                center_lon = sum(lons) / len(lons)
                center_lat = sum(lats) / len(lats)
                
                # Calculate bounds
                bounds = {
                    'min_lon': min(lons),
                    'max_lon': max(lons),
                    'min_lat': min(lats),
                    'max_lat': max(lats)
                }
                
                return center_lon, center_lat, bounds
        
        # For other complex geometries, return None for now
        return None, None, None
    
    except (IndexError, TypeError, ValueError):
        return None, None, None


def create_feature_collection(dataframe: pd.DataFrame) -> Dict[str, Any]:
    """
    Create a GeoJSON FeatureCollection from a dataframe with geometry data.
    
    Args:
        dataframe: DataFrame containing geometry and properties
        
    Returns:
        Dict containing GeoJSON FeatureCollection
    """
    features = []
    
    for idx, row in dataframe.iterrows():
        try:
            # Parse geometry
            geom_obj = None
            if 'geom' in row and pd.notna(row['geom']):
                geom_obj = parse_geojson_geometry(row['geom'])
            
            if not geom_obj:
                continue
            
            # Create properties (exclude geom and coordinate columns)
            properties = {}
            exclude_cols = ['geom', 'lat', 'lon', 'longitude', 'latitude', 'key', 'origen_sheet', 'geometry_bounds', 'geometry_type']
            
            for col, value in row.items():
                if col not in exclude_cols:
                    # Handle NaN or null values based on data type
                    if pd.isna(value):
                        # Check if the column should contain numeric data
                        if col in ['bpin', 'ppto_base', 'pagos_realizados', 'avance_físico_obra', 'ejecucion_financiera_obra', 
                                  'longitud_proyectada', 'longitud_ejecutada', 'usuarios_beneficiarios']:
                            properties[col] = 0.00
                        else:
                            properties[col] = None
                    elif col == 'bpin':
                        # Special handling for BPIN to ensure it's always an integer
                        try:
                            properties[col] = int(float(value))
                        except (ValueError, TypeError):
                            properties[col] = 0.00
                    elif isinstance(value, (np.int64, np.int32, pd.Int64Dtype)):
                        properties[col] = int(value)
                    elif isinstance(value, (np.float64, np.float32)):
                        # Round float values to 2 decimal places for monetary/measurement values
                        # Keep 6 decimal places for coordinates
                        if col in ['longitude', 'latitude']:
                            properties[col] = round(float(value), 6)
                        else:
                            properties[col] = round(float(value), 2)
                    elif isinstance(value, float):
                        # Handle regular Python floats
                        if col in ['longitude', 'latitude']:
                            properties[col] = round(value, 6)
                        else:
                            properties[col] = round(value, 2)
                    else:
                        properties[col] = value
            
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": geom_obj,
                "properties": properties
            }
            
            features.append(feature)
            
        except Exception as e:
            print(f"Warning: Could not create feature for row {idx}: {e}")
            continue
    
    # Create FeatureCollection
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    
    return feature_collection


def unidades_proyecto_transformer(data_directory: str = "transformation_app/app_inputs/unidades_proyecto_input") -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Transform project units data for infrastructure equipment and road infrastructure.
    Creates two main tables with geospatial data optimized for FastAPI and map visualization.
    
    Args:
        data_directory (str): Path to the directory containing Excel files
        
    Returns:
        Tuple of (unidad_proyecto_infraestructura_equipamientos, unidad_proyecto_infraestructura_vial)
    """
    
    # Get the absolute path to the data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    directory_path = os.path.join(parent_dir, data_directory)
    
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    print(f"Loading data from: {directory_path}")
    
    # Define file paths
    equipamientos_path = os.path.join(directory_path, "obras_equipamientos.xlsx")
    lineales_path = os.path.join(directory_path, "obras_lineales.xlsx")
    
    # Check if files exist
    if not os.path.exists(equipamientos_path):
        raise FileNotFoundError(f"File not found: {equipamientos_path}")
    if not os.path.exists(lineales_path):
        raise FileNotFoundError(f"File not found: {lineales_path}")
    
    # Load Excel files
    print("Loading obras_equipamientos.xlsx...")
    df_equipamientos = pd.read_excel(equipamientos_path)
    print(f"Loaded {len(df_equipamientos)} rows from obras_equipamientos.xlsx")
    
    print("Loading obras_lineales.xlsx...")
    df_lineales = pd.read_excel(lineales_path)
    print(f"Loaded {len(df_lineales)} rows from obras_lineales.xlsx")
    
    # ================================
    # PROCESS EQUIPAMIENTOS DATA
    # ================================
    print("\n" + "="*60)
    print("PROCESSING EQUIPAMIENTOS DATA")
    print("="*60)
    
    # Create standardized equipamientos dataframe
    equipamientos_standard_columns = {
        'bpin': 'bpin',
        'identificador': 'identificador', 
        'fuente_financiacion': 'cod_fuente_financiamiento',
        'usuarios': 'usuarios_beneficiarios',
        'dataframe': 'dataframe',
        'nickname': 'nickname',
        'nickname_detalle': 'nickname_detalle',
        'comuna_corregimiento': 'comuna_corregimiento',
        'barrio_vereda': 'barrio_vereda',
        'direccion': 'direccion',
        'clase_obra': 'clase_obra',
        'subclase': 'subclase_obra',
        'tipo_intervencion': 'tipo_intervencion',
        'descripcion_intervencion': 'descripcion_intervencion',
        'centros_gravedad': 'es_centro_gravedad',
        'presupuesto_base': 'ppto_base',
        'avance_obra': 'avance_físico_obra',
        'geom': 'geom'
    }
    
    # Create equipamientos dataframe
    df_equipamientos_processed = df_equipamientos.copy()
    
    # Remove unnecessary columns
    columns_to_remove = ['key', 'origen_sheet', 'lat', 'lon']
    df_equipamientos_processed = df_equipamientos_processed.drop(columns=[col for col in columns_to_remove if col in df_equipamientos_processed.columns], errors='ignore')
    
    # Rename columns
    df_equipamientos_processed = df_equipamientos_processed.rename(columns=equipamientos_standard_columns)
    
    # Create the final equipamientos dataframe with required columns
    unidad_proyecto_infraestructura_equipamientos = pd.DataFrame()
    
    # Map columns to final schema
    final_equipamientos_columns = [
        'bpin', 'identificador', 'cod_fuente_financiamiento', 'usuarios_beneficiarios',
        'dataframe', 'nickname', 'nickname_detalle', 'comuna_corregimiento', 
        'barrio_vereda', 'direccion', 'clase_obra', 'subclase_obra', 
        'tipo_intervencion', 'descripcion_intervencion', 'estado_unidad_proyecto',
        'fecha_inicio_planeado', 'fecha_fin_planeado', 'fecha_inicio_real', 
        'fecha_fin_real', 'es_centro_gravedad', 'ppto_base', 'pagos_realizados',
        'avance_físico_obra', 'ejecucion_financiera_obra', 'geom'
    ]
    
    for col in final_equipamientos_columns:
        if col in df_equipamientos_processed.columns:
            unidad_proyecto_infraestructura_equipamientos[col] = df_equipamientos_processed[col]
        else:
            # Set default values for missing columns
            if col == 'estado_unidad_proyecto':
                unidad_proyecto_infraestructura_equipamientos[col] = 'En ejecución'
            elif col in ['fecha_inicio_planeado', 'fecha_fin_planeado', 'fecha_inicio_real', 'fecha_fin_real']:
                unidad_proyecto_infraestructura_equipamientos[col] = None
            elif col in ['pagos_realizados', 'ejecucion_financiera_obra']:
                unidad_proyecto_infraestructura_equipamientos[col] = 0.00
            else:
                unidad_proyecto_infraestructura_equipamientos[col] = None
    
    # Process data types and clean values
    print("Cleaning and processing equipamientos data...")
    
    # Fix columns that should be text but are mistakenly float64 due to all NaN values
    text_columns = ['nickname_detalle', 'direccion', 'descripcion_intervencion']
    for col in text_columns:
        if col in unidad_proyecto_infraestructura_equipamientos.columns:
            unidad_proyecto_infraestructura_equipamientos[col] = unidad_proyecto_infraestructura_equipamientos[col].apply(
                lambda x: None if pd.isna(x) else str(x)
            )
    
    # Convert BPIN to integer (ensure no decimals, handle large numbers)
    if 'bpin' in unidad_proyecto_infraestructura_equipamientos.columns:
        # Handle large BPIN numbers by using int64 directly
        def convert_bpin(value):
            if pd.isna(value):
                return None
            try:
                # Convert to float first to handle scientific notation, then to int
                return int(float(value))
            except (ValueError, OverflowError):
                return None
        
        unidad_proyecto_infraestructura_equipamientos['bpin'] = unidad_proyecto_infraestructura_equipamientos['bpin'].apply(convert_bpin)
        # Explicitly cast to object type to handle mixed int/None values for JSON serialization
        unidad_proyecto_infraestructura_equipamientos['bpin'] = unidad_proyecto_infraestructura_equipamientos['bpin'].astype('object')
    
    # Clean monetary values (round to 2 decimal places)
    monetary_cols_equipamientos = ['ppto_base', 'pagos_realizados', 'ejecucion_financiera_obra']
    for col in monetary_cols_equipamientos:
        if col in unidad_proyecto_infraestructura_equipamientos.columns:
            unidad_proyecto_infraestructura_equipamientos[col] = unidad_proyecto_infraestructura_equipamientos[col].apply(
                lambda x: clean_monetary_value(x) if pd.notna(x) else 0.00
            ).round(2)
    
    # Clean percentage values (avance_físico_obra) - round to 2 decimal places
    if 'avance_físico_obra' in unidad_proyecto_infraestructura_equipamientos.columns:
        unidad_proyecto_infraestructura_equipamientos['avance_físico_obra'] = pd.to_numeric(
            unidad_proyecto_infraestructura_equipamientos['avance_físico_obra'], errors='coerce'
        ).fillna(0.0).round(2)
    
    # Clean usuarios_beneficiarios as numeric
    if 'usuarios_beneficiarios' in unidad_proyecto_infraestructura_equipamientos.columns:
        unidad_proyecto_infraestructura_equipamientos['usuarios_beneficiarios'] = pd.to_numeric(
            unidad_proyecto_infraestructura_equipamientos['usuarios_beneficiarios'], errors='coerce'
        ).fillna(0.0).round(2)
    
    # Convert es_centro_gravedad to boolean
    if 'es_centro_gravedad' in unidad_proyecto_infraestructura_equipamientos.columns:
        unidad_proyecto_infraestructura_equipamientos['es_centro_gravedad'] = unidad_proyecto_infraestructura_equipamientos['es_centro_gravedad'].astype(bool)
    
    print(f"Processed equipamientos: {len(unidad_proyecto_infraestructura_equipamientos)} rows")
    
    # ================================
    # PROCESS LINEALES/VIAL DATA  
    # ================================
    print("\n" + "="*60)
    print("PROCESSING INFRAESTRUCTURA VIAL DATA")
    print("="*60)
    
    # Create standardized lineales dataframe
    lineales_standard_columns = {
        'bpin': 'bpin',
        'identificador': 'identificador',
        'fuente_financiacion': 'cod_fuente_financiamiento', 
        'usuarios': 'usuarios_beneficiarios',
        'dataframe': 'dataframe',
        'nickname': 'nickname',
        'nickname_detalle': 'nickname_detalle',
        'comuna_corregimiento': 'comuna_corregimiento',
        'barrio_vereda': 'barrio_vereda',
        'direccion': 'direccion',
        'clase_obra': 'clase_obra',
        'subclase': 'subclase_obra',
        'tipo_intervencion': 'tipo_intervencion',
        'descripcion_intervencion': 'descripcion_intervencion',
        'centros_gravedad': 'es_centro_gravedad',
        'unidad': 'unidad_medicion',
        'cantidad': 'longitud_proyectada',
        'presupuesto_base': 'ppto_base',
        'avance_obra': 'avance_físico_obra',
        'geom': 'geom'
    }
    
    # Create lineales dataframe
    df_lineales_processed = df_lineales.copy()
    
    # Remove unnecessary columns
    columns_to_remove = ['key', 'origen_sheet', 'lat', 'lon']
    df_lineales_processed = df_lineales_processed.drop(columns=[col for col in columns_to_remove if col in df_lineales_processed.columns], errors='ignore')
    
    # Rename columns
    df_lineales_processed = df_lineales_processed.rename(columns=lineales_standard_columns)
    
    # Create the final vial dataframe with required columns
    unidad_proyecto_infraestructura_vial = pd.DataFrame()
    
    # Map columns to final schema
    final_vial_columns = [
        'bpin', 'identificador', 'id_via', 'cod_fuente_financiamiento', 'usuarios_beneficiarios',
        'dataframe', 'nickname', 'nickname_detalle', 'comuna_corregimiento', 
        'barrio_vereda', 'direccion', 'clase_obra', 'subclase_obra', 
        'tipo_intervencion', 'descripcion_intervencion', 'estado_unidad_proyecto',
        'unidad_medicion', 'fecha_inicio_planeado', 'fecha_fin_planeado', 
        'fecha_inicio_real', 'fecha_fin_real', 'es_centro_gravedad',
        'longitud_proyectada', 'longitud_ejecutada', 'ppto_base', 'pagos_realizados',
        'avance_físico_obra', 'ejecucion_financiera_obra', 'geom'
    ]
    
    for col in final_vial_columns:
        if col in df_lineales_processed.columns:
            unidad_proyecto_infraestructura_vial[col] = df_lineales_processed[col]
        else:
            # Set default values for missing columns
            if col == 'estado_unidad_proyecto':
                unidad_proyecto_infraestructura_vial[col] = 'En ejecución'
            elif col == 'id_via':
                # Generate id_via from identificador or row index
                unidad_proyecto_infraestructura_vial[col] = df_lineales_processed.get('identificador', range(len(df_lineales_processed)))
            elif col in ['fecha_inicio_planeado', 'fecha_fin_planeado', 'fecha_inicio_real', 'fecha_fin_real']:
                unidad_proyecto_infraestructura_vial[col] = None
            elif col in ['longitud_ejecutada', 'pagos_realizados', 'ejecucion_financiera_obra']:
                unidad_proyecto_infraestructura_vial[col] = 0.00
            else:
                unidad_proyecto_infraestructura_vial[col] = None
    
    # Process data types and clean values
    print("Cleaning and processing vial data...")
    
    # Fix columns that should be text but are mistakenly float64 due to all NaN values
    text_columns = ['nickname_detalle', 'direccion', 'subclase_obra', 'descripcion_intervencion']
    for col in text_columns:
        if col in unidad_proyecto_infraestructura_vial.columns:
            unidad_proyecto_infraestructura_vial[col] = unidad_proyecto_infraestructura_vial[col].apply(
                lambda x: None if pd.isna(x) else str(x)
            )
    
    # Convert BPIN to integer (ensure no decimals, handle large numbers)
    if 'bpin' in unidad_proyecto_infraestructura_vial.columns:
        # Handle large BPIN numbers by using int64 directly
        def convert_bpin(value):
            if pd.isna(value):
                return None
            try:
                # Convert to float first to handle scientific notation, then to int
                return int(float(value))
            except (ValueError, OverflowError):
                return None
        
        unidad_proyecto_infraestructura_vial['bpin'] = unidad_proyecto_infraestructura_vial['bpin'].apply(convert_bpin)
        # Explicitly cast to object type to handle mixed int/None values for JSON serialization
        unidad_proyecto_infraestructura_vial['bpin'] = unidad_proyecto_infraestructura_vial['bpin'].astype('object')
    
    # Clean monetary values (round to 2 decimal places)
    monetary_cols_vial = ['ppto_base', 'pagos_realizados', 'ejecucion_financiera_obra']
    for col in monetary_cols_vial:
        if col in unidad_proyecto_infraestructura_vial.columns:
            unidad_proyecto_infraestructura_vial[col] = unidad_proyecto_infraestructura_vial[col].apply(
                lambda x: clean_monetary_value(x) if pd.notna(x) else 0.00
            ).round(2)
    
    # Clean length values (round to 2 decimal places)
    length_cols = ['longitud_proyectada', 'longitud_ejecutada']
    for col in length_cols:
        if col in unidad_proyecto_infraestructura_vial.columns:
            unidad_proyecto_infraestructura_vial[col] = pd.to_numeric(
                unidad_proyecto_infraestructura_vial[col], errors='coerce'
            ).fillna(0.0).round(2)
    
    # Clean percentage values (avance_físico_obra) - round to 2 decimal places
    if 'avance_físico_obra' in unidad_proyecto_infraestructura_vial.columns:
        unidad_proyecto_infraestructura_vial['avance_físico_obra'] = pd.to_numeric(
            unidad_proyecto_infraestructura_vial['avance_físico_obra'], errors='coerce'
        ).fillna(0.0).round(2)
    
    # Clean usuarios_beneficiarios as numeric
    if 'usuarios_beneficiarios' in unidad_proyecto_infraestructura_vial.columns:
        unidad_proyecto_infraestructura_vial['usuarios_beneficiarios'] = pd.to_numeric(
            unidad_proyecto_infraestructura_vial['usuarios_beneficiarios'], errors='coerce'
        ).fillna(0.0).round(2)
    
    # Convert es_centro_gravedad to boolean
    if 'es_centro_gravedad' in unidad_proyecto_infraestructura_vial.columns:
        unidad_proyecto_infraestructura_vial['es_centro_gravedad'] = unidad_proyecto_infraestructura_vial['es_centro_gravedad'].astype(bool)
    
    print(f"Processed vial data: {len(unidad_proyecto_infraestructura_vial)} rows")
    
    # ================================
    # GEOSPATIAL PROCESSING
    # ================================
    print("\n" + "="*60)
    print("PROCESSING GEOSPATIAL DATA")
    print("="*60)
    
    # Process geometries for both dataframes
    for df_name, df in [("equipamientos", unidad_proyecto_infraestructura_equipamientos), 
                        ("vial", unidad_proyecto_infraestructura_vial)]:
        
        print(f"\nProcessing geometries for {df_name}...")
        
        valid_geoms = 0
        invalid_geoms = 0
        
        # Extract coordinate information
        df['longitude'] = None
        df['latitude'] = None
        df['geometry_bounds'] = None
        df['geometry_type'] = None
        
        for idx, row in df.iterrows():
            geom_obj = parse_geojson_geometry(row.get('geom'))
            
            if geom_obj:
                valid_geoms += 1
                
                # Extract coordinates and bounds
                lon, lat, bounds = extract_coordinates_info(geom_obj)
                df.at[idx, 'longitude'] = round(lon, 6) if lon is not None else None  # 6 decimals for coordinates
                df.at[idx, 'latitude'] = round(lat, 6) if lat is not None else None   # 6 decimals for coordinates
                df.at[idx, 'geometry_bounds'] = json.dumps(bounds) if bounds else None
                df.at[idx, 'geometry_type'] = geom_obj['type']
            else:
                invalid_geoms += 1
        
        print(f"  Valid geometries: {valid_geoms}")
        print(f"  Invalid geometries: {invalid_geoms}")
        print(f"  Success rate: {valid_geoms/(valid_geoms+invalid_geoms)*100:.1f}%")
    
    # ================================
    # DATA SUMMARY
    # ================================
    print("\n" + "="*60)
    print("DATA TRANSFORMATION SUMMARY")
    print("="*60)
    
    print(f"\nUnidad Proyecto Infraestructura Equipamientos:")
    print(f"  Rows: {len(unidad_proyecto_infraestructura_equipamientos)}")
    print(f"  Columns: {len(unidad_proyecto_infraestructura_equipamientos.columns)}")
    print(f"  Valid geometries: {unidad_proyecto_infraestructura_equipamientos['geometry_type'].notna().sum()}")
    
    print(f"\nUnidad Proyecto Infraestructura Vial:")
    print(f"  Rows: {len(unidad_proyecto_infraestructura_vial)}")
    print(f"  Columns: {len(unidad_proyecto_infraestructura_vial.columns)}")
    print(f"  Valid geometries: {unidad_proyecto_infraestructura_vial['geometry_type'].notna().sum()}")
    
    return unidad_proyecto_infraestructura_equipamientos, unidad_proyecto_infraestructura_vial


def save_geospatial_data(df_equipamientos: pd.DataFrame, df_vial: pd.DataFrame, output_directory: str = "app_outputs/unidades_proyecto_outputs"):
    """
    Save the processed data in multiple formats optimized for different use cases.
    
    Args:
        df_equipamientos: Processed equipamientos dataframe
        df_vial: Processed vial dataframe  
        output_directory: Directory to save output files
    """
    
    # Create output directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, output_directory)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n" + "="*60)
    print("SAVING GEOSPATIAL DATA")
    print("="*60)
    print(f"Output directory: {output_dir}")
    
    saved_files = []
    failed_files = []
    
    # ================================
    # SAVE DATABASE-READY JSON FILES
    # ================================
    print("\nSaving database-ready JSON files...")
    
    dataframes_to_save = [
        ("unidad_proyecto_infraestructura_equipamientos", df_equipamientos),
        ("unidad_proyecto_infraestructura_vial", df_vial)
    ]
    
    for df_name, dataframe in dataframes_to_save:
        try:
            # Create a copy for processing
            df_copy = dataframe.copy()
            
            # Convert data types for JSON compatibility
            for col in df_copy.columns:
                if col == 'bpin':
                    # Special handling for BPIN to ensure it's always an integer
                    df_copy[col] = df_copy[col].apply(lambda x: int(x) if pd.notna(x) and x is not None else 0.00)
                elif df_copy[col].dtype == 'Int64':
                    # Convert Int64 to regular int, handling NaN values
                    df_copy[col] = df_copy[col].apply(lambda x: int(x) if pd.notna(x) else 0.00)
                elif df_copy[col].dtype in ['float64', 'float32']:
                    # Round float values to appropriate decimal places
                    if col in ['longitude', 'latitude']:
                        df_copy[col] = df_copy[col].apply(lambda x: round(x, 6) if pd.notna(x) else 0.00)
                    else:
                        df_copy[col] = df_copy[col].apply(lambda x: round(x, 2) if pd.notna(x) else 0.00)
                elif df_copy[col].dtype == 'object':
                    # Handle mixed types in object columns
                    def clean_object_value(x):
                        if pd.isna(x):
                            # Check if this column should contain numeric data
                            numeric_columns = ['bpin', 'ppto_base', 'pagos_realizados', 'avance_físico_obra', 'ejecucion_financiera_obra', 
                                              'longitud_proyectada', 'longitud_ejecutada', 'usuarios_beneficiarios']
                            if col in numeric_columns:
                                return 0.00
                            else:
                                return None
                        elif col == 'bpin':
                            # Force BPIN to be integer
                            try:
                                return int(float(x))
                            except (ValueError, TypeError):
                                return 0.00
                        elif isinstance(x, (int, np.int64, np.int32)):
                            return int(x)
                        elif isinstance(x, (float, np.float64, np.float32)):
                            if col in ['longitude', 'latitude']:
                                return round(float(x), 6)
                            else:
                                return round(float(x), 2)
                        else:
                            return x
                    df_copy[col] = df_copy[col].apply(clean_object_value)
            
            # Drop auxiliary coordinate columns for database storage
            columns_to_drop = ['longitude', 'latitude', 'geometry_bounds', 'geometry_type']
            db_df = df_copy.drop(columns=[col for col in columns_to_drop if col in df_copy.columns])
            
            # Save database-ready JSON
            json_filename = f"{df_name}.json"
            json_filepath = os.path.join(output_dir, json_filename)
            
            # Convert to JSON with orient='records' for API compatibility
            # Use custom serializer to ensure BPIN values are integers
            import json as json_module
            
            records = db_df.to_dict('records')
            # Force BPIN to be integer in each record
            for record in records:
                if 'bpin' in record and record['bpin'] is not None:
                    try:
                        record['bpin'] = int(float(record['bpin']))
                    except (ValueError, TypeError, OverflowError):
                        record['bpin'] = 0.00
                
                # Handle other numeric fields that should be 0.00 if null/NaN
                numeric_fields = ['ppto_base', 'pagos_realizados', 'avance_físico_obra', 'ejecucion_financiera_obra', 
                                 'longitud_proyectada', 'longitud_ejecutada', 'usuarios_beneficiarios']
                for field in numeric_fields:
                    if field in record and record[field] is None:
                        record[field] = 0.00
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json_module.dump(records, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(json_filepath) / 1024  # Size in KB
            print(f"✓ Saved {df_name}: {json_filename} ({len(dataframe)} rows, {file_size:.1f} KB)")
            saved_files.append(json_filename)
            
        except Exception as e:
            print(f"✗ Failed to save {df_name}: {e}")
            failed_files.append(df_name)
    
    # ================================
    # SAVE GEOJSON FILES FOR MAPPING
    # ================================
    print("\nSaving GeoJSON files for mapping...")
    
    geojson_files = [
        ("equipamientos_geojson", df_equipamientos, "equipamientos.geojson"),
        ("vial_geojson", df_vial, "infraestructura_vial.geojson")
    ]
    
    for geojson_name, dataframe, filename in geojson_files:
        try:
            # Create GeoJSON FeatureCollection
            feature_collection = create_feature_collection(dataframe)
            
            # Save GeoJSON file
            geojson_filepath = os.path.join(output_dir, filename)
            with open(geojson_filepath, 'w', encoding='utf-8') as f:
                json.dump(feature_collection, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(geojson_filepath) / 1024  # Size in KB
            feature_count = len(feature_collection['features'])
            print(f"✓ Saved {geojson_name}: {filename} ({feature_count} features, {file_size:.1f} KB)")
            saved_files.append(filename)
            
        except Exception as e:
            print(f"✗ Failed to save {geojson_name}: {e}")
            failed_files.append(geojson_name)
    
    # ================================
    # SAVE SUMMARY STATISTICS
    # ================================
    print("\nSaving summary statistics...")
    
    try:
        summary_stats = {
            "generated_at": datetime.now().isoformat(),
            "equipamientos": {
                "total_records": int(len(df_equipamientos)),
                "valid_geometries": int(df_equipamientos['geometry_type'].notna().sum()),
                "geometry_types": {k: int(v) for k, v in df_equipamientos['geometry_type'].value_counts().to_dict().items()},
                "total_budget": float(df_equipamientos['ppto_base'].sum()),
                "communes": int(df_equipamientos['comuna_corregimiento'].nunique())
            },
            "infraestructura_vial": {
                "total_records": int(len(df_vial)),
                "valid_geometries": int(df_vial['geometry_type'].notna().sum()),
                "geometry_types": {k: int(v) for k, v in df_vial['geometry_type'].value_counts().to_dict().items()},
                "total_budget": float(df_vial['ppto_base'].sum()),
                "total_length": float(df_vial['longitud_proyectada'].sum()),
                "communes": int(df_vial['comuna_corregimiento'].nunique())
            }
        }
        
        # Save summary
        summary_filepath = os.path.join(output_dir, "data_summary.json")
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_stats, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved data_summary.json")
        saved_files.append("data_summary.json")
        
    except Exception as e:
        print(f"✗ Failed to save summary statistics: {e}")
        failed_files.append("data_summary")
    
    # ================================
    # SAVE COORDINATE INDEX FOR OPTIMIZATION
    # ================================
    print("\nSaving spatial indexes...")
    
    try:
        # Create spatial index for fast geographic queries
        equipamientos_index = []
        vial_index = []
        
        # Extract coordinate info for equipamientos
        for idx, row in df_equipamientos.iterrows():
            if pd.notna(row.get('longitude')) and pd.notna(row.get('latitude')):
                equipamientos_index.append({
                    "id": int(idx),
                    "bpin": int(row.get('bpin')) if pd.notna(row.get('bpin')) and row.get('bpin') != 0.00 else 0.00,
                    "identificador": str(row.get('identificador')) if pd.notna(row.get('identificador')) else None,
                    "longitude": float(row['longitude']),
                    "latitude": float(row['latitude']),
                    "geometry_type": str(row.get('geometry_type')) if pd.notna(row.get('geometry_type')) else None,
                    "bounds": json.loads(row['geometry_bounds']) if row.get('geometry_bounds') else None
                })
        
        # Extract coordinate info for vial
        for idx, row in df_vial.iterrows():
            if pd.notna(row.get('longitude')) and pd.notna(row.get('latitude')):
                vial_index.append({
                    "id": int(idx),
                    "bpin": int(row.get('bpin')) if pd.notna(row.get('bpin')) and row.get('bpin') != 0.00 else 0.00,
                    "identificador": str(row.get('identificador')) if pd.notna(row.get('identificador')) else None,
                    "id_via": str(row.get('id_via')) if pd.notna(row.get('id_via')) else None,
                    "longitude": float(row['longitude']),
                    "latitude": float(row['latitude']),
                    "geometry_type": str(row.get('geometry_type')) if pd.notna(row.get('geometry_type')) else None,
                    "bounds": json.loads(row['geometry_bounds']) if row.get('geometry_bounds') else None
                })
        
        # Save spatial indexes
        spatial_index = {
            "equipamientos": equipamientos_index,
            "infraestructura_vial": vial_index
        }
        
        index_filepath = os.path.join(output_dir, "spatial_index.json")
        with open(index_filepath, 'w', encoding='utf-8') as f:
            json.dump(spatial_index, f, indent=2, ensure_ascii=False)
        
        file_size = os.path.getsize(index_filepath) / 1024  # Size in KB
        print(f"✓ Saved spatial_index.json ({len(equipamientos_index + vial_index)} indexed features, {file_size:.1f} KB)")
        saved_files.append("spatial_index.json")
        
    except Exception as e:
        print(f"✗ Failed to save spatial index: {e}")
        failed_files.append("spatial_index")
    
    # ================================
    # SAVE SUMMARY
    # ================================
    print(f"\n" + "="*60)
    print("SAVE SUMMARY")
    print("="*60)
    print(f"Successfully saved: {len(saved_files)} files")
    for filename in saved_files:
        print(f"  ✓ {filename}")
    
    if failed_files:
        print(f"\nFailed to save: {len(failed_files)} files")
        for filename in failed_files:
            print(f"  ✗ {filename}")
    
    print(f"\nOutput directory: {output_dir}")
    print(f"Total files in directory: {len(os.listdir(output_dir))}")
    
    # Show file details
    print(f"\nFile details:")
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        file_size = os.path.getsize(filepath) / 1024  # Size in KB
        print(f"  {filename}: {file_size:.1f} KB")


def main():
    """Main function for testing the transformer."""
    try:
        print("="*80)
        print("UNIDADES DE PROYECTO DATA TRANSFORMATION")
        print("="*80)
        
        # Transform the data
        df_equipamientos, df_vial = unidades_proyecto_transformer()
        
        if df_equipamientos is not None and df_vial is not None:
            print("\n" + "="*60)
            print("TRANSFORMATION COMPLETED SUCCESSFULLY")
            print("="*60)
            
            # Display sample data
            print(f"\nEquipamientos sample data:")
            print(df_equipamientos.head(3))
            print(f"\nEquipamientos columns: {list(df_equipamientos.columns)}")
            
            print(f"\nVial sample data:")
            print(df_vial.head(3))
            print(f"\nVial columns: {list(df_vial.columns)}")
            
            # Save the processed data
            save_geospatial_data(df_equipamientos, df_vial)
            
            return df_equipamientos, df_vial
        
        else:
            print("Error: Data transformation failed")
            return None, None
        
    except Exception as e:
        print(f"Error in transformation: {e}")
        return None, None


if __name__ == "__main__":
    df_equipamientos, df_vial = main()
