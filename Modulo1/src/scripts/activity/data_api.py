from fastapi import FastAPI
from sklearn.datasets import load_iris
import pandas as pd

app = FastAPI()

@app.get("/iris")
def get_iris():
    """
    Retorna el dataset de Iris como una lista de diccionarios
    """
    iris = load_iris(as_frame=True)
    df = iris.frame
    return df.to_dict(orient="records")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("data_api:app", host="0.0.0.0", port=8080, reload=True)

# uvicorn data_api:app --reload

