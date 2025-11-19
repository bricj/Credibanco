import logging
import re
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .tools import SQLTools
from .memory import ConversationMemoryManager

logger = logging.getLogger(__name__)

class SQLAgentSystem:
    """Sistema de agente SQL especializado extraído del core original"""
    
    def __init__(self, database_url: str, llm: ChatGoogleGenerativeAI, memory_manager: ConversationMemoryManager):
        self.llm = llm
        self.db = SQLDatabase.from_uri(database_url)
        self.memory_manager = memory_manager
        
        # Obtener contexto de la base de datos
        self.database_context = self._get_database_context()
        
        # Inicializar herramientas SQL
        self.sql_tools = SQLTools(self.db)
        
        # Crear agente SQL
        self.sql_agent = self._create_sql_agent()
        self.unified_agent = self._create_unified_agent()
    
    def _get_database_context(self):
        """Obtiene información sobre la estructura de la base de datos"""
        try:
            tables_info = self.db.get_table_info()
            
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
        """Crear agente SQL especializado"""
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
    
    def _clean_sql_query(self, sql_text: str) -> str:
        """Limpiar consulta SQL de markdown y formatting"""
        print(f"🧹 Limpiando query: {sql_text[:100]}...")
        
        # Remover markdown code blocks
        sql_text = re.sub(r'```sql\s*', '', sql_text, flags=re.IGNORECASE)
        sql_text = re.sub(r'```\s*', '', sql_text)
        
        # Remover texto explicativo con asteriscos
        sql_text = re.sub(r'\*\*.*?\*\*', '', sql_text)
        
        # Remover números de sección y texto explicativo
        sql_text = re.sub(r'\d+\.\s*[^:]*:\s*', '', sql_text)
        
        # Extraer solo la consulta SELECT (primera ocurrencia limpia)
        select_patterns = [
            r'(SELECT[^;]*?(?:ORDER BY[^;]*?)?);',  # SELECT con ORDER BY y semicolon
            r'(SELECT[^;]*?ORDER BY[^`\n]*)',       # SELECT con ORDER BY sin semicolon
            r'(SELECT[^;`\n]*FROM[^;`\n]*)',        # SELECT básico
        ]
        
        cleaned_query = None
        for pattern in select_patterns:
            select_match = re.search(pattern, sql_text, re.IGNORECASE | re.DOTALL)
            if select_match:
                cleaned_query = select_match.group(1)
                break
        
        if not cleaned_query:
            # Fallback: buscar cualquier SELECT
            select_match = re.search(r'(SELECT.*?)(?=\n\n|\Z|```)', sql_text, re.IGNORECASE | re.DOTALL)
            if select_match:
                cleaned_query = select_match.group(1)
            else:
                cleaned_query = sql_text
        
        # Limpiar espacios y saltos de línea múltiples
        cleaned_query = ' '.join(cleaned_query.split())
        
        # Asegurar que termine en punto y coma
        if not cleaned_query.strip().endswith(';'):
            cleaned_query = cleaned_query.strip() + ';'
        
        print(f"✨ Query limpia: {cleaned_query}")
        return cleaned_query.strip()
    
    def _execute_sql_directly(self, sql_query: str):
        """Ejecuta una consulta SQL directamente cuando las herramientas fallan"""
        try:
            # Limpiar query de markdown y formatting
            cleaned_query = self._clean_sql_query(sql_query)
            print(f"🔍 Ejecutando consulta limpia: {cleaned_query}")
            
            try:
                result_str = self.db.run(cleaned_query)
                print(f"✅ Consulta ejecutada con db.run()")
                print(f"📊 Resultado: {result_str}")
                return f"✅ Resultado de la consulta:\n{result_str}"
                
            except Exception as e1:
                print(f"⚠️ db.run() falló: {e1}")
                try:
                    result = self.db._execute(cleaned_query)
                    
                    if hasattr(result, 'fetchall'):
                        rows = result.fetchall()
                        columns = [desc[0] for desc in result.description] if result.description else []
                    else:
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
    
    def process_sql_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """Procesar consulta SQL completa"""
        try:
            # Obtener memoria del usuario
            chat_history = self.memory_manager.get_memory(user_id)
            
            # Prompt específico para extracción de datos
            enhanced_query = f"""
Pregunta del usuario: {query}

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
            
            # Ejecutar agente SQL
            result = self.sql_agent.invoke({
                "input": enhanced_query,
                "chat_history": chat_history
            })
            
            output = result["output"]
            print(f"🔍 SQL Agent Output: {output}")
            
            # Si el agente no ejecutó la consulta, hacerlo directamente
            if "Necesitaría el resultado" in output or ("execute_sql" in output and "SELECT" in output) or "```sql" in output:
                print("⚡ Las herramientas SQL no funcionaron, ejecutando directamente...")
                
                # Intentar múltiples patrones de extracción
                sql_patterns = [
                    r'```sql\s*(SELECT[^`]*?)```',  # Markdown code block
                    r'(SELECT[^;]*?;)',             # SELECT con semicolon
                    r'(SELECT[^`\n]*FROM[^`\n]*)',  # SELECT básico hasta FROM
                ]
                
                sql_query = None
                for pattern in sql_patterns:
                    sql_match = re.search(pattern, output, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql_query = sql_match.group(1).strip()
                        break
                
                if sql_query:
                    print(f"🔍 Query extraída: {sql_query[:100]}...")
                    direct_result = self._execute_sql_directly(sql_query)
                    output = f"Consulta original del agente:\n{output}\n\n{direct_result}"
                else:
                    # Buscar cualquier SELECT como último recurso
                    fallback_match = re.search(r'(SELECT[^;]*)', output, re.IGNORECASE | re.DOTALL)
                    if fallback_match:
                        sql_query = fallback_match.group(1).strip()
                        print(f"🔍 Fallback query: {sql_query[:100]}...")
                        direct_result = self._execute_sql_directly(sql_query)
                        output = f"Consulta original del agente:\n{output}\n\n{direct_result}"
                    else:
                        output = f"❌ No se pudo extraer consulta SQL del output:\n{output}"
            
            # Generar respuesta final
            final_result = self.unified_agent.invoke({
                "query": query,
                "sql_results": output,
                "chat_history": chat_history
            })
            
            # Guardar en memoria
            self.memory_manager.save_interaction(user_id, query, final_result["output"])
            
            return {
                "success": True,
                "response": final_result["output"],
                "sql_raw_result": output,
                "query_type": "sql"
            }
            
        except Exception as e:
            logger.error(f"Error processing SQL query: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Error procesando consulta SQL. Verifica que la base de datos esté disponible.",
                "query_type": "sql"
            }