# from langchain_core.tools import tool
# from langchain_community.tools.sql_database.tool import (
#     InfoSQLDatabaseTool,
#     ListSQLDatabaseTool,
#     QuerySQLDataBaseTool,
# )

# class SQLTools:
#     def __init__(self, db):
#         self.db = db
    
#     def get_tools(self):
#         @tool("list_tables")
#         def list_tables() -> str:
#             """List the available tables in the database"""
#             return ListSQLDatabaseTool(db=self.db).invoke("")
        
#         @tool("tables_schema")
#         def tables_schema(tables: str) -> str:
#             """Get the schema of specified tables. Input is comma-separated list of tables."""
#             return InfoSQLDatabaseTool(db=self.db).invoke(tables)
        
#         @tool("execute_sql")
#         def execute_sql(sql_query: str) -> str:
#             """Execute a SQL query against the database. Returns the result"""
#             return QuerySQLDataBaseTool(db=self.db).invoke(sql_query)
        
#         return [list_tables, tables_schema, execute_sql]

# class AnalystTools:
#     def get_tools(self):
#         @tool
#         def analyze_provided_data(data_description: str) -> str:
#             """Analiza los datos proporcionados y genera insights generales"""
#             return f"Análisis de los datos: {data_description}. Generando insights sobre patrones, tendencias y observaciones clave."
        
#         @tool
#         def generate_insights(data_context: str) -> str:
#             """Genera insights y conclusiones basados en el contexto de datos"""
#             return f"Insights generados basados en: {data_context}"
        
#         @tool
#         def get_table_statistics(table_name: str) -> str:
#             """Obtiene estadísticas descriptivas de una tabla específica"""
#             return f"Estadísticas calculadas para la tabla: {table_name}"
        
#         @tool
#         def generate_data_insights(analysis_request: str) -> str:
#             """Genera insights y conclusiones basadas en datos analizados"""
#             return f"Insights generados para: {analysis_request}"
        
#         return [analyze_provided_data, generate_insights, get_table_statistics, generate_data_insights]

# class ReportTools:
#     def get_tools(self):
#         @tool
#         def format_executive_summary(analysis_content: str) -> str:
#             """Formatea contenido de análisis en un resumen ejecutivo estructurado"""
#             formatted = f"""
#             EXECUTIVE SUMMARY
#             =================
            
#             Based on analysis: {analysis_content}
            
#             Key findings will be summarized in clear bullet points.
#             """
#             return formatted
        
#         @tool
#         def create_bullet_points(long_text: str) -> str:
#             """Convierte texto largo en puntos clave concisos"""
#             return f"• Key points extracted from: {long_text[:100]}..."
        
#         @tool
#         def generate_recommendations(analysis_data: str) -> str:
#             """Genera recomendaciones basadas en datos analizados"""
#             return f"Recommendations based on: {analysis_data}"
        
#         return [format_executive_summary, create_bullet_points, generate_recommendations]

from langchain_core.tools import tool
from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLDataBaseTool,
)

class SQLTools:
    def __init__(self, db):
        self.db = db
    
    def get_tools(self):
        @tool("list_tables")
        def list_tables() -> str:
            """List the available tables in the database"""
            return ListSQLDatabaseTool(db=self.db).invoke("")
        
        @tool("tables_schema")
        def tables_schema(tables: str) -> str:
            """Get the schema of specified tables. Input is comma-separated list of tables."""
            return InfoSQLDatabaseTool(db=self.db).invoke(tables)
        
        @tool("execute_sql")
        def execute_sql(sql_query: str) -> str:
            """Execute a SQL query against the database. Returns the result"""
            try:
                print(f"🔍 Ejecutando SQL: {sql_query}")
                
                # Usar la herramienta de LangChain
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql_query)
                
                print(f"✅ SQL ejecutado exitosamente")
                print(f"📊 Resultado: {result}")
                
                # La herramienta ya devuelve un string formateado
                return str(result)
                
            except Exception as e:
                error_msg = f"❌ Error ejecutando SQL: {str(e)}"
                print(error_msg)
                return error_msg
        
        return [list_tables, tables_schema, execute_sql]

class AnalystTools:
    def get_tools(self):
        @tool
        def analyze_provided_data(data_description: str) -> str:
            """Analiza los datos proporcionados y genera insights generales"""
            return f"Análisis de los datos: {data_description}. Generando insights sobre patrones, tendencias y observaciones clave."
        
        @tool
        def generate_insights(data_context: str) -> str:
            """Genera insights y conclusiones basados en el contexto de datos"""
            return f"Insights generados basados en: {data_context}"
        
        @tool
        def get_table_statistics(table_name: str) -> str:
            """Obtiene estadísticas descriptivas de una tabla específica"""
            return f"Estadísticas calculadas para la tabla: {table_name}"
        
        @tool
        def generate_data_insights(analysis_request: str) -> str:
            """Genera insights y conclusiones basadas en datos analizados"""
            return f"Insights generados para: {analysis_request}"
        
        return [analyze_provided_data, generate_insights, get_table_statistics, generate_data_insights]

class ReportTools:
    def get_tools(self):
        @tool
        def format_executive_summary(analysis_content: str) -> str:
            """Formatea contenido de análisis en un resumen ejecutivo estructurado"""
            formatted = f"""
            EXECUTIVE SUMMARY
            =================
            
            Based on analysis: {analysis_content}
            
            Key findings will be summarized in clear bullet points.
            """
            return formatted
        
        @tool
        def create_bullet_points(long_text: str) -> str:
            """Convierte texto largo en puntos clave concisos"""
            return f"• Key points extracted from: {long_text[:100]}..."
        
        @tool
        def generate_recommendations(analysis_data: str) -> str:
            """Genera recomendaciones basadas en datos analizados"""
            return f"Recommendations based on: {analysis_data}"
        
        return [format_executive_summary, create_bullet_points, generate_recommendations]