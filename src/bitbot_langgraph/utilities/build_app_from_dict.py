from typing import Annotated, List, TypedDict, Dict, Tuple, Union, Literal, Optional
from langgraph.graph import START, END, StateGraph, MessagesState

# this function iterates a dict and generates a langgraph graph from it
# here is an example dict:
# workflow_dict = {
#     "nodes": {
#         "planner": plan_step,
#         "agent": execute_step,
#         "replan": replan_step,
#         "concat_steps_to_lesson": concat_steps_to_lesson
#     },
#     "edges": {
#         START: "planner",
#         "planner": "agent",
#         "agent": "replan",
#         "concat_steps_to_lesson": END
#     },
#     "conditional_edges": {
#         "replan": {
#             "function": should_end,
#             "mapping": { "agent": "agent", "__end__": "concat_steps_to_lesson" }
#         }
#     }
# }
# Here's the desired output from the above dict:
# workflow = StateGraph(State)
# workflow.add_node("planner", plan_step)
# workflow.add_node("agent", execute_step)
# workflow.add_node("replan", replan_step)
# workflow.add_node("concat_steps_to_lesson", concat_steps_to_lesson)

# workflow.add_edge(START, "planner")
# workflow.add_edge("planner", "agent")
# workflow.add_edge("agent", "replan")
# workflow.add_edge("concat_steps_to_lesson", END)

# workflow.add_conditional_edges(
#     "replan",
#     # Next, we pass in the function that will determine which node is called next.
#     should_end,
#     { "agent": "agent", "__end__": "concat_steps_to_lesson" }
# )
def build_app_from_dict(app_dict: dict, state: dict, checkpointer=None):
    """Build a graph from a dict."""

    workflow = StateGraph(state)

    for node_name, node_func in app_dict["nodes"].items():
        workflow.add_node(node_name, node_func)

    for start_node, end_node in app_dict["edges"].items():
        workflow.add_edge(start_node, end_node)

    for node_name, conditional_edge in app_dict["conditional_edges"].items():
        f = conditional_edge["function"]
        m = conditional_edge["mapping"]

        if not callable(f):
            raise ValueError("The function must be callable.")
        
        if not m or not isinstance(m, dict):
            # do nothing
            pass

        workflow.add_conditional_edges(
            node_name,
            conditional_edge["function"],
            conditional_edge["mapping"]
        )

    app = workflow.compile(checkpointer=checkpointer)
    return app
