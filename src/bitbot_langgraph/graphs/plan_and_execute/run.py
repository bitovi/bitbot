# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# utilities
from bitbot_langgraph.graphs.plan_and_execute.make import make_graph
from bitbot_langgraph.utilities.run_graph import run_graph
from bitbot_langgraph.utilities.make_mermaid_from_app import make_mermaid_from_app

# use python to get the name of the current directory
import os
current_directory = os.path.dirname(__file__)
mermaid_path = os.path.join(current_directory, "graph.mermaid.md")

def save_graph_to_file(app, filepath=mermaid_path, logger=None):
    logger = logger or logging.getLogger(__name__)

    logger.debug(f"save_graph_to_file: {mermaid_path}")

    # generate mermaid from the app and save to file
    return make_mermaid_from_app(app, path=filepath, logger=logger)
    


# run
default_inputs = { "input": "Create a .5h lesson on introduction to geometry. use lots of examples." }
default_config = { "recursion_limit": 50 }
async def run(inputs=default_inputs, logger=None, output_graph=False, config=default_config, memory=None):
    logger = logger or logging.getLogger(__name__)
    logger.info(f"run with inputs: {inputs}")

    app = make_graph(logger, memory)
    logger.info(f"apps: {app}")
    logger.info(f"config: {config}")


    # generate mermaid from the app and save to file
    if output_graph:
        save_graph_to_file(app, filepath=mermaid_path, logger=logger)


    # run apps["super_graph"]
    logger.info(f"running graph for super_graph")

    await run_graph(
        app,
        inputs,
        config,
        logger=logger,
        input_transformer=None
    )
