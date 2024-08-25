from langgraph.graph import START, END
from typing import Literal

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

# utilities
from bitbot_langgraph.utilities.build_app_from_dict import build_app_from_dict

# state
from bitbot_langgraph.graphs.plan_and_execute.state import State

# steps
from bitbot_langgraph.graphs.plan_and_execute.steps.planner import (
    Step as PlanStep
)
from bitbot_langgraph.graphs.plan_and_execute.steps.replanner import (
    Step as ReplannerStep
)
from bitbot_langgraph.graphs.plan_and_execute.steps.executor import (
    Step as ExecutorStep
)
from bitbot_langgraph.graphs.plan_and_execute.steps.response_formatter import (
    Step as ResponseFormatterStep
)



def make_graph(logger=None, memory=None):
    logger = logger or logging.getLogger(__name__)
    logger.info("make_graph")

    # set up tools
    # TODO: fetch from external source (subgraph under executor?)
    # tools = [scrape_webpages, duckduckgo_tool, wikipedia_tool]



    # conditional edge methods
    def should_end(state: State) -> Literal["agent", "format"]:
        if "response" in state and state["response"]:
            return "format"
        else:
            return "agent"



    return build_app_from_dict({
        "nodes": {
            "planner": PlanStep(logger, model_name="gpt-4o").node,
            "agent": ExecutorStep(logger, model_name="gpt-4o").node,
            # TODO: new node for deciding whether to replan or send the response
            "replan": {
                "node": ReplannerStep(logger, model_name="gpt-4o").node,
                "retry": {
                    "max_attempts": 5
                }
            },

            # new node for generating a final response
            "format_response": ResponseFormatterStep(logger).node,

            # TODO: new node for sending the final response to slack
        },
        "edges": {
            START: "planner",
            "planner": "agent",
            "agent": "replan",
            "format_response": END
        },
        "conditional_edges": {
            "replan": {
                "function": should_end,
                "mapping": { "agent": "agent", "format": "format_response" }
            }
        }
    }, State, checkpointer=memory, logger=logger)
