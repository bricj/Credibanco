import logging
from typing import Dict, Any, TypedDict
from langchain_openai import ChatOpenAI
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
    detailed_analysis: str
    markdown_report: str
    user_id: str

class MultiAgentSQLSystem:
    def __init__(self, database_url: str, model_name: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(model_name=model_name, temperature=0.0)
        self.db = SQLDatabase.from_uri(database_url)
        
        # Inicializar herramientas
        self.sql_tools = SQLTools(self.db)
        self.analyst_tools = AnalystTools()
        self.report_tools = ReportTools()
        
        # Inicializar memoria
        self.memory_manager = ConversationMemoryManager()
        
        # Crear agentes
        self.sql_agent = self._create_sql_agent()
        self.analyst_agent = self._create_analyst_agent()
        self.report_agent = self._create_report_agent()
        
        # Crear pipeline
        self.analysis_pipeline = self._create_pipeline()
    
    def _create_sql_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an experienced database engineer who is master at creating efficient and complex SQL queries.
                You have a deep understanding of how different databases work and how to optimize queries.
                Use the `list_tables` to find available tables.
                Use the `tables_schema` to understand the metadata for the tables.
                Use the `execute_sql` to check your queries for correctness."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.sql_tools.get_tools(), prompt)
        return AgentExecutor(agent=agent, tools=self.sql_tools.get_tools(), verbose=True)
    
    def _create_analyst_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You have deep experience with analyzing datasets using Python.
                Your work is always based on the provided data and is clear,
                easy-to-understand and to the point. You have attention
                to detail and always produce very detailed work."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.analyst_tools.get_tools(), prompt)
        return AgentExecutor(agent=agent, tools=self.analyst_tools.get_tools(), verbose=True)
    
    def _create_report_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Your writing style is well known for clear and effective communication.
                You always summarize long texts into bullet points that contain the most
                important details. Your goal: Write executive summary type reports based on analyst work.
                Always structure your reports with:
                - Clear executive summary
                - Key findings in bullet points
                - Actionable recommendations"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_openai_tools_agent(self.llm, self.report_tools.get_tools(), prompt)
        return AgentExecutor(agent=agent, tools=self.report_tools.get_tools(), verbose=True)
    
    def _create_pipeline(self):
        def extract_data_node(state: AnalysisState):
            # Obtener memoria del usuario
            chat_history = self.memory_manager.get_memory(state['user_id'])
            
            result = self.sql_agent.invoke({
                "input": f"Extract data that is required for the query: {state['query']}",
                "chat_history": chat_history
            })
            
            # Guardar en memoria
            self.memory_manager.save_interaction(
                state['user_id'], 
                state['query'], 
                result["output"]
            )
            
            return {"database_result": result["output"]}
        
        def analyze_data_node(state: AnalysisState):
            chat_history = self.memory_manager.get_memory(state['user_id'])
            
            result = self.analyst_agent.invoke({
                "input": f"Analyze the data from the database and write an analysis for {state['query']}. Database data: {state['database_result']}",
                "chat_history": chat_history
            })
            return {"detailed_analysis": result["output"]}
        
        def write_report_node(state: AnalysisState):
            chat_history = self.memory_manager.get_memory(state['user_id'])
            
            result = self.report_agent.invoke({
                "input": f"Write an executive summary report. Analysis: {state['detailed_analysis']}",
                "chat_history": chat_history
            })
            return {"markdown_report": result["output"]}
        
        workflow = StateGraph(AnalysisState)
        workflow.add_node("extract_data", extract_data_node)
        workflow.add_node("analyze_data", analyze_data_node)
        workflow.add_node("write_report", write_report_node)
        
        workflow.set_entry_point("extract_data")
        workflow.add_edge("extract_data", "analyze_data")
        workflow.add_edge("analyze_data", "write_report")
        workflow.add_edge("write_report", END)
        
        return workflow.compile()
    
    async def process_message(self, message: str, user_id: str) -> dict:
        try:
            initial_state = {"query": message, "user_id": user_id}
            result = self.analysis_pipeline.invoke(initial_state)
            
            return {
                "success": True,
                "response": result["markdown_report"],
                "database_result": result.get("database_result", ""),
                "detailed_analysis": result.get("detailed_analysis", "")
            }
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Error procesando análisis de datos."
            }