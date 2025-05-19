#from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
from fastapi import FastAPI, HTTPException, Depends, Query, Response

# Importar agentes (implementados según instrucciones anteriores)
from agents.research_agent import create_research_agent
from agents.rag_agent import create_rag_agent
from agents.stock_agent import create_stock_agent

# Obtener claves API
openai_api_key = os.getenv("OPENAI_API_KEY")
serpapi_api_key = os.getenv("SERPAPI_API_KEY")

# Verificar que existan
if not openai_api_key or not serpapi_api_key:
    raise ValueError("Faltan variables de entorno necesarias: OPENAI_API_KEY o SERPAPI_API_KEY")

app = FastAPI(title="Financial AI Agents API")

# Modelos de datos
class ResearchQuery(BaseModel):
    query: str

class RAGQuery(BaseModel):
    query: str
    pdf_url: Optional[str] = None

class StockQuery(BaseModel):
    ticker: str
    query: str

# Endpoints

## Visualizacion en formato json
# @app.post("/agents/research")
# async def research_endpoint(request: ResearchQuery):
#     try:
#         agent = create_research_agent()
#         response = agent.run(request.query)
#         return {"result": response}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/research")
async def research_endpoint(request: ResearchQuery, format: Optional[str] = Query("json", enum=["json", "text", "markdown"])):
    try:
        agent = create_research_agent()
        response_text = agent.run(request.query)

        if format == "text":
            return Response(content=response_text, media_type="text/plain")
        elif format == "markdown":
            md = f"# Research Report\n\n**Query:** `{request.query}`\n\n---\n\n{response_text}"
            return Response(content=md, media_type="text/markdown")
        else:
            return {"result": response_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Seccion especial para generar reporte
class ResearchRequest(BaseModel):
    topic: str

@app.post("/generate-report")
def generate_report(request: ResearchRequest):
    agent = create_research_agent()
    prompt = f"Generate a financial intelligence report on: {request.topic}"
    result = agent.run(prompt)
    return {"report": result}
# Fin seccion

DEFAULT_PDF_URL = "https://www.apple.com/environment/pdf/Apple_Environmental_Progress_Report_2024.pdf"

@app.post("/agents/rag")
async def rag_endpoint(request: RAGQuery):
    try:
        pdf_url = request.pdf_url or DEFAULT_PDF_URL
        agent = create_rag_agent(pdf_url)
        response = agent.run(request.query)
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/stock")
async def stock_endpoint(request: StockQuery):
    try:
        agent = create_stock_agent()
        response = agent.run(f"Analyze {request.ticker}: {request.query}")
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Verificación de salud
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)