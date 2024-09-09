import os
import asyncio
import time
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from bitbot_langgraph.graphs.multi_agent_collaboration.run import run as multi_agent_collaboration_run
from bitbot_langgraph.graphs.heirarchical_teams.run import run as heirarchical_teams_run
from bitbot_langgraph.graphs.plan_and_execute.run import run as plan_and_execute_run


from slack_bolt.app.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.error import BoltUnhandledRequestError
from slack_bolt.response import BoltResponse

# from langgraph.checkpoint.sqlite import SqliteSaver
# import sqlite3

import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




# Initializes your slack_app with your bot token and socket mode handler


slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
slack_app_token = os.environ.get("SLACK_APP_TOKEN")

slack_app = AsyncApp(
    token=slack_bot_token,
    raise_error_for_unhandled_request=True
)


# async def _run_collab():
#     logger.info("main.py _run_collab")

#     inputs = { "input": "fetch the United States' GDP over the last 5 years, then draw a line graph of it. once you code it, finish" }
#     # config = { "recursion_limit": 50, "configurable": {"thread_id": "2"} }
#     config = { "recursion_limit": 50 }
#     results = await multi_agent_collaboration_run(inputs, output_graph=True, config=config)

#     if not results:
#         logger.info("No results")
#         return
    

#     if not results["messages"]:
#         logger.info("No messages")
#         logger.info(f"results: {results}")
#         return
    

#     # final_message = results["messages"][-1]
#     # final_message_content = final_message.content
#     # final_message_response_metadata = final_message.response_metadata
#     # final_message_usage_metadata = final_message.usage_metadata

#     logger.info("")
#     logger.info("==============================")
#     logger.info("==============================")
#     logger.info("==============================")
#     logger.info("results: ", results)
#     # logger.info("final_message", final_message)
#     # logger.info("=======")
#     # logger.info(f"final_message_content: {final_message_content}")
#     # logger.info("=======")
#     # logger.info(f"final_message_response_metadata: {final_message_response_metadata}")
#     # logger.info("=======")
#     # logger.info(f"final_message_usage_metadata: {final_message_usage_metadata}")
#     logger.info("==============================")

# async def _run_teams():
#     logger.info("main.py _run_teams")

#     inputs = { "input": "Create a .5h lesson on mathematics order of precedence for operators." }
#     # config = { "recursion_limit": 50, "configurable": {"thread_id": "2"} }
#     config = { "recursion_limit": 100 }
#     results = await heirarchical_teams_run(inputs, output_graph=True, config=config)

#     if not results:
#         logger.info("No results")
#         return
    

#     if not results["messages"]:
#         logger.info("No messages")
#         logger.info(f"results: {results}")
#         return
    

#     # final_message = results["messages"][-1]
#     # final_message_content = final_message.content
#     # final_message_response_metadata = final_message.response_metadata
#     # final_message_usage_metadata = final_message.usage_metadata

#     logger.info("")
#     logger.info("==============================")
#     logger.info("==============================")
#     logger.info("==============================")
#     logger.info("results: ", results)
#     # logger.info("final_message", final_message)
#     # logger.info("=======")
#     # logger.info(f"final_message_content: {final_message_content}")
#     # logger.info("=======")
#     # logger.info(f"final_message_response_metadata: {final_message_response_metadata}")
#     # logger.info("=======")
#     # logger.info(f"final_message_usage_metadata: {final_message_usage_metadata}")
#     logger.info("==============================")

async def _run_plan_and_execute(query, thread_id=None):
    logger.info("main.py _run_plan_and_execute")
    logger.info(f"query: {query}")
    # mempath from env var: SQLITE_DB_PATH
    mempath = os.getenv("SQLITE_DB_PATH", "checkpoints.sqlite")


    # input_query = """
    # plan a trip to vermont in september. 
    # it should be for 2 weeks.
    # we'll be driving and camping.
    # We'll be driving a camper van.
    # we like hiking. we have 3 kids (6, 3, and 0), and we will not be able to go on long hikes (a few miles at most).
    # We'll be driving a little ways (max 7h at a time) and then stopping at an airBnB for monday through thursday.
    # We can drive further on friday and saturday and camp on the weekends, too.
    # You do not have access to a human to ask questions. You must use your best judgement.
    # Fridays are preferable for travel days (though not the only days for travel)
    # Starting location is Kingsport, TN
    # When you don't have the information you need, ask me.
    # """


    input_query = """
    how many U.S. gold medalists in 2024?
    """    



    if query:
        input_query = query
    
    inputs = {
        "input": input_query,
        "thread_id": thread_id
    }
    config = { "recursion_limit": 100, "configurable": {"thread_id": thread_id} }
    results = None
    async with aiosqlite.connect(mempath) as conn:
        memory = AsyncSqliteSaver(conn)
        try:
            results = await plan_and_execute_run(inputs, output_graph=True, config=config, memory=memory)
        except Exception as e:
            logger.error(f"Caught Error from plan_and_execute_run: {e}")


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

    logger.info("Starting app..")
    handler = AsyncSocketModeHandler(slack_app, slack_app_token)
    await handler.start_async()

    # await _run_collab()
    # await _run_teams()
    # results = await _run_plan_and_execute(query, thread_id)
    # logger.info(f"results: {results}")
    # return results

    # # generate thread id
    # thread_id = str(int(time.time()))
    # # thread_id = "1724649395"

    # # await _run_collab()
    # # await _run_teams()
    # while True:
    #     # get input from user
    #     logger.info(f"thread_id: {thread_id}")
    #     query = input("Enter a query: ")

    #     try:
    #         results = await _run_plan_and_execute(query, thread_id)
    #         logger.info(f"results: {results}")
    #     except Exception as e:
    #         logger.error(f"Caught Error in outer loop: {e}")



# # error handler
@slack_app.error
async def handle_errors(error):
    if isinstance(error, BoltUnhandledRequestError):
        # you may want to have some logging here
        return BoltResponse(status=200, body="")
    else:
        # other error patterns
        return BoltResponse(status=500, body="Something Wrong")


@slack_app.message(":wave:")
async def say_hello(message, say):
    user = message['user']
    await say(f"Hi there, <@{user}>!")


# # listens to mentions of the bot and calls the temporal agent with the query
# # then posts the result to the channel
@slack_app.event("app_mention")
async def handle_app_mention(say, body, client):
    logger.info("=====================================")
    logger.info("=====================================")
    logger.info("=====================================")
    logger.info("=====================================")
    logger.info("=====================================")
    logger.info("=====================================")
    logger.info("in client.py/handle_app_mention")

    logger.info(f"body: {body}")
    event = body["event"]
    logger.info(f"event: {event}")

    logger.info(f"client: {client}")


    #replace the bot mention (e.g. `<@.......>`) with an empty string
    user_id = body["authorizations"][0]["user_id"]
    logger.info(f"user_id: {user_id}")

    query = body["event"]["text"].replace(f"<@{user_id}>", "").strip()
    logger.info(f"query: {query}")

    thread_ts = event.get("thread_ts", None) or event["ts"]
    logger.info(f"thread_ts: {thread_ts}")  

    channel = event["channel"]
    logger.info(f"channel: {channel}")

    logger.info("adding reaction to message")
    await client.reactions_add(
        channel=event["channel"],
        name="eyes",
        timestamp=thread_ts
    )

    # ack_thread_id = ack_response["message"]["thread_ts"]
    # logger.info(f"ack_thread_id: {ack_thread_id}")

    result = await _run_plan_and_execute(query, thread_ts)

    logger.info(f"Result: {result}")

    # remove reaction
    logger.info("removing reaction from message")
    await client.reactions_remove(
        channel=channel,
        name="eyes",
        timestamp=thread_ts
    )


#     say(f"Result: {result}")
#     ack_message_final = f"""
# Responded to your query:

# > {query}
#     """
#     ack_response_final = await say(ack_message_final, thread_ts=ack_thread_id)
#     logger.info(f"ack_response_final: {ack_response_final}")


def main():
    # Start your app
    asyncio.run(_main())


if __name__ == "__main__":
    main()