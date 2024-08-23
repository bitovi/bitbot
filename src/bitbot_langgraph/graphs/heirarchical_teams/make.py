import os
import operator
import functools
from pathlib import Path
from datetime import datetime
from typing import Annotated, List, TypedDict, Dict

from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    AIMessage
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

# load utilities
from bitbot_langgraph.graphs.heirarchical_teams.utilities import create_agent, agent_node, create_team_supervisor

# tools
from bitbot_langgraph.tools.search_sample import search
from bitbot_langgraph.tools.python_repl import python_repl
from bitbot_langgraph.tools.file_tools import create_outline, read_document, write_document, edit_document
from bitbot_langgraph.tools.scrape_webpages import scrape_webpages

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



# [{"url": url, "title": title, "description": description, "content": content}]
class ResearchItem(BaseModel):
    url: str
    title: str
    description: str
    content: str

class ResearchItems(BaseModel):
    items: list[ResearchItem]

# research_items_converter prompt
research_items_converter_prompt = """
For the given message, return a list of research items.
Here is the message:
{messages}
"""

# research message converter
# essentially returns a callable LLM with a built-in prompt
def make_research_message_converter(prompt_str=research_items_converter_prompt):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                prompt_str
            ),
            ("placeholder", "{messages}"),
        ]
    )
    return prompt | ChatOpenAI(
        model="gpt-4o", temperature=0
    ).with_structured_output(ResearchItems)


# make lesson message converter
class Lesson(BaseModel):
    title: str
    content: str
    
lesson_structure = """
# Lesson: [title. example: OOPs! Introduction to the Order of Operations in mathematics]

**Duration:** [duration. example: 30 minutes]

---

# Objective:
[objective. example: Understand and apply the order of precedence for mathematical operators in expressions.]

---

# Materials Needed:
- [list of materials needed. example: Whiteboard, chalkboard, or paper]
- [additional materials. example: Calculator (optional, for checking answers)]

---

# Lesson Outline:
1. **[Introduction to Topic]** ([time duration. example: 5 minutes])
2. **[Key Concept or Rule Introduction]** ([time duration. example: 10 minutes])
[...etc...]

## 1. [Introduction to Topic] ([time duration. example: 5 minutes])

### [Subtopic 1 - Definition or Concept Introduction]
[paragraph explaining the first subtopic. example: Operators are symbols that represent mathematical operations such as addition (+), subtraction (-), multiplication (×), division (÷), and exponentiation (^).]

[additional paragraphs or explanations related to the first subtopic.]

### [Subtopic 2 - Importance or Application]
[paragraph explaining the importance or application of the topic. example: The order in which operations are performed significantly affects the outcome of mathematical expressions.]

[additional paragraphs or explanations related to the importance or application.]

## 2. [Key Concept or Rule Introduction] ([time duration. example: 10 minutes])

### [Subtopic 1 - Specific Rule or Principle]
[paragraph introducing the specific rule or principle. example: In mathematics, not all operations are treated equally; some must be performed before others according to specific rules.]

[additional paragraphs or explanations related to the specific rule or principle.]

### 1. [First Element of the Rule or Principle]
[explanation of the first element. example: Parentheses are used to group parts of an expression that should be evaluated first.]

#### Examples:
- [Example 1]
- [Example 2]
[...additional examples as needed...]

### 2. [Next Element of the Rule or Principle]
[explanation of the next element. example: Exponents are calculated after parentheses and before multiplication, division, addition, or subtraction.]

[...continue with other elements...]

## [Next Major Section...]
[Continue outlining the rest of the lesson in a similar format.]

---

# Conclusion:
[summary of the lesson. example: now you know...]
"""

lesson_converter_prompt = """
For the given messages & research items, Output a lesson in markdown format.
The lesson should focus on a homeschool environment in which there are only a couple of children (siblings) of different ages.
Do not suggest breaking up in groups. be thorough when providing examples.  Provide at least 3 more than you think you should.
Here are the messages:
{messages}

Here are the research items:
{research_items}

The lesson should be structured as follows:
{lesson_structure}
"""
def make_lesson_message_converter(prompt_str=lesson_converter_prompt):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                prompt_str
            ),
            ("placeholder", "{messages}"),
            ("placeholder", "{research_items}"),
            ("placeholder", "{lesson_structure}"),
        ]
    )
    return prompt | ChatOpenAI(
        model="gpt-4o", temperature=0
    ).with_structured_output(Lesson)

def make_research_team_graph(logger=None):
    # set up logging
    logger = logger or logging.getLogger(__name__)
    logger.info("make_research_team_graph")

    # define the state
    class State(TypedDict):
        # A message is added after each team member finishes
        messages: Annotated[list[BaseMessage], operator.add]

        # The team members are tracked so they are aware of
        # the others' skill-sets        
        team_members: List[str]

        # Used to route work. The supervisor calls a function
        # that will update this every time it makes a decision
        next: str

        research_items: Annotated[ResearchItems, operator.add]

        lesson: Lesson
        





    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # make agents
    search_agent = create_agent(
        llm,
        [duckduckgo_tool, wikipedia_tool],
        "You are a research assistant who can search for up-to-date info using a variety of search tools"
        " such as DuckDuckGo and Wikipedia. Use the search tool to find relevant information for the lesson."
        " Never suggest handouts or worksheets unless it's accompanyied by a link to a printable version."
    )
    search_node = functools.partial(agent_node, agent=search_agent, name="Search")


    # make this agent return a list of research
    # example:
    # [{"url": url, "title": title, "description": description, "content": content}]
    search_message_converter = make_research_message_converter()
    def convert_search_message_to_research_item(state: State):
        last_message = state["messages"][-1]
        output = search_message_converter.invoke({
            "messages": [last_message]
        })
        return {"research_items": output.items}
    
    research_message_converter = make_research_message_converter()
    def convert_research_message_to_research_item(state: State):
        last_message = state["messages"][-1]
        output = research_message_converter.invoke({
            "messages": [last_message]
        })
        return {"research_items": output.items}



    research_agent = create_agent(
        llm,
        [scrape_webpages],
        "You are a research assistant who can scrape specified urls for more detailed information using the scrape_webpages function.",
    )
    research_node = functools.partial(agent_node, agent=research_agent, name="WebScraper")

    lesson_converter = make_lesson_message_converter()
    def convert_lesson_message(state: State):
        # convert research_items to messages
        research_items = state["research_items"]

        research_items_messages = []
        if research_items and len(research_items) > 0:
            for item in research_items:
                research_items_messages.append(HumanMessage(content=f"Title: {item.title}\nDescription: {item.description}\nContent: {item.content}"))

        lesson = lesson_converter.invoke({
            "messages": state["messages"],
            "research_items": research_items_messages
        })
        return {
            "lesson": lesson
        }



    supervisor_agent = create_team_supervisor(
        llm,
        "You are a supervisor tasked with managing a conversation between the"
        " following workers:  Search, WebScraper. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH.",
        ["Search", "WebScraper"],
    )
    # Define the workflow
    workflow = StateGraph(State)

    # add_node - add nodes to the workflow
    workflow.add_node("Search", search_node)
    workflow.add_node("WebScraper", research_node)
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("convert_search_message_to_research_item", convert_search_message_to_research_item)
    workflow.add_node("convert_research_message_to_research_item", convert_research_message_to_research_item)
    workflow.add_node("convert_lesson_message", convert_lesson_message)

    

    # add_edge - add edges to the workflow
    workflow.add_edge("Search", "convert_search_message_to_research_item")
    workflow.add_edge("convert_search_message_to_research_item", "supervisor")
    workflow.add_edge("WebScraper", "convert_research_message_to_research_item")
    workflow.add_edge("convert_research_message_to_research_item", "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {"Search": "Search", "WebScraper": "WebScraper", "FINISH": "convert_lesson_message"},
    )

    workflow.add_edge("convert_lesson_message", END)


    workflow.add_edge(START, "supervisor")
    chain = workflow.compile()

    # The following functions interoperate between the top level graph state
    # and the state of the research sub-graph
    # this makes it so that the states of each graph don't get intermixed
    def enter_chain(message: str):
        logger.info(f"enter_chain: {message}")
        results = {
            "messages": [HumanMessage(content=message)],
        }
        return results


    # return chain
    research_chain = enter_chain | chain
    return research_chain


def make_document_review_team_graph(logger=None):
    # set up logging
    logger = logger or logging.getLogger(__name__)
    logger.info("make_document_review_team_graph")

    # define the state
    class State(TypedDict):
        # This tracks the team's conversation internally
        messages: Annotated[List[BaseMessage], operator.add]
        # This provides each worker with context on the others' skill sets
        team_members: str
        # This is how the supervisor tells langgraph who to work next
        next: str

        lesson: Lesson

        lesson_title: str
        lesson_content: str

        review_count: int

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # make agents
    content_reviewer_agent = create_agent(
        llm,
        [read_document],
        "You are a content reviewer tasked with ensuring that the lesson is complete and suitable for a child to learn from."
        " The document should be a fully usable lesson without the need for additional research."
        " If the content is inadequate, provide feedback for revisions."
        "This is the content you will be reviewing:"
        "title: {lesson_title}\n{lesson_content}"
    )
    content_reviewer_node = functools.partial(agent_node, agent=content_reviewer_agent, name="ContentReviewer")

    child_comprehension_specialist_agent = create_agent(
        llm,
        [read_document],
        "You are a child comprehension specialist ensuring that the language and structure of the lesson are appropriate for a child to understand."
        " The document should be engaging and educationally sound for the target age group."
        "This is the content you will be reviewing:"
        "\nTitle: {lesson_title}\n{lesson_content}"
    )
    child_comprehension_specialist_node = functools.partial(
        agent_node, agent=child_comprehension_specialist_agent, name="ChildComprehensionSpecialist"
    )

    review_supervisor = create_team_supervisor(
        llm,
        "You are a supervisor tasked with managing a conversation between the"
        " following workers: {team_members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
        " If there have already been 2 reviews, respond with FINISH."
        " You have reviewed the document {review_count} times."
        " You are only finished when both the ContentReviewer and ChildComprehensionSpecialist have reviewed the document.",
        ["ContentReviewer", "ChildComprehensionSpecialist"],
    )


    def convert_lesson_message(state: State):
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("convert_lesson_message - in make_document_review_team_graph")
        logger.info(f"convert_lesson_message: {state}")
        lesson = None
        if "lesson" in state:
            lesson = state["lesson"]

        if not lesson:
            lesson = Lesson(title="No Title", content="No Content")

        return {"lesson_title": lesson.title, "lesson_content": lesson.content}

    def increment_review_count(state: State):
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("increment_review_count - review team")
        new_review_count = 0
        existing_count = None
        if "review_count" in state and state["review_count"]:
            existing_count = state["review_count"]
        
        if not existing_count:
            logger.info("existing_count not found")
            existing_count = 0
        

        # cast existing_count to int
        existing_count_int = int(existing_count)

        new_review_count = existing_count_int + 1

        logger.info(f"existing_count: {existing_count}")
        logger.info(f"increment_review_count: {new_review_count}") 

        return {"review_count": new_review_count}
    
    increment_review_count_partial = functools.partial(increment_review_count)

    # Define the workflow
    workflow = StateGraph(State)

    # add_node - add nodes to the workflow
    workflow.add_node("ContentReviewer", content_reviewer_node)
    workflow.add_node("ChildComprehensionSpecialist", child_comprehension_specialist_node)
    workflow.add_node("supervisor", review_supervisor)
    workflow.add_node("convert_lesson_message", convert_lesson_message)
    workflow.add_node("increment_review_count", increment_review_count_partial)

    # Add the edges that always occur
    workflow.add_edge("ContentReviewer", "increment_review_count")
    workflow.add_edge("increment_review_count", "supervisor")
    workflow.add_edge("ChildComprehensionSpecialist", "supervisor")

    # Add the edges where routing applies
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "ContentReviewer": "ContentReviewer",
            "ChildComprehensionSpecialist": "ChildComprehensionSpecialist",
            "FINISH": END,
        },
    )

    workflow.add_edge(START, "convert_lesson_message")
    workflow.add_edge("convert_lesson_message", "supervisor")
    chain = workflow.compile()

    # The following functions interoperate between the top level graph state
    # and the state of the research sub-graph
    # this makes it so that the states of each graph don't get intermixed
    # params:
    # messages: a dict with "messages" key. the value of "messages" is a list of messages
    # members: a list of team members
    def enter_chain(messages: Dict[str, List[str]], members: List[str]):

        lesson = None
        if "lesson" in messages:
            lesson = messages["lesson"]
        else:
            lesson = Lesson(title="No Title (review_team enter chain)", content="No Content")
            logger.log("lesson not found in messages")

        research_items = []
        if "research_items" in messages:
            research_items = messages["research_items"]

        review_count = 0
        if "review_count" in messages:
            review_count = messages["review_count"]

        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("enter chain - review team")
        logger.info(f"messages: {messages}")
        logger.info(f"members: {members}")
        logger.info(f"lesson: {lesson}")
        logger.info(f"review_count: {review_count}")
        logger.info(f"research_items: {research_items}")

        results = {
            "messages": messages["messages"],
            "lesson": lesson,
            "review_count": review_count,
            "team_members": ", ".join(members)
        }
        return results


    # We reuse the enter/exit functions to wrap the graph
    members = workflow.nodes

    # members only if not supervisor, convert_lesson_message, or increment_review_count
    # should be a list
    specific_members_list = [m for m in members if m not in ["supervisor", "convert_lesson_message", "increment_review_count"]]

    review_chain = (
        functools.partial(enter_chain, members=specific_members_list)
        | workflow.compile()
    )

    return review_chain



file_structure_example = """
/app/docs_root/
    curriculum/
        mathematics/
            grade_1/
                addition/
                    index.md
                    properties.md
                    single_digit.md
                    double_digit.md
                    many_digits.md
                    [...etc...]
                subtraction/
                    index.md
                    properties.md
                    single_digit.md
                    double_digit.md
                    many_digits.md
                    [...etc...]
                [...etc...]
            [...etc...]
        social_studies/
            grade_1/
                geography/
                    index.md
                    maps.md
                    globes.md
                    [...etc...]
                history/
                    index.md
                    ancient_civilizations.md
                    modern_era.md
                    [...etc...]
                [...etc...]
            [...etc...]
        [...etc...]   
"""
# the template is:
# /app/docs_root/curriculum/{subject}/{grade}/{topic}/{document}.md


# This will be run before each worker agent begins work
# It makes it so they are more aware of the current state
# of the working directory.
def prelude(state):
    # get working directory from env
    WORKING_DIRECTORY_ENV = os.getenv("WORKING_DIRECTORY", "/app/docs_root")
    WORKING_DIRECTORY = Path(WORKING_DIRECTORY_ENV)

    written_files = []
    if not WORKING_DIRECTORY.exists():
        WORKING_DIRECTORY.mkdir()
    try:
        written_files = [
            f.relative_to(WORKING_DIRECTORY) for f in WORKING_DIRECTORY.rglob("*")
        ]
    except Exception:
        pass
    if not written_files:
        return {**state, "current_files": "No files written."}
    return {
        **state,
        "current_files": "\nBelow are files your team has written to the directory:\n"
        + "\n".join([f" - {f}" for f in written_files])
        + "\nHere is an example of the file structure:\n"
        + file_structure_example
        + "\n"
        + "respect the format indicated by the following examples:"
        + "\n"
        + "- /app/docs_root/curriculum/[subject]/[grade]/[topic]/[document].md"
        + "\n"
        + "- /app/docs_root/curriculum/[subject]/[grade]/[topic]/[graph_title].png"
        + "\n"
        + "\n"
        + "generate meaningful names for [document] and [graph_title] to make it easier for humans to navigate the files."
        + "\n"
        + "Do not include spaces or special characters in file names. Use only letters, numbers, underscores, and hyphens."
        + "\n"
        + "For example, use 'grade_1' instead of 'Grade 1'.",
    }
def make_document_writing_team_graph(logger=None):
    # set up logging
    logger = logger or logging.getLogger(__name__)
    logger.info("make_document_writing_team_graph")

    # define the state
    class State(TypedDict):
        # This tracks the team's conversation internally
        messages: Annotated[List[BaseMessage], operator.add]
        # This provides each worker with context on the others' skill sets
        team_members: str
        # This is how the supervisor tells langgraph who to work next
        next: str
        # This tracks the shared directory state
        current_files: str

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # make agents
    doc_writer_agent = create_agent(
        llm,
        [write_document, edit_document, read_document],
        "You are an expert writing a research document.\n"
        "If there's an error using a tool. try once more. If it fails again, just say you are done and provide the error.\n"
        # The {current_files} value is populated automatically by the graph state
        "Below are files currently in your directory:\n{current_files}",
    )
    # Injects current directory working state before each call
    context_aware_doc_writer_agent = prelude | doc_writer_agent
    doc_writing_node = functools.partial(
        agent_node, agent=context_aware_doc_writer_agent, name="DocWriter"
    )

    note_taking_agent = create_agent(
        llm,
        [create_outline, read_document],
        "You are an expert senior researcher tasked with writing a paper outline and"
        " taking notes to craft a perfect paper.{current_files}",
    )
    context_aware_note_taking_agent = prelude | note_taking_agent
    note_taking_node = functools.partial(
        agent_node, agent=context_aware_note_taking_agent, name="NoteTaker"
    )

    chart_generating_agent = create_agent(
        llm,
        [read_document, python_repl],
        "You are a data viz expert tasked with generating charts for a research project."
        "Save your charts as PNGs in the shared directory. "
        "{current_files}",
    )
    context_aware_chart_generating_agent = prelude | chart_generating_agent
    chart_generating_node = functools.partial(
        agent_node, agent=context_aware_chart_generating_agent, name="ChartGenerator"
    )

    doc_writing_supervisor = create_team_supervisor(
        llm,
        "You are a supervisor tasked with managing a conversation between the"
        " following workers:  {team_members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH.",
        ["DocWriter", "NoteTaker", "ChartGenerator"],
    )






    # Define the workflow
    workflow = StateGraph(State)

    # add_node - add nodes to the workflow
    workflow.add_node("DocWriter", doc_writing_node)
    workflow.add_node("NoteTaker", note_taking_node)
    workflow.add_node("ChartGenerator", chart_generating_node)
    workflow.add_node("supervisor", doc_writing_supervisor)

    # Add the edges that always occur
    workflow.add_edge("DocWriter", "supervisor")
    workflow.add_edge("NoteTaker", "supervisor")
    workflow.add_edge("ChartGenerator", "supervisor")

    # Add the edges where routing applies
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "DocWriter": "DocWriter",
            "NoteTaker": "NoteTaker",
            "ChartGenerator": "ChartGenerator",
            "FINISH": END,
        },
    )

    workflow.add_edge(START, "supervisor")
    chain = workflow.compile()

    # return chain

    # TODO: test this
    # The following functions interoperate between the top level graph state
    # and the state of the research sub-graph
    # this makes it so that the states of each graph don't get intermixed
    def enter_chain(message: str, members: List[str]):
        results = {
            "messages": [HumanMessage(content=message)],
            "team_members": ", ".join(members),
        }
        return results


    # We reuse the enter/exit functions to wrap the graph
    authoring_chain = (
        functools.partial(enter_chain, members=workflow.nodes)
        | workflow.compile()
    )

    return authoring_chain




def make_graph(logger=None):
    logger = logger or logging.getLogger(__name__)
    logger.info("make_graph")

    research_graph = make_research_team_graph(logger=logger)
    document_writing_graph = make_document_writing_team_graph(logger=logger)
    review_graph = make_document_review_team_graph(logger=logger)


    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    supervisor_node = create_team_supervisor(
        llm,
        "You are a supervisor tasked with managing a conversation between the"
        " following teams: {team_members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
        " Always have the ReviewTeam review the content after ResearchTeam has finished."
        " if the ReviewTeam has already reviewed the content 2 times, do not call on them again."
        " The ReviewTeam has reviewed the content {review_count} times."
        " Always have the ReviewTeam review the content before calling on the DocsTeam."
        " The DocsTeam will only be called on after the ReviewTeam has reviewed the content."
        " You're only finished when the DocsTeam has finished writing the document.",
        ["ResearchTeam", "DocsTeam", "ReviewTeam"],
    )

    # Top-level graph state
    class State(TypedDict):
        messages: Annotated[List[BaseMessage], operator.add]
        next: str
        research_items: Annotated[ResearchItems, operator.add]
        
        # This will be generated in the ReviewTeam sub-graph
        review_count: int

        # the document content generated by the research team
        lesson: Lesson


    def get_last_message(state: State) -> str:
        return state["messages"][-1].content


    def join_graph(response: dict):
        response_final = {}
        if "lesson" in response:
            response_final["lesson"] = response["lesson"]
        else:
            response_final["lesson"] = Lesson(title="No Title (join)", content="No Content")

        if "research_items" in response:
            response_final["research_items"] = response["research_items"]
        else:
            response_final["research_items"] = []

        if "messages" in response:
            response_final["messages"] = [response["messages"][-1]]
        else:
            response_final["messages"] = []

        logger.info(f"join_graph response: {response}")
        if "review_count" in response:
            response_final["review_count"] = response["review_count"]
        else:
            response_final["review_count"] = 0
        return response_final
    
    def increment_review_count(state: State):
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("increment_review_count")
        new_review_count = 0
        existing_count = None
        if "review_count" in state and state["review_count"]:
            existing_count = state["review_count"]
        
        if not existing_count:
            logger.info("existing_count not found")
            existing_count = 0
        

        # cast existing_count to int
        existing_count_int = int(existing_count)

        new_review_count = existing_count_int + 1

        logger.info(f"existing_count: {existing_count}")
        logger.info(f"increment_review_count: {new_review_count}") 

        return {"review_count": new_review_count}
    
    increment_review_count_partial = functools.partial(increment_review_count)

    def review_team_wrapper_func(state: State):
        # TODO: map state
        review_graph_response = review_graph.invoke(state)

        logger.info(f"review_team_wrapper_func:")
        logger.info(f"review_graph_response: {review_graph_response}")

        join_graph_response = join_graph(review_graph_response)

        logger.info(f"join_graph_response: {join_graph_response}")

        return join_graph_response
    review_team_wrapper_func_partial = functools.partial(review_team_wrapper_func)

    # Define the graph.
    super_graph = StateGraph(State)
    # First add the nodes, which will do the work
    super_graph.add_node("ResearchTeam", get_last_message | research_graph | join_graph)
    super_graph.add_node("DocsTeam", get_last_message | document_writing_graph | join_graph)
    super_graph.add_node("ReviewTeam", review_team_wrapper_func_partial)
    super_graph.add_node("supervisor", supervisor_node)
    super_graph.add_node("increment_review_count", increment_review_count_partial)

    # Define the graph connections, which controls how the logic
    # propagates through the program
    super_graph.add_edge("ResearchTeam", "supervisor")
    super_graph.add_edge("DocsTeam", "supervisor")
    super_graph.add_edge("ReviewTeam", "increment_review_count")
    super_graph.add_edge("increment_review_count", "supervisor")
    super_graph.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "DocsTeam": "DocsTeam",
            "ResearchTeam": "ResearchTeam",
            "ReviewTeam": "ReviewTeam",
            "FINISH": END,
        },
    )
    super_graph.add_edge(START, "supervisor")
    super_graph = super_graph.compile()

    return {
        "research_graph": research_graph,
        "document_writing_graph": document_writing_graph,
        "review_graph": review_graph,
        "super_graph": super_graph,
    }