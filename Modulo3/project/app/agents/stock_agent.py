import os
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI

def create_stock_agent():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    serpapi_api_key = os.getenv("SERPAPI_API_KEY")

    if not openai_api_key or not serpapi_api_key:
        raise ValueError("OPENAI_API_KEY o SERPAPI_API_KEY no están definidos en el entorno")

    llm = ChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo",
        openai_api_key=openai_api_key
    )

    tools = load_tools(["serpapi"], llm=llm)

    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    return agent

# if __name__ == "__main__":
#     agent = create_stock_agent()
#     pregunta = "¿Qué está pasando hoy con las acciones de Nvidia?"
#     respuesta = agent.run(pregunta)
#     print("\n📊 Respuesta del agente:")
#     print(respuesta)
