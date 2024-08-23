# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# utilities
from bitbot_langgraph.graphs.heirarchical_teams.make import make_graph
from bitbot_langgraph.utilities.run_graph import run_graph_sync
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

def save_graph_to_file(app, filepath=mermaid_path, logger=None):
    logger = logger or logging.getLogger(__name__)

    logger.debug(f"save_graph_to_file: {mermaid_path}")

    # generate mermaid from the app and save to file
    return make_mermaid_from_app(app, path=filepath, logger=logger)
    


# run
default_inputs = { "input": "Create a .5h lesson on introduction to geometry. use lots of examples." }
default_config = { "recursion_limit": 50 }
async def run(inputs=default_inputs, logger=None, output_graph=False, config=default_config):
    logger = logger or logging.getLogger(__name__)
    logger.info(f"run with inputs: {inputs}")

    apps = make_graph(logger)
    logger.info(f"apps: {apps}")
    logger.info(f"config: {config}")


    # generate mermaid from the app and save to file
    if output_graph:
        # iterate through apps dict (looks like this: { "app1": app, "app2": app2 })
        for app_name, app in apps.items():
            logger.info(f"outputting graph for {app_name}")
            new_mermaid_filename = f"{app_name}.mermaid.md"

            # replace the last part of mermaid_path with the new filename
            new_mermaid_full_path = mermaid_path.replace("graph.mermaid.md", new_mermaid_filename)
            save_graph_to_file(app, filepath=new_mermaid_full_path, logger=logger)


    # run apps["research_graph"]
    # logger.info(f"running graph for research_graph")
    # run_graph_sync(
    #     apps["research_graph"],
    #     inputs,
    #     config,
    #     logger=logger
    # )

    # run apps["document_writing_graph"]
    # logger.info(f"running graph for document_writing_graph")
    # run_graph_sync(
    #     apps["document_writing_graph"],
    #     inputs,
    #     config,
    #     logger=logger
    # )

    # run apps["super_graph"]
    logger.info(f"running graph for super_graph")
    run_graph_sync(
        apps["super_graph"],
        inputs,
        config,
        logger=logger
    )
