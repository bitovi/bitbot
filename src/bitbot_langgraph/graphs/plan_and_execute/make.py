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
from bitbot_langgraph.graphs.plan_and_execute.steps.plan_or_response import (
    Step as PlanOrResponseStep
)
from bitbot_langgraph.graphs.plan_and_execute.steps.slack_send_message import (
    Step as SlackSendMessageStep
)



def make_graph(logger=None, memory=None):
    logger = logger or logging.getLogger(__name__)
    logger.info("make_graph")

    # set up tools
    # TODO: fetch from external source (subgraph under executor?)
    # tools = [scrape_webpages, duckduckgo_tool, wikipedia_tool]



    # conditional edge methods
    def should_end(state: State) -> Literal["plan", "respond"]:
        if "response" in state and state["response"]:
            return "respond"
        else:
            return "plan"



    return build_app_from_dict({
        "nodes": {
            "planner": PlanStep(logger, model_name="gpt-4o").node,
            "agent": ExecutorStep(logger, model_name="gpt-4o").node,
            #  node for deciding whether to replan or send the response
            "plan_or_response": PlanOrResponseStep(logger, model_name="dwightfoster03/functionary-small-v3.1:latest").node,
            # "plan_or_response": PlanOrResponseStep(logger, model_name="lm_studio").node,
            # "plan_or_response": PlanOrResponseStep(logger).node,
            "replan": {
                "node": ReplannerStep(logger, model_name="gpt-4o").node,
                "retry": {
                    "max_attempts": 5
                }
            },

            # new node for generating a final response
            "format_response": ResponseFormatterStep(logger, model_name="gpt-4o").node,

            # node for sending the final response to slack
            "slack_send_message": SlackSendMessageStep(logger).node
        },
        "edges": {
            START: "planner",
            "planner": "agent",
            "replan": "agent",
            "agent": "plan_or_response",
            "format_response": "slack_send_message",
            "slack_send_message": END
        },
        "conditional_edges": {
            "plan_or_response": {
                "function": should_end,
                "mapping": { "plan": "replan", "respond": "format_response" }
            }
        }
    }, State, checkpointer=memory, logger=logger)
