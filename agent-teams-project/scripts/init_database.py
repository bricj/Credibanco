import pandas as pd
import sqlite3
import os
import json

def load_multiple_files_to_db():
    """Carga múltiples archivos a una sola base de datos"""
    
    data_dir = "data"
    db_path = "data/company_data.db"
    
    if not os.path.exists(data_dir):
        print("❌ No existe carpeta data/")
        return
    
    # Conectar a base de datos
    conn = sqlite3.connect(db_path)
    
    # Buscar todos los archivos de datos
    files = os.listdir(data_dir)
    loaded_tables = []
    
    for file in files:
        if file.endswith('.db'):  # Saltar archivos de base de datos
            continue
            
        file_path = os.path.join(data_dir, file)
        table_name = os.path.splitext(file)[0]  # nombre sin extensión
        
        try:
            print(f"📊 Procesando: {file}")
            
            # Cargar según tipo de archivo
            if file.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            elif file.endswith('.json'):
                df = pd.read_json(file_path)
            else:
                print(f"⚠️  Tipo no soportado: {file}")
                continue
            
            # Cargar a base de datos
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            loaded_tables.append(table_name)
            
            print(f"✅ Tabla '{table_name}': {len(df)} filas, {len(df.columns)} columnas")
            
        except Exception as e:
            print(f"❌ Error con {file}: {e}")
    
    conn.close()
    
    if loaded_tables:
        print(f"\n🚀 Base de datos creada: {db_path}")
        print(f"📋 Tablas disponibles: {', '.join(loaded_tables)}")
    else:
        print("❌ No se cargaron datos")

if __name__ == "__main__":
    load_multiple_files_to_db()