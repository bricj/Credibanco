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
    # Nuevos campos opcionales del OrchestratorSystem
    query_type: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None

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
        
        # Log adicional del tipo de consulta procesada
        query_type = result.get("query_type", "unknown")
        intent = result.get("intent", "unknown")
        confidence = result.get("confidence", 0.0)
        
        logger.info(f"Query processed - Type: {query_type}, Intent: {intent}, Confidence: {confidence:.2f}")
        
        return AnalysisResponse(
            response=result.get("response", ""),
            success=result.get("success", False),
            database_result=result.get("database_result", ""),
            detailed_analysis=result.get("detailed_analysis", ""),
            error=result.get("error", ""),
            query_type=query_type,
            intent=intent,
            confidence=confidence
        )
    except Exception as e:
        logger.error(f"Error en SQL analysis endpoint: {e}")
        return AnalysisResponse(
            response="Error procesando análisis de datos.",
            success=False,
            database_result="",
            detailed_analysis="",
            error=str(e),
            query_type="error"
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
        # Acceso corregido al sql_agent en la nueva arquitectura
        result = multi_agent_system.sql_agent.sql_agent.invoke({
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
        # Acceso corregido al sql_agent en la nueva arquitectura
        result = multi_agent_system.sql_agent.sql_agent.invoke({
            "input": f"Show me the schema for table: {table_name}",
            "chat_history": []
        })
        return {"schema": result["output"]}
    except Exception as e:
        logger.error(f"Error obteniendo schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))

############################ RAG ########################################################

@app.post("/api/rag/ingest")
async def ingest_rag_documents():
    """Ingestar todos los documentos para RAG"""
    try:
        result = multi_agent_system.rag_agent.ingest_all_documents()
        logger.info(f"RAG Ingesta completada: {result}")
        return result
    except Exception as e:
        logger.error(f"Error en ingesta RAG: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/rag/stats")
async def get_rag_stats():
    """Obtener estadísticas del sistema RAG"""
    try:
        stats = multi_agent_system.rag_agent.get_knowledge_stats()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo stats RAG: {e}")
        return {"error": str(e)}

@app.post("/api/rag/debug")
async def debug_rag_search(request: dict):
    """Debug de búsqueda RAG"""
    try:
        query = request.get("query", "")
        k = request.get("k", 5)
        
        if not query:
            raise HTTPException(status_code=400, detail="Query requerida")
        
        result = multi_agent_system.rag_agent.debug_search(query, k)
        return result
    except Exception as e:
        logger.error(f"Error en debug RAG: {e}")
        return {"error": str(e)}

@app.post("/api/rag/reset")
async def reset_rag_knowledge():
    """Resetear completamente la base de conocimiento RAG"""
    try:
        result = multi_agent_system.rag_agent.reset_knowledge_base()
        logger.info(f"RAG Reset completado: {result}")
        return result
    except Exception as e:
        logger.error(f"Error reseteando RAG: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/rag/validate")
async def validate_rag_system():
    """Validar que el sistema RAG funciona correctamente"""
    try:
        # Intentar asegurar vectorstore
        vectorstore_ready = multi_agent_system.rag_agent._ensure_vectorstore()
        
        if vectorstore_ready:
            # Hacer validación completa
            validation = multi_agent_system.rag_agent._validate_vectorstore()
            return {
                "status": "ready",
                "vectorstore_ready": True,
                "validation": validation
            }
        else:
            return {
                "status": "not_ready",
                "vectorstore_ready": False,
                "message": "Vectorstore no disponible. Ejecuta /api/rag/ingest primero."
            }
    except Exception as e:
        logger.error(f"Error validando RAG: {e}")
        return {"status": "error", "error": str(e)}


########################## ENDPOINTS INICIALIZACION #####################################

@app.post("/api/system/initialize")
async def initialize_complete_system():
    """Inicializar completamente el sistema multi-agente"""
    try:
        results = {
            "sql_initialization": {"status": "pending"},
            "rag_initialization": {"status": "pending"},
            "system_status": {"status": "pending"}
        }
        
        # 1. Verificar/inicializar SQL
        try:
            # Verificar conexión a base de datos
            sql_result = multi_agent_system.sql_agent.sql_agent.invoke({
                "input": "List all available tables",
                "chat_history": []
            })
            results["sql_initialization"] = {
                "status": "success",
                "message": "Base de datos SQL conectada",
                "tables_available": True
            }
        except Exception as e:
            results["sql_initialization"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 2. Inicializar RAG
        try:
            rag_stats = multi_agent_system.rag_agent.get_knowledge_stats()
            
            if rag_stats.get("vectorstore_info", {}).get("documents_in_vectorstore", 0) == 0:
                # Hacer ingesta automática
                ingest_result = multi_agent_system.rag_agent.ingest_all_documents()
                results["rag_initialization"] = {
                    "status": "success" if ingest_result.get("success") else "error",
                    "message": "Documentos procesados automáticamente",
                    "documents_processed": ingest_result.get("documents_processed", 0),
                    "chunks_created": ingest_result.get("chunks_created", 0)
                }
            else:
                results["rag_initialization"] = {
                    "status": "success",
                    "message": "RAG ya inicializado",
                    "documents_in_vectorstore": rag_stats["vectorstore_info"]["documents_in_vectorstore"]
                }
        except Exception as e:
            results["rag_initialization"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 3. Estado final del sistema
        sql_ready = results["sql_initialization"]["status"] == "success"
        rag_ready = results["rag_initialization"]["status"] == "success"
        
        results["system_status"] = {
            "status": "ready" if (sql_ready and rag_ready) else "partial",
            "sql_agent": "ready" if sql_ready else "error",
            "rag_agent": "ready" if rag_ready else "error",
            "hybrid_mode": "available" if (sql_ready and rag_ready) else "limited"
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error en inicialización completa: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/system/status")
async def get_system_status():
    """Estado completo del sistema"""
    try:
        # Verificar SQL
        sql_status = "unknown"
        try:
            multi_agent_system.sql_agent.sql_agent.invoke({
                "input": "SELECT 1",
                "chat_history": []
            })
            sql_status = "ready"
        except:
            sql_status = "error"
        
        # Verificar RAG
        rag_status = "unknown"
        rag_docs = 0
        try:
            rag_stats = multi_agent_system.rag_agent.get_knowledge_stats()
            rag_docs = rag_stats.get("vectorstore_info", {}).get("documents_in_vectorstore", 0)
            rag_status = "ready" if rag_docs > 0 else "empty"
        except:
            rag_status = "error"
        
        return {
            "system_ready": sql_status == "ready" and rag_status == "ready",
            "components": {
                "sql_agent": {
                    "status": sql_status,
                    "description": "Análisis de base de datos transaccionales"
                },
                "rag_agent": {
                    "status": rag_status,
                    "documents_loaded": rag_docs,
                    "description": "Consultas de documentos y conocimiento"
                },
                "router_agent": {
                    "status": "ready",
                    "description": "Clasificación inteligente de consultas"
                }
            },
            "capabilities": {
                "sql_queries": sql_status == "ready",
                "document_queries": rag_status == "ready",
                "hybrid_queries": sql_status == "ready" and rag_status == "ready"
            }
        }
        
    except Exception as e:
        return {"error": str(e)}

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
                "orchestrator": "ready",
                "sql_agent": "ready",
                "router_agent": "ready",
                "database": "connected",
                "teams_handler": "ready",
                "telegram_handler": "ready"
            },
            "settings": {
                "database_url_set": bool(settings.DATABASE_URL),
                # Corregido: usar GOOGLE_API_KEY en lugar de OPENAI_API_KEY
                "google_api_key_set": bool(getattr(settings, 'GOOGLE_API_KEY', None)),
                # Mantener retrocompatibilidad con OPENAI_API_KEY si existe
                "openai_key_set": bool(getattr(settings, 'OPENAI_API_KEY', None)),
                "telegram_token_set": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "temp"),
                "teams_configured": bool(settings.TEAMS_BOT_ID and settings.TEAMS_BOT_ID != "temp")
            },
            "architecture": {
                "version": "2.0",
                "orchestrator_enabled": True,
                "router_agent_enabled": True,
                "rag_agent_enabled": True,  # Será True cuando implementemos RAG
                "sql_agent_enabled": True
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
        "version": "2.0.0",
        "architecture": "Orchestrator-based Multi-Agent System",
        "agents": {
            "orchestrator": "Main coordinator agent",
            "router": "Query intent classification",
            "sql_agent": "Database analysis specialist",
            "rag_agent": "Knowledge base (coming soon)"
        },
        "supported_platforms": ["Teams", "Telegram"],
        "endpoints": {
            "sql_analysis": "/api/sql-analysis",
            "teams_webhook": "/api/teams/webhook",
            "telegram_webhook": "/api/telegram/webhook",
            "database_tables": "/api/database/tables",
            "health": "/health"
        }
    }

@app.get("/api/system/query-types")
async def query_types_info():
    """Información sobre los tipos de consulta soportados"""
    return {
        "supported_query_types": {
            "sql": {
                "description": "Análisis de datos transaccionales",
                "keywords": ["total", "suma", "cantidad", "transacciones", "periodo", "franquicia", "plataforma"],
                "examples": [
                    "¿Cuál es el total de transacciones por periodo?",
                    "Mostrar transacciones por franquicia",
                    "Análisis de datos por plataforma"
                ]
            },
            "rag": {
                "description": "Consultas de conocimiento y documentación",
                "keywords": ["explicar", "qué es", "cómo funciona", "documentación", "procedimiento"],
                "examples": [
                    "¿Qué es una franquicia de tarjeta?",
                    "Explica el proceso de transacciones",
                    "Documentación del sistema"
                ],
                "status": "coming_soon"
            },
            "hybrid": {
                "description": "Combinación de datos y conocimiento",
                "examples": [
                    "Comparar nuestros datos con estándares de la industria",
                    "Contexto de negocio para estos números"
                ],
                "status": "planned"
            }
        },
        "router": {
            "classification_method": "keyword_analysis",
            "confidence_threshold": 0.5,
            "fallback_to": "sql"
        }
    }

@app.get("/")
async def root():
    """Endpoint raíz con información básica"""
    return {
        "message": "Multi-Agent SQL Analysis API",
        "version": "2.0.0",
        "architecture": "Orchestrator-based System",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "system_info": "/api/system/info"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)