from langchain.utilities import SerpAPIWrapper
from langchain.tools import Tool
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
import os

def create_research_agent():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    serpapi_api_key = os.getenv("SERPAPI_API_KEY")

    search = SerpAPIWrapper(serpapi_api_key=serpapi_api_key)
    search_tool = Tool(
        name="Web Search",
        func=search.run,
        description="Útil para buscar información financiera actualizada en internet."
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        openai_api_key=openai_api_key
    )

    research_agent = initialize_agent(
        [search_tool],
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    return research_agent

# if __name__ == "__main__":
#     agent = create_research_agent()
#     # Ejemplo simple para probar
#     pregunta = "¿Cuál es la situación actual del mercado bursátil?"
#     respuesta = agent.run(pregunta)
#     print("Respuesta del agente:")
#     print(respuesta)