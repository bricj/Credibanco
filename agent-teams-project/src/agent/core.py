import logging
import os
from typing import Dict, Any, TypedDict
from enum import Enum

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Variables de entorno cargadas desde .env")
except ImportError:
    print("⚠️ python-dotenv no disponible, usando variables del sistema")
except Exception as e:
    print(f"⚠️ Error cargando .env: {e}")

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from .sql_agent import SQLAgentSystem
from .memory import ConversationMemoryManager

logger = logging.getLogger(__name__)

class QueryIntent(Enum):
    SQL = "sql"
    RAG = "rag"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"

class OrchestratorState(TypedDict):
    query: str
    user_id: str
    intent: str
    confidence: float
    sql_result: str
    rag_result: str
    final_response: str
    query_type: str

class RouterAgent:
    """Agente router que determina el tipo de consulta"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
    
    def classify_intent(self, query: str) -> Dict[str, Any]:
        """Clasificar la intención de la consulta"""
        
        # Keywords específicos para SQL
        sql_keywords = [
            "total", "suma", "cantidad", "transacciones", "periodo", "franquicia", 
            "plataforma", "valor", "análisis", "reporte", "datos", "consulta",
            "cuánto", "cuántos", "mostrar", "listar", "comparar", "grupo",
            "mes", "año", "fecha", "establecimiento", "entidad"
        ]
        
        # Keywords específicos para RAG (cuando se implemente)
        rag_keywords = [
            "explicar", "qué es", "cómo funciona", "documentación", "procedimiento",
            "política", "guía", "manual", "instrucciones", "definición",
            "concepto", "proceso", "metodología", "normativa"
        ]
        
        query_lower = query.lower()
        
        # Contar matches
        sql_matches = sum(1 for keyword in sql_keywords if keyword in query_lower)
        rag_matches = sum(1 for keyword in rag_keywords if keyword in query_lower)
        
        # Determinar intención
        if sql_matches > rag_matches:
            intent = QueryIntent.SQL
            confidence = min(0.9, 0.5 + (sql_matches * 0.1))
        elif rag_matches > sql_matches:
            intent = QueryIntent.RAG
            confidence = min(0.9, 0.5 + (rag_matches * 0.1))
        elif sql_matches == rag_matches and sql_matches > 0:
            intent = QueryIntent.HYBRID
            confidence = 0.6
        else:
            # Por defecto, asumir SQL para este dominio específico
            intent = QueryIntent.SQL
            confidence = 0.4
        
        return {
            "intent": intent.value,
            "confidence": confidence,
            "sql_matches": sql_matches,
            "rag_matches": rag_matches,
            "reasoning": f"SQL keywords: {sql_matches}, RAG keywords: {rag_matches}"
        }

class OrchestratorSystem:
    """Sistema orquestador principal que reemplaza MultiAgentSQLSystem"""
    
    def __init__(self, database_url: str, model_name: str = "gemini-1.5-flash"):
        # Configurar LLM
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY no encontrada")
            print("💡 Verifica tu archivo .env o variables de entorno")
            print("🔧 Ejemplo en .env: GOOGLE_API_KEY=AIza...")
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        print(f"✅ GOOGLE_API_KEY encontrada: {google_api_key[:20]}...")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.0,
            convert_system_message_to_human=True
        )
        
        # Inicializar memoria compartida
        self.memory_manager = ConversationMemoryManager()
        
        # Inicializar agentes especializados
        self.router = RouterAgent(self.llm)
        self.sql_agent = SQLAgentSystem(database_url, self.llm, self.memory_manager)
        
        # Crear pipeline de orquestación
        self.orchestration_pipeline = self._create_orchestration_pipeline()
        
        logger.info("✅ OrchestratorSystem inicializado correctamente")
    
    def _create_orchestration_pipeline(self):
        """Crear pipeline de orquestación con LangGraph"""
        
        def router_node(state: OrchestratorState):
            """Nodo router que clasifica la intención"""
            classification = self.router.classify_intent(state['query'])
            
            logger.info(f"🔀 Query clasificada como: {classification['intent']} (confianza: {classification['confidence']:.2f})")
            
            return {
                "intent": classification['intent'],
                "confidence": classification['confidence'],
                "query_type": classification['intent']
            }
        
        def sql_processing_node(state: OrchestratorState):
            """Nodo de procesamiento SQL"""
            result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
            
            return {
                "sql_result": result.get('sql_raw_result', ''),
                "final_response": result.get('response', ''),
                "query_type": "sql"
            }
        
        def rag_processing_node(state: OrchestratorState):
            """Nodo de procesamiento RAG (placeholder por ahora)"""
            # TODO: Implementar cuando RAG esté listo
            return {
                "rag_result": "RAG no implementado aún",
                "final_response": "Lo siento, el sistema de conocimiento externo aún no está disponible. ¿Puedo ayudarte con consultas de datos transaccionales?",
                "query_type": "rag"
            }
        
        def hybrid_processing_node(state: OrchestratorState):
            """Nodo de procesamiento híbrido (placeholder por ahora)"""
            # Por ahora, redirigir a SQL
            result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
            
            return {
                "sql_result": result.get('sql_raw_result', ''),
                "rag_result": "Componente RAG pendiente",
                "final_response": result.get('response', ''),
                "query_type": "hybrid"
            }
        
        def determine_route(state: OrchestratorState):
            """Determinar la ruta basada en la intención"""
            intent = state.get('intent', 'sql')
            
            if intent == 'rag':
                return 'rag_processing'
            elif intent == 'hybrid':
                return 'hybrid_processing'
            else:
                return 'sql_processing'
        
        # Crear StateGraph
        workflow = StateGraph(OrchestratorState)
        
        # Agregar nodos
        workflow.add_node("router", router_node)
        workflow.add_node("sql_processing", sql_processing_node)
        workflow.add_node("rag_processing", rag_processing_node)
        workflow.add_node("hybrid_processing", hybrid_processing_node)
        
        # Definir flujo
        workflow.set_entry_point("router")
        
        # Routing condicional desde router
        workflow.add_conditional_edges(
            "router",
            determine_route,
            {
                "sql_processing": "sql_processing",
                "rag_processing": "rag_processing", 
                "hybrid_processing": "hybrid_processing"
            }
        )
        
        # Todos los nodos de procesamiento van al final
        workflow.add_edge("sql_processing", END)
        workflow.add_edge("rag_processing", END)
        workflow.add_edge("hybrid_processing", END)
        
        return workflow.compile()
    
    async def process_message(self, message: str, user_id: str) -> Dict[str, Any]:
        """Procesar mensaje principal - mantiene compatibilidad con API existente"""
        try:
            initial_state = {
                "query": message,
                "user_id": user_id,
                "intent": "",
                "confidence": 0.0,
                "sql_result": "",
                "rag_result": "",
                "final_response": "",
                "query_type": ""
            }
            
            # Ejecutar pipeline de orquestación
            result = self.orchestration_pipeline.invoke(initial_state)
            
            logger.info(f"✅ Consulta procesada: {result['query_type']} (confianza: {result.get('confidence', 0):.2f})")
            
            return {
                "success": True,
                "response": result["final_response"],
                "database_result": result.get("sql_result", ""),
                "detailed_analysis": "",  # Mantener compatibilidad
                "query_type": result.get("query_type", "unknown"),
                "intent": result.get("intent", "unknown"),
                "confidence": result.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Error procesando consulta. Verifica configuración del sistema.",
                "query_type": "error"
            }

# Mantener compatibilidad con código existente
MultiAgentSQLSystem = OrchestratorSystem