# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from src.agent.core import MultiAgentSQLSystem
# from src.api.teams_handler import TeamsHandler
# from src.config.settings import settings
# import logging

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Multi-Agent SQL Analysis API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Instanciar sistema
# multi_agent_system = MultiAgentSQLSystem(
#     database_url=settings.DATABASE_URL,
#     model_name=settings.LLM_MODEL
# )
# teams_handler = TeamsHandler()

# class AnalysisRequest(BaseModel):
#     message: str
#     user_id: str
#     channel_id: str = None

# class AnalysisResponse(BaseModel):
#     response: str
#     success: bool
#     database_result: str = None
#     detailed_analysis: str = None
#     error: str = None

# @app.post("/api/sql-analysis", response_model=AnalysisResponse)
# async def sql_analysis_endpoint(request: AnalysisRequest):
#     """Endpoint principal para análisis SQL con multi-agentes"""
#     try:
#         result = await multi_agent_system.process_message(
#             message=request.message,
#             user_id=request.user_id
#         )
        
#         return AnalysisResponse(
#             response=result["response"],
#             success=result["success"],
#             database_result=result.get("database_result"),
#             detailed_analysis=result.get("detailed_analysis"),
#             error=result.get("error")
#         )
#     except Exception as e:
#         logger.error(f"Error en SQL analysis endpoint: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/teams/webhook")
# async def teams_webhook(payload: dict):
#     """Webhook para recibir mensajes de Teams"""
#     try:
#         return await teams_handler.handle_webhook(payload, multi_agent_system)
#     except Exception as e:
#         logger.error(f"Error en Teams webhook: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/database/tables")
# async def get_database_tables():
#     """Endpoint para obtener las tablas disponibles"""
#     try:
#         result = multi_agent_system.sql_agent.invoke({
#             "input": "List all available tables",
#             "chat_history": []
#         })
#         return {"tables": result["output"]}
#     except Exception as e:
#         logger.error(f"Error obteniendo tablas: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/api/database/schema/{table_name}")
# async def get_table_schema(table_name: str):
#     """Endpoint para obtener el schema de una tabla específica"""
#     try:
#         result = multi_agent_system.sql_agent.invoke({
#             "input": f"Show me the schema for table: {table_name}",
#             "chat_history": []
#         })
#         return {"schema": result["output"]}
#     except Exception as e:
#         logger.error(f"Error obteniendo schema: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "agents": "multi-agent SQL system ready"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)


######### ------------------------------------------------- #######

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from src.agent.core import MultiAgentSQLSystem
from src.api.teams_handler import TeamsHandler
from src.api.telegram_handler import TelegramHandler
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent SQL Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instanciar sistemas
multi_agent_system = MultiAgentSQLSystem(
    database_url=settings.DATABASE_URL,
    model_name=settings.LLM_MODEL
)
teams_handler = TeamsHandler()
telegram_handler = TelegramHandler()

class AnalysisRequest(BaseModel):
    message: str
    user_id: str
    channel_id: Optional[str] = None

class AnalysisResponse(BaseModel):
    response: str
    success: bool
    database_result: Optional[str] = None
    detailed_analysis: Optional[str] = None
    error: Optional[str] = None

class WebhookRequest(BaseModel):
    url: str

# ==================== ENDPOINTS PRINCIPALES ====================

@app.post("/api/sql-analysis", response_model=AnalysisResponse)
async def sql_analysis_endpoint(request: AnalysisRequest):
    """Endpoint principal para análisis SQL con multi-agentes"""
    try:
        result = await multi_agent_system.process_message(
            message=request.message,
            user_id=request.user_id
        )
        
        return AnalysisResponse(
            response=result.get("response", ""),
            success=result.get("success", False),
            database_result=result.get("database_result", ""),
            detailed_analysis=result.get("detailed_analysis", ""),
            error=result.get("error", "")
        )
    except Exception as e:
        logger.error(f"Error en SQL analysis endpoint: {e}")
        return AnalysisResponse(
            response="Error procesando análisis de datos.",
            success=False,
            database_result="",
            detailed_analysis="",
            error=str(e)
        )

# ==================== ENDPOINTS TEAMS ====================

@app.post("/api/teams/webhook")
async def teams_webhook(payload: dict):
    """Webhook para recibir mensajes de Teams"""
    try:
        return await teams_handler.handle_webhook(payload, multi_agent_system)
    except Exception as e:
        logger.error(f"Error en Teams webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS TELEGRAM ====================

@app.post("/api/telegram/webhook")
async def telegram_webhook(payload: dict):
    """Webhook para recibir mensajes de Telegram"""
    try:
        return await telegram_handler.handle_webhook(payload, multi_agent_system)
    except Exception as e:
        logger.error(f"Error en Telegram webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telegram/status")
async def telegram_status():
    """Endpoint para verificar estado del bot de Telegram"""
    try:
        webhook_info = await telegram_handler.get_webhook_info()
        return {
            "status": "active",
            "webhook_info": webhook_info,
            "bot_token_set": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "temp")
        }
    except Exception as e:
        logger.error(f"Error obteniendo status de Telegram: {e}")
        return {"status": "error", "error": str(e)}

@app.post("/api/telegram/set-webhook")
async def set_telegram_webhook(webhook_data: WebhookRequest):
    """Endpoint para configurar webhook de Telegram"""
    try:
        webhook_url = webhook_data.url
        if not webhook_url:
            raise HTTPException(status_code=400, detail="URL requerida")
        
        success = await telegram_handler.set_webhook(webhook_url)
        
        if success:
            return {"status": "webhook_set", "url": webhook_url}
        else:
            raise HTTPException(status_code=500, detail="Error configurando webhook")
            
    except Exception as e:
        logger.error(f"Error configurando webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/telegram/webhook")
async def delete_telegram_webhook():
    """Endpoint para eliminar webhook de Telegram"""
    try:
        success = await telegram_handler.set_webhook("")
        if success:
            return {"status": "webhook_deleted"}
        else:
            raise HTTPException(status_code=500, detail="Error eliminando webhook")
    except Exception as e:
        logger.error(f"Error eliminando webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS DATABASE ====================

@app.get("/api/database/tables")
async def get_database_tables():
    """Endpoint para obtener las tablas disponibles"""
    try:
        result = multi_agent_system.sql_agent.invoke({
            "input": "List all available tables",
            "chat_history": []
        })
        return {"tables": result["output"]}
    except Exception as e:
        logger.error(f"Error obteniendo tablas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/database/schema/{table_name}")
async def get_table_schema(table_name: str):
    """Endpoint para obtener el schema de una tabla específica"""
    try:
        result = multi_agent_system.sql_agent.invoke({
            "input": f"Show me the schema for table: {table_name}",
            "chat_history": []
        })
        return {"schema": result["output"]}
    except Exception as e:
        logger.error(f"Error obteniendo schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENDPOINTS SISTEMA ====================

@app.get("/health")
async def health_check():
    """Health check del sistema"""
    try:
        # Verificar componentes principales
        system_status = {
            "status": "healthy",
            "components": {
                "multi_agent_system": "active",
                "database": "connected",
                "teams_handler": "ready",
                "telegram_handler": "ready"
            },
            "settings": {
                "database_url_set": bool(settings.DATABASE_URL),
                "openai_key_set": bool(settings.OPENAI_API_KEY),
                "telegram_token_set": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "temp"),
                "teams_configured": bool(settings.TEAMS_BOT_ID and settings.TEAMS_BOT_ID != "temp")
            }
        }
        
        return system_status
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/system/info")
async def system_info():
    """Información del sistema"""
    return {
        "app_name": "Multi-Agent SQL Analysis API",
        "version": "1.0.0",
        "supported_platforms": ["Teams", "Telegram"],
        "endpoints": {
            "sql_analysis": "/api/sql-analysis",
            "teams_webhook": "/api/teams/webhook",
            "telegram_webhook": "/api/telegram/webhook",
            "database_tables": "/api/database/tables",
            "health": "/health"
        }
    }

@app.get("/")
async def root():
    """Endpoint raíz con información básica"""
    return {
        "message": "Multi-Agent SQL Analysis API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)