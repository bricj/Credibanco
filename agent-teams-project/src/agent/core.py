# import logging
# import os
# from typing import Dict, Any, TypedDict
# from enum import Enum

# # Cargar variables de entorno
# try:
#     from dotenv import load_dotenv
#     load_dotenv()
#     print("✅ Variables de entorno cargadas desde .env")
# except ImportError:
#     print("⚠️ python-dotenv no disponible, usando variables del sistema")
# except Exception as e:
#     print(f"⚠️ Error cargando .env: {e}")

# from langchain_google_genai import ChatGoogleGenerativeAI
# from langgraph.graph import StateGraph, END
# from .sql_agent import SQLAgentSystem
# from .rag_agent import RAGAgentSystem
# from .memory import ConversationMemoryManager

# logger = logging.getLogger(__name__)

# class QueryIntent(Enum):
#     SQL = "sql"
#     RAG = "rag"
#     HYBRID = "hybrid"
#     UNKNOWN = "unknown"

# class OrchestratorState(TypedDict):
#     query: str
#     user_id: str
#     intent: str
#     confidence: float
#     sql_result: str
#     rag_result: str
#     final_response: str
#     query_type: str

# class RouterAgent:
#     """Agente router que determina el tipo de consulta"""
    
#     def __init__(self, llm: ChatGoogleGenerativeAI):
#         self.llm = llm
    
#     def classify_intent(self, query: str) -> Dict[str, Any]:
#         """Clasificar la intención de la consulta"""
        
#         # Keywords específicos para SQL
#         sql_keywords = [
#             "total", "suma", "cantidad", "transacciones", "periodo", "franquicia", 
#             "plataforma", "valor", "análisis", "reporte", "datos", "consulta",
#             "cuánto", "cuántos", "mostrar", "listar", "comparar", "grupo",
#             "mes", "año", "fecha", "establecimiento", "entidad"
#         ]
        
#         # Keywords específicos para RAG (cuando se implemente)
#         rag_keywords = [
#             "explicar", "qué es", "cómo funciona", "documentación", "procedimiento",
#             "política", "guía", "manual", "instrucciones", "definición",
#             "concepto", "proceso", "metodología", "normativa"
#         ]
        
#         query_lower = query.lower()
        
#         # Contar matches
#         sql_matches = sum(1 for keyword in sql_keywords if keyword in query_lower)
#         rag_matches = sum(1 for keyword in rag_keywords if keyword in query_lower)
        
#         # Determinar intención
#         if sql_matches > rag_matches:
#             intent = QueryIntent.SQL
#             confidence = min(0.9, 0.5 + (sql_matches * 0.1))
#         elif rag_matches > sql_matches:
#             intent = QueryIntent.RAG
#             confidence = min(0.9, 0.5 + (rag_matches * 0.1))
#         elif sql_matches == rag_matches and sql_matches > 0:
#             intent = QueryIntent.HYBRID
#             confidence = 0.6
#         else:
#             # Por defecto, asumir SQL para este dominio específico
#             intent = QueryIntent.SQL
#             confidence = 0.4
        
#         return {
#             "intent": intent.value,
#             "confidence": confidence,
#             "sql_matches": sql_matches,
#             "rag_matches": rag_matches,
#             "reasoning": f"SQL keywords: {sql_matches}, RAG keywords: {rag_matches}"
#         }

# class OrchestratorSystem:
#     """Sistema orquestador principal que reemplaza MultiAgentSQLSystem"""
    
#     def __init__(self, database_url: str, model_name: str = "gemini-1.5-flash"):

#         # Configurar LLM
#         google_api_key = os.getenv("GOOGLE_API_KEY")
#         if not google_api_key:
#             print("❌ GOOGLE_API_KEY no encontrada")
#             print("💡 Verifica tu archivo .env o variables de entorno")
#             print("🔧 Ejemplo en .env: GOOGLE_API_KEY=AIza...")
#             raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
#         print(f"✅ GOOGLE_API_KEY encontrada: {google_api_key[:20]}...")
        
#         self.llm = ChatGoogleGenerativeAI(
#             model=model_name,
#             google_api_key=google_api_key,
#             temperature=0.0,
#             convert_system_message_to_human=True
#         )
        
#         # Inicializar memoria compartida
#         self.memory_manager = ConversationMemoryManager()
        
#         # Inicializar agentes especializados
#         self.router = RouterAgent(self.llm)
#         self.sql_agent = SQLAgentSystem(database_url, self.llm, self.memory_manager)
#         self.rag_agent = RAGAgentSystem(self.llm, self.memory_manager)
        
#         # Crear pipeline de orquestación
#         self.orchestration_pipeline = self._create_orchestration_pipeline()
        
#         logger.info("✅ OrchestratorSystem inicializado correctamente")
    
#     def _create_orchestration_pipeline(self):
#         """Crear pipeline de orquestación con LangGraph"""
        
#         def router_node(state: OrchestratorState):
#             """Nodo router que clasifica la intención"""
#             classification = self.router.classify_intent(state['query'])
            
#             logger.info(f"🔀 Query clasificada como: {classification['intent']} (confianza: {classification['confidence']:.2f})")
            
#             return {
#                 "intent": classification['intent'],
#                 "confidence": classification['confidence'],
#                 "query_type": classification['intent']
#             }
        
#         def sql_processing_node(state: OrchestratorState):
#             """Nodo de procesamiento SQL"""
#             result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
            
#             return {
#                 "sql_result": result.get('sql_raw_result', ''),
#                 "final_response": result.get('response', ''),
#                 "query_type": "sql"
#             }
        
#         def rag_processing_node(state: OrchestratorState):
#             """Nodo de procesamiento RAG"""
#             result = self.rag_agent.process_rag_query(state['query'], state['user_id'])
            
#             return {
#                 "rag_result": result.get('response', ''),
#                 "final_response": result.get('response', ''),
#                 "query_type": "rag"
#             }
        
#         def hybrid_processing_node(state: OrchestratorState):
#             """Nodo de procesamiento híbrido (placeholder por ahora)"""
#             # Por ahora, redirigir a SQL
#             result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
            
#             return {
#                 "sql_result": result.get('sql_raw_result', ''),
#                 "rag_result": "Componente RAG pendiente",
#                 "final_response": result.get('response', ''),
#                 "query_type": "hybrid"
#             }
        
#         def determine_route(state: OrchestratorState):
#             """Determinar la ruta basada en la intención"""
#             intent = state.get('intent', 'sql')
            
#             if intent == 'rag':
#                 return 'rag_processing'
#             elif intent == 'hybrid':
#                 return 'hybrid_processing'
#             else:
#                 return 'sql_processing'
        
#         # Crear StateGraph
#         workflow = StateGraph(OrchestratorState)
        
#         # Agregar nodos
#         workflow.add_node("router", router_node)
#         workflow.add_node("sql_processing", sql_processing_node)
#         workflow.add_node("rag_processing", rag_processing_node)
#         workflow.add_node("hybrid_processing", hybrid_processing_node)
        
#         # Definir flujo
#         workflow.set_entry_point("router")
        
#         # Routing condicional desde router
#         workflow.add_conditional_edges(
#             "router",
#             determine_route,
#             {
#                 "sql_processing": "sql_processing",
#                 "rag_processing": "rag_processing", 
#                 "hybrid_processing": "hybrid_processing"
#             }
#         )
        
#         # Todos los nodos de procesamiento van al final
#         workflow.add_edge("sql_processing", END)
#         workflow.add_edge("rag_processing", END)
#         workflow.add_edge("hybrid_processing", END)
        
#         return workflow.compile()
    
#     async def process_message(self, message: str, user_id: str) -> Dict[str, Any]:
#         """Procesar mensaje principal - mantiene compatibilidad con API existente"""
#         try:
#             initial_state = {
#                 "query": message,
#                 "user_id": user_id,
#                 "intent": "",
#                 "confidence": 0.0,
#                 "sql_result": "",
#                 "rag_result": "",
#                 "final_response": "",
#                 "query_type": ""
#             }
            
#             # Ejecutar pipeline de orquestación
#             result = self.orchestration_pipeline.invoke(initial_state)
            
#             logger.info(f"✅ Consulta procesada: {result['query_type']} (confianza: {result.get('confidence', 0):.2f})")
            
#             return {
#                 "success": True,
#                 "response": result["final_response"],
#                 "database_result": result.get("sql_result", ""),
#                 "detailed_analysis": "",  # Mantener compatibilidad
#                 "query_type": result.get("query_type", "unknown"),
#                 "intent": result.get("intent", "unknown"),
#                 "confidence": result.get("confidence", 0.0)
#             }
            
#         except Exception as e:
#             logger.error(f"Error processing message: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "response": "Error procesando consulta. Verifica configuración del sistema.",
#                 "query_type": "error"
#             }

# # Mantener compatibilidad con código existente
# MultiAgentSQLSystem = OrchestratorSystem

############################################

import logging
import os
import time
from typing import Dict, Any, TypedDict
from enum import Enum
from collections import defaultdict

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
from .rag_agent import RAGAgentSystem
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
    def __init__(self, llm: ChatGoogleGenerativeAI, sql_weight=1.2, rag_weight=1.0, confidence_threshold=0.6):
        self.llm = llm
        self.sql_weight = sql_weight
        self.rag_weight = rag_weight
        self.confidence_threshold = confidence_threshold

    def classify_intent(self, query: str) -> Dict[str, Any]:
        sql_keywords = [
            "busqueda en la base de datos", "búsqueda en la base de datos",
            "obtener de la base de datos", "extraer de la base de datos",
            "calcular a partir de la base de datos", "consultar la base de datos",
            "buscar en la base de datos", "datos de la base de datos",
            "información de la base de datos", "registros de la base de datos",
            "tabla de la base de datos", "query en la base de datos",
            "filtrar en la base de datos", "agrupar en la base de datos",
            "sumar de la base de datos", "contar en la base de datos",
            "mostrar de la base de datos", "listar de la base de datos"
        ]

        rag_keywords = [
            "buscar en los estados financieros", "búsqueda en los estados financieros",
            "obtener de los estados financieros", "extraer de los estados financieros",
            "información de los estados financieros", "datos de los estados financieros",
            "consultar los estados financieros", "revisar los estados financieros",
            "buscar en el informe de gestión", "búsqueda en el informe de gestión",
            "obtener del informe de gestión", "extraer del informe de gestión",
            "información del informe de gestión", "datos del informe de gestión",
            "consultar el informe de gestión", "revisar el informe de gestión",
            "según los estados financieros", "conforme a los estados financieros",
            "de acuerdo al informe de gestión", "según el informe de gestión"
        ]

        hybrid_keywords = [
            "comparar base de datos con estados financieros",
            "contrastar datos con informe de gestión",
            "validar base de datos contra estados financieros",
            "análisis conjunto de base de datos e informes",
            "cruzar información de base de datos y estados financieros",
            "verificar datos contra informe de gestión"
        ]

        query_lower = query.lower()
        sql_matches = sum(1 for k in sql_keywords if k in query_lower)
        rag_matches = sum(1 for k in rag_keywords if k in query_lower)
        hybrid_matches = sum(1 for k in hybrid_keywords if k in query_lower)

        sql_score = sql_matches * self.sql_weight
        rag_score = rag_matches * self.rag_weight
        hybrid_score = hybrid_matches * 1.1
        total_score = sql_score + rag_score + hybrid_score

        if total_score == 0:
            if any(w in query_lower for w in ["cuánto", "monto", "total", "suma"]):
                intent = QueryIntent.SQL
                confidence = 0.4
            elif any(w in query_lower for w in ["qué", "cómo", "explicar"]):
                intent = QueryIntent.RAG
                confidence = 0.4
            else:
                intent = QueryIntent.SQL
                confidence = 0.3
        elif hybrid_score > 0 and (sql_score > 0 or rag_score > 0):
            intent = QueryIntent.HYBRID
            confidence = min(0.95, 0.6 + (hybrid_score / max(total_score, 1)) * 0.3)
        elif sql_score > rag_score:
            intent = QueryIntent.SQL
            confidence = min(0.95, 0.5 + (sql_score / max(total_score, 1)) * 0.4)
        elif rag_score > sql_score:
            intent = QueryIntent.RAG
            confidence = min(0.95, 0.5 + (rag_score / max(total_score, 1)) * 0.4)
        else:
            intent = QueryIntent.SQL
            confidence = 0.5

        if confidence < self.confidence_threshold:
            if intent == QueryIntent.HYBRID:
                intent = QueryIntent.SQL
            confidence = 0.4

        return {
            "intent": intent.value,
            "confidence": confidence,
            "sql_matches": sql_matches,
            "rag_matches": rag_matches,
            "hybrid_matches": hybrid_matches,
            "reasoning": f"SQL: {sql_matches}, RAG: {rag_matches}, Híbrido: {hybrid_matches}"
        }

class OrchestratorSystem:
    def __init__(self, database_url: str, model_name: str = "gemini-1.5-flash", sql_weight: float = 1.2, rag_weight: float = 1.5, confidence_threshold: float = 0.6, fallback_to_sql: bool = True):
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY no encontrada")
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.0,
            convert_system_message_to_human=True
        )

        self.memory_manager = ConversationMemoryManager()
        self.router = RouterAgent(self.llm, sql_weight, rag_weight, confidence_threshold)
        self.fallback_to_sql = fallback_to_sql
        self.sql_agent = SQLAgentSystem(database_url, self.llm, self.memory_manager)
        self.rag_agent = RAGAgentSystem(self.llm, self.memory_manager)

        self.metrics = defaultdict(int)
        self.confidence_sum = defaultdict(float)
        self.times = defaultdict(list)
        self.orchestration_pipeline = self._create_orchestration_pipeline()
        logger.info("✅ OrchestratorSystem inicializado correctamente")

    def _create_orchestration_pipeline(self):
        def router_node(state: OrchestratorState):
            classification = self.router.classify_intent(state['query'])
            logger.info(f"🔀 Query clasificada como: {classification['intent']} (confianza: {classification['confidence']:.2f})")
            return {
                "intent": classification['intent'],
                "confidence": classification['confidence'],
                "query_type": classification['intent']
            }

        def sql_processing_node(state: OrchestratorState):
            result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
            return {
                "sql_result": result.get('sql_raw_result', ''),
                "final_response": result.get('response', ''),
                "query_type": "sql"
            }

        def rag_processing_node(state: OrchestratorState):
            try:
                result = self.rag_agent.process_rag_query(state['query'], state['user_id'])
                return {
                    "rag_result": result.get('response', ''),
                    "final_response": result.get('response', ''),
                    "query_type": "rag"
                }
            except Exception as e:
                logger.error(f"Error en RAG: {e}")
                if self.fallback_to_sql:
                    return sql_processing_node(state)
                return {"final_response": f"Error RAG: {str(e)}", "query_type": "rag_error"}

        def hybrid_processing_node(state: OrchestratorState):
            try:
                sql_result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
                rag_result = self.rag_agent.process_rag_query(state['query'], state['user_id'])
                combined = f"**Datos:** {sql_result.get('response', '')}\n\n**Contexto:** {rag_result.get('response', '')}"
                return {
                    "sql_result": sql_result.get('sql_raw_result', ''),
                    "rag_result": rag_result.get('response', ''),
                    "final_response": combined,
                    "query_type": "hybrid"
                }
            except Exception as e:
                logger.error(f"Error híbrido: {e}")
                if self.fallback_to_sql:
                    return sql_processing_node(state)
                return {"final_response": f"Error híbrido: {str(e)}", "query_type": "hybrid_error"}

        def determine_route(state: OrchestratorState):
            intent = state.get('intent', 'sql')
            if intent == 'rag':
                return 'rag_processing'
            elif intent == 'hybrid':
                return 'hybrid_processing'
            else:
                return 'sql_processing'

        workflow = StateGraph(OrchestratorState)
        workflow.add_node("router", router_node)
        workflow.add_node("sql_processing", sql_processing_node)
        workflow.add_node("rag_processing", rag_processing_node)
        workflow.add_node("hybrid_processing", hybrid_processing_node)
        workflow.set_entry_point("router")
        workflow.add_conditional_edges("router", determine_route, {
            "sql_processing": "sql_processing",
            "rag_processing": "rag_processing",
            "hybrid_processing": "hybrid_processing"
        })
        workflow.add_edge("sql_processing", END)
        workflow.add_edge("rag_processing", END)
        workflow.add_edge("hybrid_processing", END)
        return workflow.compile()

    async def process_message(self, message: str, user_id: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            initial_state = {
                "query": message, "user_id": user_id, "intent": "",
                "confidence": 0.0, "sql_result": "", "rag_result": "",
                "final_response": "", "query_type": ""
            }
            result = self.orchestration_pipeline.invoke(initial_state)
            processing_time = time.time() - start_time
            query_type = result.get("query_type", "unknown")
            intent = result.get("intent", "unknown")
            confidence = result.get("confidence", 0.0)
            self.metrics[f"total"] += 1
            self.metrics[f"by_{query_type}"] += 1
            self.confidence_sum[intent] += confidence
            self.times[query_type].append(processing_time)
            logger.info(f"✅ {query_type} - {confidence:.2f} - {processing_time:.2f}s")
            return {
                "success": True,
                "response": result["final_response"],
                "database_result": result.get("sql_result", ""),
                "query_type": query_type,
                "intent": intent,
                "confidence": confidence
            }
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Error procesando consulta.",
                "query_type": "error"
            }

    def get_metrics(self) -> Dict[str, Any]:
        total = self.metrics.get("total", 0)
        if total == 0:
            return {"message": "Sin queries"}
        return {
            "total": total,
            "sql": f"{self.metrics.get('by_sql', 0)} ({self.metrics.get('by_sql', 0)/total*100:.1f}%)",
            "rag": f"{self.metrics.get('by_rag', 0)} ({self.metrics.get('by_rag', 0)/total*100:.1f}%)",
            "hybrid": f"{self.metrics.get('by_hybrid', 0)} ({self.metrics.get('by_hybrid', 0)/total*100:.1f}%)",
            "errors": self.metrics.get("errors", 0),
            "avg_sql_time": f"{sum(self.times['sql'])/len(self.times['sql']):.2f}s" if self.times['sql'] else "N/A",
            "avg_rag_time": f"{sum(self.times['rag'])/len(self.times['rag']):.2f}s" if self.times['rag'] else "N/A"
        }

MultiAgentSQLSystem = OrchestratorSystem
import logging
import os
import time
from typing import Dict, Any, TypedDict
from enum import Enum
from collections import defaultdict

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
from .rag_agent import RAGAgentSystem
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
    def __init__(self, llm: ChatGoogleGenerativeAI, sql_weight=1.2, rag_weight=1.0, confidence_threshold=0.6):
        self.llm = llm
        self.sql_weight = sql_weight
        self.rag_weight = rag_weight
        self.confidence_threshold = confidence_threshold

    def classify_intent(self, query: str) -> Dict[str, Any]:
        sql_keywords = [
            "busqueda en la base de datos", "búsqueda en la base de datos",
            "obtener de la base de datos", "extraer de la base de datos",
            "calcular a partir de la base de datos", "consultar la base de datos",
            "buscar en la base de datos", "datos de la base de datos",
            "información de la base de datos", "registros de la base de datos",
            "tabla de la base de datos", "query en la base de datos",
            "filtrar en la base de datos", "agrupar en la base de datos",
            "sumar de la base de datos", "contar en la base de datos",
            "mostrar de la base de datos", "listar de la base de datos"
        ]

        rag_keywords = [
            "buscar en los estados financieros", "búsqueda en los estados financieros",
            "obtener de los estados financieros", "extraer de los estados financieros",
            "información de los estados financieros", "datos de los estados financieros",
            "consultar los estados financieros", "revisar los estados financieros",
            "buscar en el informe de gestión", "búsqueda en el informe de gestión",
            "obtener del informe de gestión", "extraer del informe de gestión",
            "información del informe de gestión", "datos del informe de gestión",
            "consultar el informe de gestión", "revisar el informe de gestión",
            "según los estados financieros", "conforme a los estados financieros",
            "de acuerdo al informe de gestión", "según el informe de gestión"
        ]

        hybrid_keywords = [
            "comparar base de datos con estados financieros",
            "contrastar datos con informe de gestión",
            "validar base de datos contra estados financieros",
            "análisis conjunto de base de datos e informes",
            "cruzar información de base de datos y estados financieros",
            "verificar datos contra informe de gestión"
        ]

        query_lower = query.lower()
        sql_matches = sum(1 for k in sql_keywords if k in query_lower)
        rag_matches = sum(1 for k in rag_keywords if k in query_lower)
        hybrid_matches = sum(1 for k in hybrid_keywords if k in query_lower)

        sql_score = sql_matches * self.sql_weight
        rag_score = rag_matches * self.rag_weight
        hybrid_score = hybrid_matches * 1.1
        total_score = sql_score + rag_score + hybrid_score

        if total_score == 0:
            if any(w in query_lower for w in ["cuánto", "monto", "total", "suma"]):
                intent = QueryIntent.SQL
                confidence = 0.4
            elif any(w in query_lower for w in ["qué", "cómo", "explicar"]):
                intent = QueryIntent.RAG
                confidence = 0.4
            else:
                intent = QueryIntent.SQL
                confidence = 0.3
        elif hybrid_score > 0 and (sql_score > 0 or rag_score > 0):
            intent = QueryIntent.HYBRID
            confidence = min(0.95, 0.6 + (hybrid_score / max(total_score, 1)) * 0.3)
        elif sql_score > rag_score:
            intent = QueryIntent.SQL
            confidence = min(0.95, 0.5 + (sql_score / max(total_score, 1)) * 0.4)
        elif rag_score > sql_score:
            intent = QueryIntent.RAG
            confidence = min(0.95, 0.5 + (rag_score / max(total_score, 1)) * 0.4)
        else:
            intent = QueryIntent.SQL
            confidence = 0.5

        if confidence < self.confidence_threshold:
            if intent == QueryIntent.HYBRID:
                intent = QueryIntent.SQL
            confidence = 0.4

        return {
            "intent": intent.value,
            "confidence": confidence,
            "sql_matches": sql_matches,
            "rag_matches": rag_matches,
            "hybrid_matches": hybrid_matches,
            "reasoning": f"SQL: {sql_matches}, RAG: {rag_matches}, Híbrido: {hybrid_matches}"
        }

class OrchestratorSystem:
    def __init__(self, database_url: str, model_name: str = "gemini-1.5-flash", sql_weight: float = 1.2, rag_weight: float = 1.5, confidence_threshold: float = 0.6, fallback_to_sql: bool = True):
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            print("❌ GOOGLE_API_KEY no encontrada")
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=google_api_key,
            temperature=0.0,
            convert_system_message_to_human=True
        )

        self.memory_manager = ConversationMemoryManager()
        self.router = RouterAgent(self.llm, sql_weight, rag_weight, confidence_threshold)
        self.fallback_to_sql = fallback_to_sql
        self.sql_agent = SQLAgentSystem(database_url, self.llm, self.memory_manager)
        self.rag_agent = RAGAgentSystem(self.llm, self.memory_manager)

        self.metrics = defaultdict(int)
        self.confidence_sum = defaultdict(float)
        self.times = defaultdict(list)
        self.orchestration_pipeline = self._create_orchestration_pipeline()
        logger.info("✅ OrchestratorSystem inicializado correctamente")

    def _create_orchestration_pipeline(self):
        def router_node(state: OrchestratorState):
            classification = self.router.classify_intent(state['query'])
            logger.info(f"🔀 Query clasificada como: {classification['intent']} (confianza: {classification['confidence']:.2f})")
            return {
                "intent": classification['intent'],
                "confidence": classification['confidence'],
                "query_type": classification['intent']
            }

        def sql_processing_node(state: OrchestratorState):
            result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
            return {
                "sql_result": result.get('sql_raw_result', ''),
                "final_response": result.get('response', ''),
                "query_type": "sql"
            }

        def rag_processing_node(state: OrchestratorState):
            try:
                result = self.rag_agent.process_rag_query(state['query'], state['user_id'])
                return {
                    "rag_result": result.get('response', ''),
                    "final_response": result.get('response', ''),
                    "query_type": "rag"
                }
            except Exception as e:
                logger.error(f"Error en RAG: {e}")
                if self.fallback_to_sql:
                    return sql_processing_node(state)
                return {"final_response": f"Error RAG: {str(e)}", "query_type": "rag_error"}

        def hybrid_processing_node(state: OrchestratorState):
            try:
                sql_result = self.sql_agent.process_sql_query(state['query'], state['user_id'])
                rag_result = self.rag_agent.process_rag_query(state['query'], state['user_id'])
                combined = f"**Datos:** {sql_result.get('response', '')}\n\n**Contexto:** {rag_result.get('response', '')}"
                return {
                    "sql_result": sql_result.get('sql_raw_result', ''),
                    "rag_result": rag_result.get('response', ''),
                    "final_response": combined,
                    "query_type": "hybrid"
                }
            except Exception as e:
                logger.error(f"Error híbrido: {e}")
                if self.fallback_to_sql:
                    return sql_processing_node(state)
                return {"final_response": f"Error híbrido: {str(e)}", "query_type": "hybrid_error"}

        def determine_route(state: OrchestratorState):
            intent = state.get('intent', 'sql')
            if intent == 'rag':
                return 'rag_processing'
            elif intent == 'hybrid':
                return 'hybrid_processing'
            else:
                return 'sql_processing'

        workflow = StateGraph(OrchestratorState)
        workflow.add_node("router", router_node)
        workflow.add_node("sql_processing", sql_processing_node)
        workflow.add_node("rag_processing", rag_processing_node)
        workflow.add_node("hybrid_processing", hybrid_processing_node)
        workflow.set_entry_point("router")
        workflow.add_conditional_edges("router", determine_route, {
            "sql_processing": "sql_processing",
            "rag_processing": "rag_processing",
            "hybrid_processing": "hybrid_processing"
        })
        workflow.add_edge("sql_processing", END)
        workflow.add_edge("rag_processing", END)
        workflow.add_edge("hybrid_processing", END)
        return workflow.compile()

    async def process_message(self, message: str, user_id: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            initial_state = {
                "query": message, "user_id": user_id, "intent": "",
                "confidence": 0.0, "sql_result": "", "rag_result": "",
                "final_response": "", "query_type": ""
            }
            result = self.orchestration_pipeline.invoke(initial_state)
            processing_time = time.time() - start_time
            query_type = result.get("query_type", "unknown")
            intent = result.get("intent", "unknown")
            confidence = result.get("confidence", 0.0)
            self.metrics[f"total"] += 1
            self.metrics[f"by_{query_type}"] += 1
            self.confidence_sum[intent] += confidence
            self.times[query_type].append(processing_time)
            logger.info(f"✅ {query_type} - {confidence:.2f} - {processing_time:.2f}s")
            return {
                "success": True,
                "response": result["final_response"],
                "database_result": result.get("sql_result", ""),
                "query_type": query_type,
                "intent": intent,
                "confidence": confidence
            }
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Error procesando consulta.",
                "query_type": "error"
            }

    def get_metrics(self) -> Dict[str, Any]:
        total = self.metrics.get("total", 0)
        if total == 0:
            return {"message": "Sin queries"}
        return {
            "total": total,
            "sql": f"{self.metrics.get('by_sql', 0)} ({self.metrics.get('by_sql', 0)/total*100:.1f}%)",
            "rag": f"{self.metrics.get('by_rag', 0)} ({self.metrics.get('by_rag', 0)/total*100:.1f}%)",
            "hybrid": f"{self.metrics.get('by_hybrid', 0)} ({self.metrics.get('by_hybrid', 0)/total*100:.1f}%)",
            "errors": self.metrics.get("errors", 0),
            "avg_sql_time": f"{sum(self.times['sql'])/len(self.times['sql']):.2f}s" if self.times['sql'] else "N/A",
            "avg_rag_time": f"{sum(self.times['rag'])/len(self.times['rag']):.2f}s" if self.times['rag'] else "N/A"
        }

MultiAgentSQLSystem = OrchestratorSystem
