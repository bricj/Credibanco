import requests
import pandas as pd
from fastapi import FastAPI

def get_summary_iris():
    """
    Retorna el dataset de Iris como una lista de diccionarios
    """
    url = "http://127.0.0.1:8080/iris"

    response = requests.get(url)

    if response.status_code == 200:

        data = response.json()

        df = pd.DataFrame(data)
        
        grouped_df = df.groupby('target').mean().reset_index()
        
    else:
        print("Error al obtener los datos:", response.status_code)
        
    return grouped_df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("data_api:app", host="0.0.0.0", port=8980, reload=True)