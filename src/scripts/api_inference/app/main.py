import os
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
import os

# Ruta donde están los modelos dentro del contenedor Docker
MODEL_DIR = "C:/Users/Sebastian/Documents/Projects/Credibanco/modulo1/src/scripts/api_inference/app/models/"

app = FastAPI()

class PredictionInput(BaseModel):
    Culmen_Length: float
    Culmen_Depth: float
    Flipper_Length: float
    Body_Mass: float

# Configuracion del logger
logging.basicConfig(
    filename='./logs/mi_app.log',
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def load_model(model_name: str):
    """Carga un modelo desde un archivo .pkl"""
    model_path = os.path.join(MODEL_DIR, model_name)
    if not os.path.exists(model_path):
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    
    return joblib.load(model_path)


@app.get("/models")
def list_models():
    """Lista los modelos disponibles en la carpeta /models"""
    models = [f[0:-4] for f in os.listdir(MODEL_DIR) if f.endswith(".pkl")]
    return {"available_models": models}

@app.get("/model-schema/{model_name}")
def get_model_schema(model_name: str) -> Dict[str, Any]:
    """Obtiene la estructura esperada de los datos de entrada para hacer una predicción"""
    try:
        model = load_model(f'{model_name}.pkl')
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar el modelo: {str(e)}")

    schema = {"model_name": model_name}

    # Intentar obtener nombres de columnas si existen
    if hasattr(model, "feature_names_in_"):
        input_features = list(model.feature_names_in_)
    else:
        input_features = ["feature_" + str(i) for i in range(model.n_features_in_)]

    schema["input_features"] = input_features

    # Generar un ejemplo de entrada
    schema["example_input"] = {
        "data": [[0.0 for _ in range(len(input_features))]]
    }

    return schema


@app.post("/predict/{model_name}")
def predict(model_name: str, input_data: PredictionInput):
    """Realiza una predicción con el modelo especificado"""
    try:
        model = load_model(f'{model_name}.pkl')
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al cargar el modelo: {str(e)}")

    # Convertir la entrada a DataFrame si el modelo requiere ese formato
    try:
        numerical = [
            input_data.Culmen_Length, 
            input_data.Culmen_Depth, 
            input_data.Flipper_Length, 
            input_data.Body_Mass
        ]
        numerical = np.array(numerical).reshape(1, -1)
        predictions = model.predict(numerical)

        logging.info(f'predicción realizada con {model_name} \n \
                    entradas: {input_data} \n \
                    salida: {predictions}')

        return {"predictions": predictions.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la predicción: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Ejeutar en consola: uvicorn main:app --reload