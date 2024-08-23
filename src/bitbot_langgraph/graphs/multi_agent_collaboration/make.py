import operator
import functools
from datetime import datetime
from typing import Annotated, List, Tuple, TypedDict, Literal, Union, Optional, Sequence
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    AIMessage
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)


# tools
from bitbot_langgraph.tools.search_sample import search
from bitbot_langgraph.tools.python_repl import python_repl


# from langchain_community.tools import DuckDuckGoSearchRun, ShellTool, WikipediaQueryRun
# from langchain_community.agent_toolkits import FileManagementToolkit
# from langchain.agents import load_tools

from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun

# # Setup working directory
# working_directory = "/app/docs_root"
# file_toolkit = FileManagementToolkit(root_dir=working_directory)
# file_tools = file_toolkit.get_tools()



duckduckgo_tool = DuckDuckGoSearchRun()
wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# shell_tool = ShellTool()
# input_tool = InputTool()
# directory_read_tool = DirectoryReadTool()
# directory_search_tool = DirectorySearchTool()
# code_interpreter_tool = CodeInterpreterTool()
# file_read_tool = FileReadTool()
# pdf_search_tool = PDFSearchTool()
# txt_search_tool = TXTSearchTool()
# csv_search_tool = CSVSearchTool()
# xml_search_tool = XMLSearchTool()
# json_search_tool = JSONSearchTool()
# file_append_tool = FileAppendTool()



def create_agent(llm, tools, system_message, logger=None):
    """Create an agent."""

    logger = logger or logging.getLogger(__name__)

    logger.info(f"create_agent: {llm}")
    logger.info(f"  tools: {tools}")

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK, another assistant with different tools "
                " will help where you left off. Execute what you can to make progress."
                " If you or any of the other assistants have the final answer or deliverable,"
                " prefix your response with FINAL ANSWER so the team knows to stop."
                "If you have enough data to build a graph,"
                " prefix your response with BUILDGRAPH so the graph builder can be selected"
                " You have access to the following tools: {tool_names}.\n{system_message}",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt.partial(system_message=system_message)
    prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
    return prompt | llm.bind_tools(tools)



def make_graph(logger=None):
    # set up logging
    logger = logger or logging.getLogger(__name__)
    logger.info("make_graph")


    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)

    # define the state
    # This defines the object that is passed between each node
    # in the graph. We will create different nodes for each agent and tool
    class State(TypedDict):
        messages: Annotated[Sequence[BaseMessage], operator.add]
        sender: str

    # Helper function to create a node for a given agent
    def agent_node(state, agent, name):
        result = agent.invoke(state)
        # We convert the agent output into a format that is suitable to append to the global state
        if isinstance(result, ToolMessage):
            pass
        else:
            result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)

        response = {
            "messages": [result],
            # Since we have a strict workflow, we can
            # track the sender so we know who to pass to next.
            "sender": name,
        }
        logger.info(f"agent_node response: {response}")
        return response

    researcher_tools = [duckduckgo_tool, wikipedia_tool]
    researcher_system_message = "You should provide accurate data for the chart_generator to use. do not use any additonal tools if you have enough data for the chart_generator"
    research_agent = create_agent(
        model,
        researcher_tools,
        system_message=researcher_system_message,
        logger=logger, 
    )
    research_node = functools.partial(agent_node, agent=research_agent, name="researcher")
    tool_node_researcher = ToolNode(researcher_tools)

    charter_tools = [python_repl]
    charter_system_message = "Any charts you display will be visible to the user"
    chart_agent = create_agent(
        model,
        charter_tools,
        system_message=charter_system_message
    )
    chart_node = functools.partial(agent_node, agent=chart_agent, name="chart_generator")
    tool_node_chart = ToolNode([python_repl])

    # router
    def router(state) -> Literal["researcher", "chart_generator", "call_tool_charter", "call_tool_researcher", "__end__"]:
        messages = state["messages"]
        last_message = messages[-1]

        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("------")
        logger.info("------")
        logger.info("------")
        logger.info("------")
        logger.info("------")
        # logger.info(f"in router: {state}")
        logger.info("in router")
        logger.info(f"  last_message: {last_message}")

        # if tool calls in the last message, go back to sender
        # if no tool call in the last message, switch to other sender
        sender = state.get("sender")
        logger.info(f"sender according to state: {sender}")
        
        # if last_message instance of ToolMessage
        if isinstance(last_message, ToolMessage):
            logger.info(f"last message is tool message - sender: {sender}")
            if sender == "researcher":
                return "chart_generator"
            if sender == "chart_generator":
                return "researcher"

        last_message_tool_calls = last_message.tool_calls
        if last_message_tool_calls:
            logger.info(f"last_message_tool_calls - sender: {sender}")
            if sender == "researcher":
                return "call_tool_researcher"
            if sender == "chart_generator":
                return "call_tool_charter"
        else:
            logger.info("last message did not have tool_calls")

        if "BUILDGRAPH" in last_message.content:
            logger.info("neeed to build the graph")
            return "chart_generator"

        if "FINAL ANSWER" in last_message.content:
            logger.info("final answer")
            return "__end__"
        
        
        # if not dealing with a tool, switch to other sender
        logger.info(f"not final answer: {sender}")
        if sender == "researcher":
            return "chart_generator"
        if sender == "chart_generator":
            return "researcher"
        
        return "researcher"
        
    
    # Define the workflow
    workflow = StateGraph(State)

    # add_node - add nodes to the workflow
    workflow.add_node("researcher", research_node)
    workflow.add_node("chart_generator", chart_node)
    workflow.add_node("call_tool_charter", tool_node_chart)
    workflow.add_node("call_tool_researcher", tool_node_researcher)

    

    # add_edge - add edges to the workflow
    workflow.add_edge(START, "researcher")
    

    # add_conditional_edge - add conditional edges to the workflow
    workflow.add_conditional_edges(
        "researcher",
        router
    )
    
    workflow.add_conditional_edges(
        "chart_generator",
        router
    )

    workflow.add_conditional_edges("call_tool_charter",router)
    workflow.add_edge("chart_generator", "call_tool_charter")

    workflow.add_conditional_edges("call_tool_researcher", router)
    workflow.add_edge("researcher", "call_tool_researcher")



    # compile the app
    app = workflow.compile()
    return app