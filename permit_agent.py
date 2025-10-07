import json
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from langgraph.graph.state import CompiledStateGraph

# document indexing
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage
from typing import Annotated
import operator

from permit_agent_data_models import PermitInfo


NUM_CHUNKS_TO_RETRIEVE = 3
RETRIEVAL_MODEL = "gpt-4o-mini"

retrieval_llm = ChatOpenAI(model=RETRIEVAL_MODEL, temperature=0.0)


class PermitAgentState(AgentState):
    notes: Annotated[list[str], operator.add]  # partially extracted information
    permit_info: PermitInfo
    permit_json_path: str


def index_document(document_path: str) -> FAISS:
    """Index document contents into a in-memory vector store for search

    document_path (str): path to PDF document containing info needed for permit
    """
    loader = PyPDFLoader(document_path)
    docs = loader.load()

    # merge pages into a single document, o/w chunk overlaps won't be across page boundaries
    full_text = "\n".join([doc.page_content for doc in docs])

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    chunks = text_splitter.split_documents([Document(page_content=full_text)])

    vector_store = FAISS.from_documents(chunks, OpenAIEmbeddings())

    return vector_store


def create_permit_info_extraction_agent(
    model: str, document_path: str
) -> CompiledStateGraph:
    """Factory function for permit info extraction agent.

    Args:
    model (str): OpenAI model name
    document_path (str): path to PDF document containing info needed for permit
    """

    vector_store = index_document(document_path)

    @tool
    def file_search(
        query: str, tool_call_id: Annotated[str, InjectedToolCallId]
    ) -> Command:
        """Search documents provided about the solar project of interest.

        query: should be detailed enough for extracting the field of interest
        """

        prompt_template = """Extract information about {query} from the text below:

        {retrieved_content}
        """

        # retrieve relevant document chunks
        relevant_chunks = vector_store.similarity_search(
            query, k=NUM_CHUNKS_TO_RETRIEVE
        )

        chain = (
            ChatPromptTemplate.from_template(prompt_template)
            | retrieval_llm
            | StrOutputParser()
        )
        result = chain.invoke(
            {
                "query": query,
                "retrieved_content": "\n\n".join(
                    [c.page_content for c in relevant_chunks]
                ),
            }
        )

        # use Command to update state:
        # - notes with result
        # - a ToolMessage is expected
        return Command(
            update={
                "notes": [f"{query}: {result}"],
                "messages": [ToolMessage(f"result", tool_call_id=tool_call_id)],
            }
        )

    # react agent with document search
    SYSTEM_MESSAGE = (
        "You are a solar project permitting assistant."
        " You have access to documents about a project using the file search tool."
        " Extract information needed to fill out a permit, as defined by the permit schema."
        " When using the file search tool, be specific about any options the desired answer may take on."
    )
    agent = create_react_agent(
        model=ChatOpenAI(model=RETRIEVAL_MODEL, temperature=0.0),
        tools=[file_search],
        prompt=SYSTEM_MESSAGE,
        state_schema=PermitAgentState,
    )
    agent = agent.with_config({"recursion_limit": 50})  # TODO revisit recursion limit

    return agent


def create_permit_agent(model: str, document_path: str) -> CompiledStateGraph:
    """Factory function for permit agent

    Args:
    model (str): OpenAI model name
    document_path (str): path to PDF document containing info needed for permit
    """

    permit_info_extraction_agent = create_permit_info_extraction_agent(
        model=model, document_path=document_path
    )

    # nodes
    def extract_permit_info(state: PermitAgentState):
        user_msg = f"Here is the permit schema you must fill in from the available documents: {PermitInfo.model_json_schema()}"

        result = permit_info_extraction_agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": user_msg,
                    }
                ],
            }
        )

        # extract structured output
        notes = "\n\n".join(result["notes"])

        llm = ChatOpenAI(model=model, temperature=0.0).with_structured_output(
            PermitInfo
        )
        permit_info_extracted = llm.invoke([HumanMessage(notes)])

        return {"permit_info": permit_info_extracted}

    def create_json(state: PermitAgentState):
        json_data = json.loads(state["permit_info"].model_dump_json())

        timestamp = datetime.now().strftime("%Y%d%m_%H%M%S")
        json_fpath = f"permit_info_{timestamp}.json"

        try:
            with open(json_fpath, "w") as f:
                json.dump(json_data, f, indent=4)
            return {"permit_json_path": json_fpath}
        except:
            print("could not write json file")
            return {"permit_json_path": ""}

    # graph
    permit_agent_builder = StateGraph(PermitAgentState)
    permit_agent_builder.add_node("extract_permit_info", extract_permit_info)
    permit_agent_builder.add_node("create_json", create_json)

    permit_agent_builder.add_edge(START, "extract_permit_info")
    permit_agent_builder.add_edge("extract_permit_info", "create_json")
    permit_agent_builder.add_edge("create_json", END)

    permit_agent_graph = permit_agent_builder.compile()

    return permit_agent_graph
