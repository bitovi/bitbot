from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

# agent prompt
agent_executor_prompt = """
================================ System Message ================================

You are a helpful assistant.

============================= Messages Placeholder =============================

{{messages}}
"""

# agent factory
# returns a multi-tool reAct agent (prompt drive reAct agent)
def make_agent(tools=None, logger=None, model="gpt-4o-mini"):
    logger = logger or logging.getLogger(__name__)

    llm = ChatOpenAI(model=model)

    logger.info(f"make_agent: {model}")
    logger.info(f"  tools: {tools}")

    return create_react_agent(llm, tools, messages_modifier=agent_executor_prompt)


# test agent
def test_agent(query, tools=None, logger=None):
    if not logger:
        logger = logging.getLogger(__name__)
    logger.info("plan_and_execute.py test_agent")
    logger.info("make_agent")
    logger.info(f"tools: {tools}")
    agent = make_agent(tools)
    logger.info(f"agent: {agent}")

    logger.info("invoking agent")
    agent_response = agent.invoke({
        "messages": [
            ("user", query)
        ]
    })
    
    logger.info(f"agent_response: {agent_response}")
    return agent_response
