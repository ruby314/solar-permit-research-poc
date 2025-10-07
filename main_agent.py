import json
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from research_agent import create_research_agent
from permit_agent import create_permit_agent
from permit_agent_data_models import Address, PermitInfo

MAIN_AGENT_MODEL = "gpt-4o-mini"
RESEARCH_AGENT_MODEL = "gpt-4o-mini"
PERMIT_AGENT_MODEL = "gpt-4o-mini"


class MainAgentState(MessagesState):
    user_input: str
    project_address: Address
    research_result: str
    permit_info: PermitInfo
    permit_json_path: str
    final: str  # dummy placeholder for now


def create_main_agent(document_path: str) -> CompiledStateGraph:
    """Factory function for creating main agent

    Args:
    document_path (str): path to PDF containing permit info
    """
    research_agent = create_research_agent(model=RESEARCH_AGENT_MODEL)
    permit_agent = create_permit_agent(
        model=PERMIT_AGENT_MODEL, document_path=document_path
    )

    ### nodes
    # all nodes return updates to MainAgentState
    def parse_address(state: MainAgentState):

        llm = ChatOpenAI(
            model=MAIN_AGENT_MODEL, temperature=0.0
        ).with_structured_output(Address)
        address = llm.invoke(state["user_input"])
        # TODO error checking

        return {"project_address": address}

    def research_location(state: MainAgentState):
        # input location "city, state"
        address_dict = json.loads(state["project_address"].model_dump_json())
        location = f"{address_dict['city']}, {address_dict['state']}"
        result = research_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": location,
                    }
                ],
            }
        )

        return {"research_result": result["messages"][-1].content}

    def fill_in_permit_info(state: MainAgentState):
        result = permit_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "",
                    }
                ],
            }
        )
        return result

    def final_analysis(state: MainAgentState):
        # just pass through, dummy node for now
        return {"final": state["research_result"]}

    # main agent graph
    builder = StateGraph(MainAgentState)
    builder.add_node("parse_address", parse_address)
    builder.add_node("research_location", research_location)
    builder.add_node("fill_in_permit_info", fill_in_permit_info)
    builder.add_node("final_analysis", final_analysis)

    builder.add_edge(START, "parse_address")
    builder.add_edge("parse_address", "research_location")
    builder.add_edge("parse_address", "fill_in_permit_info")
    builder.add_edge("research_location", "final_analysis")
    builder.add_edge("fill_in_permit_info", "final_analysis")
    builder.add_edge("final_analysis", END)

    main_agent_graph = builder.compile()

    return main_agent_graph
