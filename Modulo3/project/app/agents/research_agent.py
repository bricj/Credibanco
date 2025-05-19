import os
from textwrap import dedent
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.utilities import SerpAPIWrapper

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
        model="gpt-4o",
        temperature=0.2,
        openai_api_key=openai_api_key
    )

    system_prompt = dedent("""\
        You are an elite research analyst in the financial services domain.
        Your expertise encompasses:

        - Deep investigative financial research and analysis
        - fact-checking and source verification
        - Data-driven reporting and visualization
        - Expert interview synthesis
        - Trend analysis and future predictions
        - Complex topic simplification
        - Ethical practices
        - Balanced perspective presentation
        - Global context integration
    """)

    instructions = dedent("""\
        1. Research Phase
           - Search for 5 authoritative sources on the topic
           - Prioritize recent publications and expert opinions
           - Identify key stakeholders and perspectives

        2. Analysis Phase
           - Extract and verify critical information
           - Cross-reference facts across multiple sources
           - Identify emerging patterns and trends
           - Evaluate conflicting viewpoints

        3. Writing Phase
           - Craft an attention-grabbing headline
           - Structure content in Financial Report style
           - Include relevant quotes and statistics
           - Maintain objectivity and balance
           - Explain complex concepts clearly

        4. Quality Control
           - Verify all facts and attributions
           - Ensure narrative flow and readability
           - Add context where necessary
           - Include future implications
    """)

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    expected_output = dedent(f"""\
        # {{Compelling Headline}}

        ## Executive Summary
        {{Concise overview of key findings and significance}}

        ## Background & Context
        {{Historical context and importance}}
        {{Current landscape overview}}

        ## Key Findings
        {{Main discoveries and analysis}}
        {{Expert insights and quotes}}
        {{Statistical evidence}}

        ## Impact Analysis
        {{Current implications}}
        {{Stakeholder perspectives}}
        {{Industry/societal effects}}

        ## Future Outlook
        {{Emerging trends}}
        {{Expert predictions}}
        {{Potential challenges and opportunities}}

        ## Expert Insights
        {{Notable quotes and analysis from industry leaders}}
        {{Contrasting viewpoints}}

        ## Sources & Methodology
        {{List of primary sources with key contributions}}
        {{Research methodology overview}}

        ---
        Research conducted by Financial Agent  
        Credit Rating Style Report  
        Published: {current_date}  
        Last Updated: {current_time}
    """)

    full_prompt = f"""{system_prompt}

Instructions:
{instructions}

Respond using the following format:
{expected_output}
"""

    agent = initialize_agent(
        [search_tool],
        llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_kwargs={
            "system_message": full_prompt
        }
    )

    return agent

