from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session
import pandas as pd
import io
import os
import unicodedata
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

from . import models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class DirectoryRequest(BaseModel):
    directory_path: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def clean_numeric(value):
    if isinstance(value, str):
        value = value.replace('$', '').replace('.', '').replace(',', '.').replace('-', '0')
    try:
        return round(float(value), 2)
    except (ValueError, TypeError):
        return 0.0

def normalize_column_names(columns):
    normalized_cols = []
    for col in columns:
        col = col.lower()
        col = col.replace(' ', '_')
        col = col.strip('_')
        col = unicodedata.normalize('NFD', col).encode('ascii', 'ignore').decode('utf-8')
        col = col.replace('ñ', 'n')
        normalized_cols.append(col)
    return normalized_cols

def get_end_of_month_date(df_origin, year):
    if pd.isna(df_origin) or pd.isna(year):
        return None

    parts = df_origin.split('_')
    if len(parts) > 1:
        month_str = parts[1]
        month_map = {
            'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
            'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
            'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
        }
        month = month_map.get(month_str.upper())

        if month is not None:
            try:
                first_day_of_month = datetime(int(year), month, 1)
                last_day_of_month = first_day_of_month + relativedelta(months=1) - relativedelta(days=1)
                return last_day_of_month.strftime('%Y-%m-%d')
            except ValueError:
                return None
    return None

def standardize_dataframes(dfs, standard_columns):
    standardized_dfs = []
    
    # Comprehensive mapping from various source column names to standard names
    column_mapping = {
        'centro_gestor': 'centro_gestor',
        'nombre_centro_gestor': 'nombre_centro_gestor',
        'bp': 'bp',
        'nombre_del_proyecto': 'nombre_proyecto',
        'nombre_proyecto': 'nombre_proyecto',
        'nompre_bp': 'nombre_proyecto',
        'nombre_bp': 'nombre_proyecto',
        'programa': 'programa_presupuestal',
        'programa_presupuestal': 'programa_presupuestal',
        'nombre_de_la_actividad': 'nombre_actividad',
        'nombre_actividad': 'nombre_actividad',
        'bpin': 'bpin',
        'sector': 'sector',
        'producto': 'producto',
        'producto_1': 'producto',
        'validador_cuipo': 'validador_cuipo',
        'fondo_1': 'fondo',
        'fondo': 'fondo',
        'nombre_de_fondo': 'nombre_fondo',
        'nombre_fondo': 'nombre_fondo',
        'clasificacion_del_fondo': 'clasificacion_fondo',
        'clasificacion_del_fondo_1': 'clasificacion_fondo',
        'clasificacion_fondo': 'clasificacion_fondo',
        'pospre_1': 'pospre',
        'pospre': 'pospre',
        'pospre_1.1': 'nombre_pospre',
        'nombre_pospre': 'nombre_pospre',
        'dimension': 'dimension',
        'nombre_de_dimension': 'nombre_dimension',
        'nombre_dimension': 'nombre_dimension',
        'linea_estrategica': 'linea_estrategica',
        'nombre_de_linea_estrategica': 'nombre_linea_estrategica',
        'programa.1': 'programa_1',
        'nombre_de_programa': 'nombre_programa',
        'nombre_programa': 'nombre_programa',
        'area_funcional': 'area_funcional',
        'nombre_del_area_funcional': 'nombre_area_funcional',
        'nombre_area_funcional': 'nombre_area_funcional',
        'origen': 'origen',
        'comuna': 'comuna',
        'vigencia': 'vigencia',
        'tipo_de_gasto': 'tipo_gasto',
        'tipo_gasto': 'tipo_gasto',
        'ppto_inicial': 'ppto_inicial',
        'reducciones': 'reducciones',
        'adiciones': 'adiciones',
        'contracreditos': 'contracreditos',
        'creditos': 'creditos',
        'aplazamiento': 'aplazamiento',
        'desaplazamiento': 'desaplazamiento',
        'ppto._modificado': 'ppto_modificado',
        'ppto_modificado': 'ppto_modificado',
        'total_acumulado_cdp': 'total_acumulado_cdp',
        'total_acumulado_rpc': 'total_acumulado_rpc',
        'total_acumul_obligac': 'total_acumul_obligac',
        'pagos': 'pagos',
        'ejecucion': 'ejecucion',
        'saldos_cdp': 'saldos_cdp',
        'ppto._disponible': 'ppto_disponible',
        'ppto_disponible': 'ppto_disponible',
        'proposito': 'proposito',
        'nombre_proposito': 'nombre_proposito',
        'reto': 'reto',
        'nombre_reto': 'nombre_reto',
        'codigo_producto_mga': 'codigo_producto_mga',
        'nombre_producto_mga': 'nombre_producto_mga',
        'organismo': 'organismo',
        'producto_mga': 'producto_mga',
        'producto_cuipo': 'producto_cuipo'
    }

    for df_name, df in dfs.items():
        # 1. Make a copy to avoid SettingWithCopyWarning
        df = df.copy()
        
        # 2. Normalize column names
        df.columns = normalize_column_names(df.columns)
        
        # Debug: Print column names to see what we have
        print(f"DataFrame {df_name} columns after normalization: {list(df.columns)}")
        
        # 3. Rename columns using the comprehensive map
        df.rename(columns=column_mapping, inplace=True)

        # 4. Handle potential duplicate columns after renaming
        df = df.loc[:,~df.columns.duplicated()]
        
        # Debug: Check if comuna is present after mapping
        print(f"DataFrame {df_name} has 'comuna' column: {'comuna' in df.columns}")
        if 'comuna' in df.columns:
            print(f"Comuna sample values: {df['comuna'].head().tolist()}")

        # 5. Add year and origin
        year = df_name.split('_')[-1]
        if year.isdigit():
            df['anio'] = int(year)
        df['dataframe_origen'] = df_name

        # 6. Create a new DataFrame with only the standard columns
        new_df = pd.DataFrame()
        string_fields = [
            'bpin', 'area_funcional', 'centro_gestor', 'dimension', 
            'linea_estrategica', 'programa_presupuestal', 'bp', 'sector',
            'producto', 'validador_cuipo', 'fondo', 'pospre', 'origen',
            'comuna', 'vigencia', 'tipo_gasto', 'organismo'
        ]
        
        for col in standard_columns:
            if col in df.columns:
                # Convert data types appropriately
                if col in string_fields:
                    # Convert numeric fields that should be strings
                    new_df[col] = df[col].astype(str).replace('nan', None)
                else:
                    new_df[col] = df[col]
            else:
                new_df[col] = None

        standardized_dfs.append(new_df)
        
    return standardized_dfs

@app.post("/upload_and_process_data/")
async def upload_and_process_data(db: Session = Depends(get_db)):
    directory_path = "downloaded_data"
    
    if not os.path.exists(directory_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    files = os.listdir(directory_path)
    spreadsheet_files = [f for f in files if f.endswith('.csv') or f.endswith('.xlsx')]

    if not spreadsheet_files:
        raise HTTPException(status_code=404, detail="No spreadsheet files found in the directory")

    dfs = {}
    for file_name in spreadsheet_files:
        file_path = os.path.join(directory_path, file_name)
        try:
            if file_name.endswith('.csv'):
                df = pd.read_csv(file_path, sep=';', on_bad_lines='skip', low_memory=False)
            else:
                df = pd.read_excel(file_path)
            
            df_name = os.path.splitext(file_name)[0]
            dfs[df_name] = df
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading file {file_name}: {e}")

    # Define the standard schema based on the database model
    model_columns = [c.name for c in models.ProjectExecution.__table__.columns if c.name != 'id']
    
    # Standardize all dataframes
    standardized_dfs = standardize_dataframes(dfs, model_columns)

    if not standardized_dfs:
        raise HTTPException(status_code=500, detail="No dataframes to process")

    # Concatenate DataFrames
    try:
        df_consolidado = pd.concat(standardized_dfs, ignore_index=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during DataFrame concatenation: {e}")

    numeric_cols = [
        "pagos", "ppto_disponible", "ppto_inicial", "ppto_modificado", 
        "reducciones", "saldos_cdp", "total_acumul_obligac", 
        "total_acumulado_cdp", "total_acumulado_rpc", "adiciones",
        "aplazamiento", "contracreditos", "creditos", "desaplazamiento", "ejecucion"
    ]

    for col in numeric_cols:
        if col in df_consolidado.columns:
            df_consolidado[col] = df_consolidado[col].apply(clean_numeric)

    if 'anio' in df_consolidado.columns and 'dataframe_origen' in df_consolidado.columns:
        df_consolidado['periodo'] = df_consolidado.apply(
            lambda row: get_end_of_month_date(row['dataframe_origen'], row['anio']),
            axis=1
        )

    # Drop rows with high percentage of nulls
    null_percentage_per_row = df_consolidado.isnull().sum(axis=1) / df_consolidado.shape[1]
    rows_to_drop_mask = null_percentage_per_row > 0.8
    df_consolidado = df_consolidado[~rows_to_drop_mask].copy()

    # Drop unnecessary columns that might have slipped through
    df_consolidado = df_consolidado.loc[:,~df_consolidado.columns.duplicated()]
    columns_to_drop = ['unnamed:_41', 'vigencia'] 
    df_consolidado.drop(columns=columns_to_drop, inplace=True, errors='ignore')


    # Convert to dictionary and filter for model fields
    data_to_insert = df_consolidado.to_dict(orient='records')
    
    model_columns_set = {c.name for c in models.ProjectExecution.__table__.columns}
    
    for record in data_to_insert:
        filtered_record = {}
        
        for key, value in record.items():
            if key in model_columns_set and pd.notna(value):
                # Convert specific fields to strings if they're numeric
                string_fields = [
                    'bpin', 'area_funcional', 'centro_gestor', 'dimension', 
                    'linea_estrategica', 'programa_presupuestal', 'bp', 'sector',
                    'producto', 'validador_cuipo', 'fondo', 'pospre', 'origen',
                    'comuna', 'vigencia', 'tipo_gasto', 'organismo'
                ]
                if key in string_fields:
                    if pd.notna(value):
                        filtered_record[key] = str(value).replace('.0', '')  # Remove .0 from floats
                    else:
                        filtered_record[key] = None
                else:
                    filtered_record[key] = value
        
        if 'periodo' in filtered_record and filtered_record['periodo']:
            try:
                filtered_record['periodo'] = datetime.strptime(filtered_record['periodo'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                continue # Skip if date is invalid

        # Ensure all required fields for the model are present, even if null
        for col in model_columns:
            if col not in filtered_record:
                filtered_record[col] = None

        try:
            execution_data = schemas.ProjectExecutionCreate(**filtered_record)
            db_execution = models.ProjectExecution(**execution_data.dict())
            db.add(db_execution)
        except Exception as e:
            print(f"Error processing record: {e}")
            continue  # Skip problematic records
    
    db.commit()

    return {"message": "La data se ha cargado exitosamente."}


@app.post("/upload_and_process_data_from/")
async def upload_and_process_data_from(
    directory_path: str = Form(..., 
        title="Ruta del Directorio",
        description="Selecciona la carpeta que contiene los archivos CSV/Excel",
        example="C:\\mi_carpeta\\datos"
    ), 
    db: Session = Depends(get_db)
):
    """
    Upload and process data from a specified directory path.
    
    Args:
        directory_path: The absolute path to the directory containing the CSV/Excel files
    """
    if not os.path.exists(directory_path):
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")

    files = os.listdir(directory_path)
    spreadsheet_files = [f for f in files if f.endswith('.csv') or f.endswith('.xlsx')]

    if not spreadsheet_files:
        raise HTTPException(status_code=404, detail=f"No spreadsheet files found in the directory: {directory_path}")

    dfs = {}
    for file_name in spreadsheet_files:
        file_path = os.path.join(directory_path, file_name)
        try:
            if file_name.endswith('.csv'):
                df = pd.read_csv(file_path, sep=';', on_bad_lines='skip', low_memory=False)
            else:
                df = pd.read_excel(file_path)
            
            df_name = os.path.splitext(file_name)[0]
            dfs[df_name] = df
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading file {file_name}: {e}")

    # Define the standard schema based on the database model
    model_columns = [c.name for c in models.ProjectExecution.__table__.columns if c.name != 'id']
    
    # Standardize all dataframes
    standardized_dfs = standardize_dataframes(dfs, model_columns)

    if not standardized_dfs:
        raise HTTPException(status_code=500, detail="No dataframes to process")

    # Concatenate DataFrames
    try:
        df_consolidado = pd.concat(standardized_dfs, ignore_index=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during DataFrame concatenation: {e}")

    numeric_cols = [
        "pagos", "ppto_disponible", "ppto_inicial", "ppto_modificado", 
        "reducciones", "saldos_cdp", "total_acumul_obligac", 
        "total_acumulado_cdp", "total_acumulado_rpc", "adiciones",
        "aplazamiento", "contracreditos", "creditos", "desaplazamiento", "ejecucion"
    ]

    for col in numeric_cols:
        if col in df_consolidado.columns:
            df_consolidado[col] = df_consolidado[col].apply(clean_numeric)

    if 'anio' in df_consolidado.columns and 'dataframe_origen' in df_consolidado.columns:
        df_consolidado['periodo'] = df_consolidado.apply(
            lambda row: get_end_of_month_date(row['dataframe_origen'], row['anio']),
            axis=1
        )

    # Drop rows with high percentage of nulls
    null_percentage_per_row = df_consolidado.isnull().sum(axis=1) / df_consolidado.shape[1]
    rows_to_drop_mask = null_percentage_per_row > 0.8
    df_consolidado = df_consolidado[~rows_to_drop_mask].copy()

    # Drop unnecessary columns that might have slipped through
    df_consolidado = df_consolidado.loc[:,~df_consolidado.columns.duplicated()]
    columns_to_drop = ['unnamed:_41', 'vigencia'] 
    df_consolidado.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Convert to dictionary and filter for model fields
    data_to_insert = df_consolidado.to_dict(orient='records')
    
    model_columns_set = {c.name for c in models.ProjectExecution.__table__.columns}
    
    processed_records = 0
    skipped_records = 0
    
    for record in data_to_insert:
        filtered_record = {}
        
        for key, value in record.items():
            if key in model_columns_set and pd.notna(value):
                # Convert specific fields to strings if they're numeric
                string_fields = [
                    'bpin', 'area_funcional', 'centro_gestor', 'dimension', 
                    'linea_estrategica', 'programa_presupuestal', 'bp', 'sector',
                    'producto', 'validador_cuipo', 'fondo', 'pospre', 'origen',
                    'comuna', 'vigencia', 'tipo_gasto', 'organismo'
                ]
                if key in string_fields:
                    if pd.notna(value):
                        filtered_record[key] = str(value).replace('.0', '')  # Remove .0 from floats
                    else:
                        filtered_record[key] = None
                else:
                    filtered_record[key] = value
        
        if 'periodo' in filtered_record and filtered_record['periodo']:
            try:
                filtered_record['periodo'] = datetime.strptime(filtered_record['periodo'], '%Y-%m-%d').date()
            except (ValueError, TypeError):
                skipped_records += 1
                continue # Skip if date is invalid

        # Ensure all required fields for the model are present, even if null
        for col in model_columns:
            if col not in filtered_record:
                filtered_record[col] = None

        try:
            execution_data = schemas.ProjectExecutionCreate(**filtered_record)
            db_execution = models.ProjectExecution(**execution_data.dict())
            db.add(db_execution)
            processed_records += 1
        except Exception as e:
            print(f"Error processing record: {e}")
            skipped_records += 1
            continue  # Skip problematic records
    
    db.commit()

    return {
        "message": f"Data cargada exitosamente desde: {directory_path}",
        "directory_processed": directory_path,
        "files_processed": len(spreadsheet_files),
        "records_processed": processed_records,
        "records_skipped": skipped_records,
        "files_found": spreadsheet_files
    }


@app.delete("/clear_database/")
async def clear_database(db: Session = Depends(get_db)):
    """
    Delete all records from the project_execution table.
    Use with caution - this will permanently delete all data!
    """
    try:
        # Count records before deletion
        record_count = db.query(models.ProjectExecution).count()
        
        # Delete all records
        db.query(models.ProjectExecution).delete()
        db.commit()
        
        return {
            "message": f"Base de datos borrada con éxito. {record_count} registros fueron eliminados.",
            "Registros Eliminados": record_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing database: {e}")


@app.get("/database_info/")
async def get_database_info(db: Session = Depends(get_db)):
    """
    Get information about the current state of the database.
    """
    try:
        record_count = db.query(models.ProjectExecution).count()
        
        # Get some sample data if records exist
        sample_data = None
        if record_count > 0:
            sample_records = db.query(models.ProjectExecution).limit(3).all()
            sample_data = [
                {
                    "id": record.id,
                    "bpin": record.bpin,
                    "nombre_proyecto": record.nombre_proyecto,
                    "comuna": record.comuna,
                    "anio": record.anio,
                    "periodo": record.periodo
                }
                for record in sample_records
            ]
        
        return {
            "total_records": record_count,
            "sample_data": sample_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database info: {e}")


@app.get("/")
def read_root():
    return {"message": "Si lees esto, tu API está funcionando correctamente. Puedes acceder a la documentación en /docs o /redoc."}
