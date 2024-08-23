# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# utilities
from bitbot_langgraph.graphs.multi_agent_collaboration.make import make_graph
from bitbot_langgraph.utilities.run_graph import run_graph
from bitbot_langgraph.utilities.make_mermaid_from_app import make_mermaid_from_app

# use python to get the name of the current directory
import os
current_directory = os.path.dirname(__file__)
mermaid_path = os.path.join(current_directory, "graph.mermaid.md")

###
### Tool definitions
###
# from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
# from langchain_community.utilities.github import GitHubAPIWrapper
# github = GitHubAPIWrapper()
# toolkit = GitHubToolkit.from_github_api_wrapper(github)
# github_tools = toolkit.get_tools()


# from homeschool_langgraph.tools.all_tools import get_tools

def save_graph_to_file(app, logger=None):
    logger = logger or logging.getLogger(__name__)

    logger.debug(f"save_graph_to_file: {mermaid_path}")

    # generate mermaid from the app and save to file
    return make_mermaid_from_app(app, path=mermaid_path, logger=logger)
    


# run
default_inputs = { "input": "Create a .5h lesson on introduction to geometry. use lots of examples." }
default_config = { "recursion_limit": 50 }
async def run(inputs=default_inputs, logger=None, output_graph=False, config=default_config):
    logger = logger or logging.getLogger(__name__)
    logger.info(f"run with inputs: {inputs}")

    app = make_graph(logger)
    logger.info(f"app: {app}")
    logger.info(f"config: {config}")


    # generate mermaid from the app and save to file
    if output_graph:
        logger.info("outputting graph")
        save_graph_to_file(app, logger)



    logger.info("running graph")
    await run_graph(
        app,
        inputs,
        config,
        logger=logger
    )
