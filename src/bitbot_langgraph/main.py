import os
import asyncio
import time
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from bitbot_langgraph.graphs.multi_agent_collaboration.run import run as multi_agent_collaboration_run
from bitbot_langgraph.graphs.heirarchical_teams.run import run as heirarchical_teams_run
from bitbot_langgraph.graphs.plan_and_execute.run import run as plan_and_execute_run


# from langgraph.checkpoint.sqlite import SqliteSaver
# import sqlite3

import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _run_collab():
    logger.info("main.py _run_collab")

    inputs = { "input": "fetch the United States' GDP over the last 5 years, then draw a line graph of it. once you code it, finish" }
    # config = { "recursion_limit": 50, "configurable": {"thread_id": "2"} }
    config = { "recursion_limit": 50 }
    results = await multi_agent_collaboration_run(inputs, output_graph=True, config=config)

    if not results:
        logger.info("No results")
        return
    

    if not results["messages"]:
        logger.info("No messages")
        logger.info(f"results: {results}")
        return
    

    # final_message = results["messages"][-1]
    # final_message_content = final_message.content
    # final_message_response_metadata = final_message.response_metadata
    # final_message_usage_metadata = final_message.usage_metadata

    logger.info("")
    logger.info("==============================")
    logger.info("==============================")
    logger.info("==============================")
    logger.info("results: ", results)
    # logger.info("final_message", final_message)
    # logger.info("=======")
    # logger.info(f"final_message_content: {final_message_content}")
    # logger.info("=======")
    # logger.info(f"final_message_response_metadata: {final_message_response_metadata}")
    # logger.info("=======")
    # logger.info(f"final_message_usage_metadata: {final_message_usage_metadata}")
    logger.info("==============================")

async def _run_teams():
    logger.info("main.py _run_teams")

    inputs = { "input": "Create a .5h lesson on mathematics order of precedence for operators." }
    # config = { "recursion_limit": 50, "configurable": {"thread_id": "2"} }
    config = { "recursion_limit": 100 }
    results = await heirarchical_teams_run(inputs, output_graph=True, config=config)

    if not results:
        logger.info("No results")
        return
    

    if not results["messages"]:
        logger.info("No messages")
        logger.info(f"results: {results}")
        return
    

    # final_message = results["messages"][-1]
    # final_message_content = final_message.content
    # final_message_response_metadata = final_message.response_metadata
    # final_message_usage_metadata = final_message.usage_metadata

    logger.info("")
    logger.info("==============================")
    logger.info("==============================")
    logger.info("==============================")
    logger.info("results: ", results)
    # logger.info("final_message", final_message)
    # logger.info("=======")
    # logger.info(f"final_message_content: {final_message_content}")
    # logger.info("=======")
    # logger.info(f"final_message_response_metadata: {final_message_response_metadata}")
    # logger.info("=======")
    # logger.info(f"final_message_usage_metadata: {final_message_usage_metadata}")
    logger.info("==============================")

async def _run_plan_and_execute():
    logger.info("main.py _run_plan_and_execute")


    input_query = """
    plan a trip to vermont in september. 
    it should be for 2 weeks.
    we'll be driving and camping.
    We'll be driving a camper van.
    we like hiking. we have 3 kids (6, 3, and 0), and we will not be able to go on long hikes (a few miles at most).
    We'll be driving a little ways (max 7h at a time) and then stopping at an airBnB for monday through thursday.
    We can drive further on friday and saturday and camp on the weekends, too.
    You do not have access to a human to ask questions. You must use your best judgement.
    Fridays are preferable for travel days (though not the only days for travel)
    Starting location is Kingsport, TN
    When you don't have the information you need, ask me.
    """
    inputs = { "input": input_query }
    # config = { "recursion_limit": 50, "configurable": {"thread_id": "2"} }
    auto_threading = True
    thread_id = str(int(time.time())) # uncomment for auto threading

    # custom thread stuff
    # thread_id = "1724340719"
    # inputs = { 
    #     "input": (
    #         "make the list"
    #     )
    # }
    
    logger.info(f"thread_id: {thread_id}")
    config = { "recursion_limit": 100, "configurable": {"thread_id": thread_id} }
        # mempath from env var: SQLITE_DB_PATH
    mempath = os.getenv("SQLITE_DB_PATH", "checkpoints.sqlite")
    # logger.info(f"mempath: {mempath}")
    # conn = sqlite3.connect(mempath)
    # memory = SqliteSaver(conn)
 
    async with aiosqlite.connect(mempath) as conn:
        memory = AsyncSqliteSaver(conn)
        results = await plan_and_execute_run(inputs, output_graph=True, config=config, memory=memory)

    if not results:
        logger.info("No results")
        logger.info(f"thread_id: {thread_id}")
        logger.info(f"")
        return
    

    if not results["messages"]:
        logger.info("No messages")
        logger.info(f"results: {results}")
        return

async def _main():
    logger.info("main.py main")

    # await _run_collab()
    # await _run_teams()
    await _run_plan_and_execute()


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()