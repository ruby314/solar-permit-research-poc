from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph.state import CompiledStateGraph


def create_research_agent(model: str) -> CompiledStateGraph:
    """Factory function for research agent

    Args:
    model (str): OpenAI model name
    """

    SYSTEM_PROMPT = (
        "You are a helpful research agent with expertise in mid size community solar installations."
        " You are able to search government domain websites and local news."
        " Create a summary of how favorable a location would be for a new community solar project. "
        " Include the following: a summary of local policy and regulations, any moratoriums, environmental restrictions, and news headlines impacting the search."
        " Include references inline."
    )

    model = ChatOpenAI(model=model, temperature=0.0)

    # search tool
    gov_domain_search_tool = TavilySearch(
        max_results=5,
        topic="general",
        include_domains=["*.gov"],
    )
    tools = [gov_domain_search_tool]

    # react agent
    agent = create_react_agent(
        model,
        tools,
        prompt=SYSTEM_PROMPT,
    ).with_config({"recursion_limit": 0})

    return agent
