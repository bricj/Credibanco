# import logging
# from typing import Dict, Any, TypedDict
# #from langchain_openai import ChatOpenAI   OPENAI
# from langchain_google_vertexai import ChatVertexAI
# from langchain_community.utilities.sql_database import SQLDatabase
# from langchain.agents import create_openai_tools_agent, AgentExecutor
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langgraph.graph import StateGraph, END
# from .tools import SQLTools, AnalystTools, ReportTools
# from .memory import ConversationMemoryManager
# import os

# logger = logging.getLogger(__name__)

# class AnalysisState(TypedDict):
#     query: str
#     database_result: str
#     final_report: str
#     user_id: str

# class MultiAgentSQLSystem:
#     # def __init__(self, database_url: str, model_name: str = "gpt-4o-mini"): # OPENAI
#     #     self.llm = ChatOpenAI(model_name=model_name, temperature=0.0)       # OPENAI
#     #  
#     def __init__(self, database_url: str, model_name: str = "gemini-1.5-flash"):
#         # Configurar Vertex AI
#         project_id = os.getenv("GCP_PROJECT_ID")
#         location = os.getenv("GCP_REGION", "us-central1")
        
#         if not project_id or project_id == "temp":
#             raise ValueError("GCP_PROJECT_ID must be set for Vertex AI")
        
#         self.llm = ChatVertexAI(
#             model_name=model_name,
#             project=project_id,
#             location=location,
#             temperature=0.0,
#             max_tokens=8192
#         )

#         self.db = SQLDatabase.from_uri(database_url)
        
#         # Inicializar herramientas
#         self.sql_tools = SQLTools(self.db)
        
#         # Inicializar memoria
#         self.memory_manager = ConversationMemoryManager()
        
#         # Crear agentes
#         self.sql_agent = self._create_sql_agent()
#         self.unified_agent = self._create_unified_agent()
        
#         # Crear pipeline optimizado
#         self.analysis_pipeline = self._create_optimized_pipeline()
    
#     def _create_sql_agent(self):
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", """Eres un ingeniero de bases de datos experimentado que domina la creación de consultas SQL eficientes y complejas.
#                 Tienes un profundo entendimiento de cómo funcionan diferentes bases de datos y cómo optimizar consultas.
#                 Usa `list_tables` para encontrar las tablas disponibles.
#                 Usa `tables_schema` para entender los metadatos de las tablas.
#                 Usa `execute_sql` para verificar la correctitud de tus consultas.
                
#                 Sé conciso y eficiente. Ejecuta la consulta y retorna los resultados claramente.
#                 Responde siempre en español."""),
#             MessagesPlaceholder(variable_name="chat_history"),
#             ("human", "{input}"),
#             ("placeholder", "{agent_scratchpad}"),
#         ])
        
#         agent = create_openai_tools_agent(self.llm, self.sql_tools.get_tools(), prompt)
#         return AgentExecutor(agent=agent, tools=self.sql_tools.get_tools(), verbose=True)
    
#     def _create_unified_agent(self):
#         """Agente unificado que hace análisis y reporte en una sola llamada"""
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", """Eres un analista de datos experto y escritor de reportes ejecutivos. Tu trabajo es:
#                 1. Analizar los resultados de consultas SQL proporcionados
#                 2. Identificar hallazgos claves
#                 3. Crear una respuesta concisa en lenguaje natural
#                 4. No generar información ni análisis si no existe en los datos
                
#                 IMPORTANTE: Responde SIEMPRE en español.
                
#                 Sé conciso, basado en datos y accionable. Enfócate en los insights más importantes."""),
#             MessagesPlaceholder(variable_name="chat_history"),
#             ("human", "Consulta: {query}\n\nResultados SQL: {sql_results}\n\nPor favor proporciona análisis y recomendaciones en español."),
#             ("placeholder", "{agent_scratchpad}"),
#         ])
        
#         agent = create_openai_tools_agent(self.llm, [], prompt)
#         return AgentExecutor(agent=agent, tools=[], verbose=True)
    
#     def _create_optimized_pipeline(self):
#         def extract_data_node(state: AnalysisState):
#             # Obtener memoria del usuario
#             chat_history = self.memory_manager.get_memory(state['user_id'])
            
#             result = self.sql_agent.invoke({
#                 "input": f"Extract data that is required for the query: {state['query']}",
#                 "chat_history": chat_history
#             })
            
#             # Guardar en memoria
#             self.memory_manager.save_interaction(
#                 state['user_id'], 
#                 state['query'], 
#                 result["output"]
#             )
            
#             return {"database_result": result["output"]}
        
#         def unified_analysis_node(state: AnalysisState):
#             """Nodo unificado que hace análisis y reporte en una sola llamada"""
#             chat_history = self.memory_manager.get_memory(state['user_id'])
            
#             result = self.unified_agent.invoke({
#                 "query": state['query'],
#                 "sql_results": state['database_result'],
#                 "chat_history": chat_history
#             })
            
#             return {"final_report": result["output"]}
        
#         workflow = StateGraph(AnalysisState)
#         workflow.add_node("extract_data", extract_data_node)
#         workflow.add_node("unified_analysis", unified_analysis_node)
        
#         workflow.set_entry_point("extract_data")
#         workflow.add_edge("extract_data", "unified_analysis")
#         workflow.add_edge("unified_analysis", END)
        
#         return workflow.compile()
    
#     async def process_message(self, message: str, user_id: str) -> dict:
#         try:
#             initial_state = {"query": message, "user_id": user_id}
#             result = self.analysis_pipeline.invoke(initial_state)
            
#             return {
#                 "success": True,
#                 "response": result["final_report"],
#                 "database_result": result.get("database_result", ""),
#                 "detailed_analysis": ""  # Ya incluido en final_report
#             }
#         except Exception as e:
#             logger.error(f"Error processing message: {e}")
#             return {
#                 "success": False,
#                 "error": str(e),
#                 "response": "Error procesando análisis de datos."
#             }

#######################

import logging
import os
from typing import Dict, Any, TypedDict
import re

# 🆕 AGREGAR: Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()  # Carga el archivo .env si existe
    print("✅ Variables de entorno cargadas desde .env")
except ImportError:
    print("⚠️ python-dotenv no disponible, usando variables del sistema")
except Exception as e:
    print(f"⚠️ Error cargando .env: {e}")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from .tools import SQLTools, AnalystTools, ReportTools
from .memory import ConversationMemoryManager

logger = logging.getLogger(__name__)

class AnalysisState(TypedDict):
    query: str
    database_result: str
    final_report: str
    user_id: str

class MultiAgentSQLSystem:
    def __init__(self, database_url: str, model_name: str = "gemini-1.5-flash"):
        # Configurar Google AI Studio con validación mejorada
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            # Mostrar mensaje más informativo
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
        
        self.db = SQLDatabase.from_uri(database_url)
        
        # Obtener contexto de la base de datos
        self.database_context = self._get_database_context()
        
        # Inicializar herramientas
        self.sql_tools = SQLTools(self.db)
        
        # Inicializar memoria
        self.memory_manager = ConversationMemoryManager()
        
        # Crear agentes
        self.sql_agent = self._create_sql_agent()
        self.unified_agent = self._create_unified_agent()
        
        # Crear pipeline optimizado
        self.analysis_pipeline = self._create_optimized_pipeline()
    
    def _get_database_context(self):
        """Obtiene información sobre la estructura de la base de datos"""
        try:
            # Obtener tablas disponibles
            tables_info = self.db.get_table_info()
            
            # Crear contexto específico basado en las tablas encontradas
            context = f"""
INFORMACIÓN DE LA BASE DE DATOS:

{tables_info}

COLUMNAS ESPECÍFICAS DE TUS DATOS:
- identificador_establecimiento: ID del establecimiento
- nombre_plataforma: Nombre de la plataforma de pago
- entidad_emisor: Entidad que emite
- entidad_autorizador: Entidad autorizadora
- franquicia: Tipo de franquicia (Visa, Mastercard, etc.)
- entidad_adquiriente: Entidad adquiriente
- nombre_subnivel_plataforma: Subnivel de plataforma
- pasarela: Pasarela de pago
- periodo: 📅 COLUMNA DE FECHA/PERIODO (usar para agrupar por tiempo)
- cantidad_transacciones: 📊 NÚMERO de transacciones
- valor_transacciones: 💰 VALOR TOTAL de transacciones (usar para sumas)

GUÍAS ESPECÍFICAS PARA CONSULTAS COMUNES:

1. Para TOTAL DE TRANSACCIONES POR PERIODO:
   - Usar: SELECT periodo, SUM(valor_transacciones) FROM tabla GROUP BY periodo
   - Columna de periodo: "periodo"
   - Columna de valor: "valor_transacciones"

2. Para CANTIDAD DE TRANSACCIONES POR PERIODO:
   - Usar: SELECT periodo, SUM(cantidad_transacciones) FROM tabla GROUP BY periodo
   
3. Para análisis por FRANQUICIA:
   - Usar: SELECT franquicia, SUM(valor_transacciones) FROM tabla GROUP BY franquicia
   
4. Para análisis por PLATAFORMA:
   - Usar: SELECT nombre_plataforma, SUM(valor_transacciones) FROM tabla GROUP BY nombre_plataforma

5. EJEMPLOS DE CONSULTAS CORRECTAS:
   - Total por periodo: SELECT periodo, SUM(valor_transacciones) as total FROM tabla GROUP BY periodo ORDER BY periodo
   - Por franquicia: SELECT franquicia, SUM(valor_transacciones) as total FROM tabla GROUP BY franquicia
   - Por plataforma: SELECT nombre_plataforma, SUM(valor_transacciones) as total FROM tabla GROUP BY nombre_plataforma
"""
            return context
            
        except Exception as e:
            logger.warning(f"No se pudo obtener contexto de BD: {e}")
            return "Usar list_tables y tables_schema para explorar la estructura de la base de datos."
    
    def _create_sql_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""Eres un ingeniero de bases de datos experimentado especializado en SQLite.

CONTEXTO DE LA BASE DE DATOS:
{self.database_context}

TU PROCESO DE TRABAJO:
1. SIEMPRE usa `list_tables` primero para ver las tablas disponibles
2. Usa `tables_schema` para entender la estructura de las tablas relevantes
3. Analiza qué columnas necesitas para responder la pregunta
4. Crea la consulta SQL apropiada
5. Usa `execute_sql` para ejecutar y verificar los resultados
6. IMPORTANTE: SIEMPRE ejecuta la consulta, no solo la muestres

REGLAS IMPORTANTES:
- EJECUTA las consultas SQL, no solo las generes
- Para "total de transacciones por periodo", usar: periodo (fecha) + valor_transacciones (monto)
- Para "cantidad de transacciones", usar: cantidad_transacciones
- Para análisis por franquicia, usar: franquicia
- Para análisis por plataforma, usar: nombre_plataforma
- Sé específico con los nombres de columnas reales
- Si no estás seguro de una estructura, verifica con tables_schema
- Responde siempre en español

EJEMPLOS DE CONSULTAS ESPECÍFICAS PARA TUS DATOS:
- Total valor por periodo: SELECT periodo, SUM(valor_transacciones) as total_valor FROM tabla GROUP BY periodo ORDER BY periodo
- Total cantidad por periodo: SELECT periodo, SUM(cantidad_transacciones) as total_cantidad FROM tabla GROUP BY periodo ORDER BY periodo  
- Por franquicia: SELECT franquicia, SUM(valor_transacciones) as total FROM tabla GROUP BY franquicia ORDER BY total DESC
- Por plataforma: SELECT nombre_plataforma, SUM(valor_transacciones) as total FROM tabla GROUP BY nombre_plataforma ORDER BY total DESC
- Combinado: SELECT periodo, franquicia, SUM(valor_transacciones) as total FROM tabla GROUP BY periodo, franquicia ORDER BY periodo, total DESC

¡EJECUTA SIEMPRE las consultas usando execute_sql!"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.sql_tools.get_tools(), prompt)
        return AgentExecutor(agent=agent, tools=self.sql_tools.get_tools(), verbose=True)
    
    def _create_unified_agent(self):
        """Agente unificado que solo responde lo que se pide"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un analista de datos experto. Tu trabajo es:
                1. Analizar los resultados de consultas SQL proporcionados
                2. Responder directamente la pregunta del usuario
                3. Ser conciso y específico
                
                IMPORTANTE: 
                - Responde SIEMPRE en español
                - Solo proporciona la información solicitada
                - No agregues recomendaciones a menos que se soliciten explícitamente
                - Sé directo y al grano
                - Si hay errores en los datos SQL, menciónalos brevemente
                
                Si el usuario pregunta por un promedio, da el promedio.
                Si pregunta por un conteo, da el conteo.
                Si pregunta por una comparación, da la comparación.
                Si pregunta por totales por periodo, presenta los datos claramente organizados.
                
                Formato para respuestas de totales por periodo:
                📊 **Total de [descripción] por [periodo]:**
                • [Periodo 1]: $[valor] 
                • [Periodo 2]: $[valor]
                • Total general: $[valor]
                
                No agregues análisis extra no solicitado."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Pregunta del usuario: {query}\n\nResultados de la base de datos: {sql_results}\n\nResponde directamente a la pregunta."),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_tools_agent(self.llm, [], prompt)
        return AgentExecutor(agent=agent, tools=[], verbose=True)
    
    def _execute_sql_directly(self, sql_query: str):
        """Ejecuta una consulta SQL directamente cuando las herramientas fallan"""
        try:
            print(f"🔍 Ejecutando consulta directa: {sql_query}")
            
            # Usar el método correcto de SQLDatabase
            try:
                # Método 1: Usar run (más seguro)
                result_str = self.db.run(sql_query)
                print(f"✅ Consulta ejecutada con db.run()")
                print(f"📊 Resultado: {result_str}")
                return f"✅ Resultado de la consulta:\n{result_str}"
                
            except Exception as e1:
                print(f"⚠️ db.run() falló: {e1}")
                try:
                    # Método 2: Usar _execute como fallback
                    result = self.db._execute(sql_query)
                    
                    # Verificar el tipo de resultado
                    if hasattr(result, 'fetchall'):
                        # Es un cursor real
                        rows = result.fetchall()
                        columns = [desc[0] for desc in result.description] if result.description else []
                    else:
                        # Ya es una lista o string
                        rows = result if isinstance(result, list) else [result]
                        columns = []
                    
                    if rows:
                        result_text = f"✅ Consulta ejecutada exitosamente:\n"
                        result_text += f"📊 {len(rows)} resultado(s) encontrado(s)\n\n"
                        
                        for i, row in enumerate(rows[:10], 1):
                            if columns and len(columns) == len(row):
                                row_dict = dict(zip(columns, row))
                                result_text += f"Resultado {i}: {row_dict}\n"
                            else:
                                result_text += f"Resultado {i}: {row}\n"
                        
                        if len(rows) > 10:
                            result_text += f"... y {len(rows) - 10} resultados más\n"
                        
                        return result_text
                    else:
                        return "❌ La consulta no devolvió resultados"
                        
                except Exception as e2:
                    return f"❌ Error ejecutando consulta directa: {str(e2)}"
                
        except Exception as e:
            return f"❌ Error general ejecutando consulta: {str(e)}"
    
    def _create_optimized_pipeline(self):
        def extract_data_node(state: AnalysisState):
            # Obtener memoria del usuario
            chat_history = self.memory_manager.get_memory(state['user_id'])
            
            try:
                # Prompt más específico para extracción de datos
                enhanced_query = f"""
Pregunta del usuario: {state['query']}

INSTRUCCIONES CRÍTICAS:
1. Primero explora las tablas disponibles con list_tables
2. Examina la estructura de las tablas relevantes con tables_schema  
3. Identifica las columnas necesarias para responder la pregunta
4. Crea la consulta SQL apropiada
5. EJECUTA la consulta usando execute_sql (NO solo la muestres)
6. Proporciona los resultados numéricos

Si la pregunta es sobre transacciones por periodo, asegúrate de:
- Encontrar la columna "periodo" (es la columna de fecha/tiempo)
- Para VALOR total: usar "valor_transacciones" 
- Para CANTIDAD total: usar "cantidad_transacciones"
- Ejemplo consulta: SELECT periodo, SUM(valor_transacciones) FROM creditcard GROUP BY periodo

IMPORTANTE: DEBES ejecutar la consulta, no solo generarla.
"""
                
                result = self.sql_agent.invoke({
                    "input": enhanced_query,
                    "chat_history": chat_history
                })
                
                output = result["output"]
                print(f"🔍 SQL Agent Output: {output}")
                
                # Si el agente no ejecutó la consulta, hacerlo directamente
                if "Necesitaría el resultado" in output or ("execute_sql" in output and "SELECT" in output):
                    print("⚡ Las herramientas SQL no funcionaron, ejecutando directamente...")
                    
                    # Extraer la consulta SQL del output del agente
                    sql_match = re.search(r'SELECT.*?;', output, re.IGNORECASE | re.DOTALL)
                    
                    if sql_match:
                        sql_query = sql_match.group(0).strip()
                        direct_result = self._execute_sql_directly(sql_query)
                        output = f"Consulta original del agente:\n{output}\n\n{direct_result}"
                    else:
                        # Intentar con un patrón más amplio
                        sql_match = re.search(r'SELECT[^;]+', output, re.IGNORECASE | re.DOTALL)
                        if sql_match:
                            sql_query = sql_match.group(0).strip() + ";"
                            direct_result = self._execute_sql_directly(sql_query)
                            output = f"Consulta original del agente:\n{output}\n\n{direct_result}"
                        else:
                            output = f"❌ No se pudo extraer consulta SQL del output:\n{output}"
                
                # Guardar en memoria
                self.memory_manager.save_interaction(
                    state['user_id'], 
                    state['query'], 
                    output
                )
                
                return {"database_result": output}
                
            except Exception as e:
                error_msg = f"❌ Error en extracción de datos: {str(e)}"
                print(f"🚨 Error SQL Agent: {e}")
                return {"database_result": error_msg}
        
        def unified_analysis_node(state: AnalysisState):
            """Nodo unificado que hace análisis y reporte en una sola llamada"""
            chat_history = self.memory_manager.get_memory(state['user_id'])
            
            result = self.unified_agent.invoke({
                "query": state['query'],
                "sql_results": state['database_result'],
                "chat_history": chat_history
            })
            
            return {"final_report": result["output"]}
        
        workflow = StateGraph(AnalysisState)
        workflow.add_node("extract_data", extract_data_node)
        workflow.add_node("unified_analysis", unified_analysis_node)
        
        workflow.set_entry_point("extract_data")
        workflow.add_edge("extract_data", "unified_analysis")
        workflow.add_edge("unified_analysis", END)
        
        return workflow.compile()
    
    async def process_message(self, message: str, user_id: str) -> dict:
        try:
            initial_state = {"query": message, "user_id": user_id}
            result = self.analysis_pipeline.invoke(initial_state)
            
            return {
                "success": True,
                "response": result["final_report"],
                "database_result": result.get("database_result", ""),
                "detailed_analysis": ""  # Ya incluido en final_report
            }
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Error procesando análisis de datos. Verifica que la base de datos esté disponible y tenga las tablas necesarias."
            }