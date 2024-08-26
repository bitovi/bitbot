# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
from langchain_core.messages import HumanMessage


# function to transform inputs into the format expected by the graph
def transform_inputs(inputs):
    return { 
        "messages": [HumanMessage(inputs["input"])]
    }

def run_graph_sync(app, inputs, config, logger=None, stream_mode="values", input_transformer=transform_inputs):
    logger = logger or logging.getLogger(__name__)

    logger.info("run_graph.py run_graph_sync")

    logger.info(f"inputs: {inputs}")
    transformed_inputs = inputs
    if input_transformer:
        transformed_inputs = input_transformer(inputs)


    logger.info(f"transformed_inputs: {transformed_inputs}")
    for event in app.stream(
        transformed_inputs,
        config=config
    ):
        
        
        logger.debug("")
        logger.debug("")
        logger.debug("=========")
        logger.debug("=========")
        logger.debug("event",event)
        logger.debug("=========")
        logger.debug("=========")

        ret = None
        for k, v in event.items():
            if k != "__end__":
                logger.info(v)
                logger.info("=========")
            else:
                logger.info("END")
                logger.info("=========")
                logger.info(v)
                ret = v
        return ret


async def run_graph(app, inputs, config, logger=None, stream_mode="values", input_transformer=transform_inputs):
    logger = logger or logging.getLogger(__name__)

    logger.info("run_graph.py run_graph")

    logger.info(f"inputs: {inputs}")
    transformed_inputs = inputs
    if input_transformer:
        transformed_inputs = input_transformer(inputs)

    logger.info(f"transformed_inputs: {transformed_inputs}")
    async for event in app.astream(
        transformed_inputs,
        config=config,
        stream_mode=stream_mode
    ):
        
        
        logger.debug("")
        logger.debug("")
        logger.debug("=========")
        logger.debug("=========")
        logger.debug("event",event)
        logger.debug("=========")
        logger.debug("=========")

        # output all but the messages first
        for k, v in event.items():
            if k != "__end__" and k != "messages":
                logger.info(v)
            if k == "__end__":
                logger.info("==END==")
                logger.info(v)


        # output the messages
        event_messages = event.get("messages", [])
        if event_messages and len(event_messages) > 0:
            last_message = event_messages[-1]
            logger.info("======")
            logger.info("last_message")
            logger.info(last_message)
            logger.info("======")
            logger.info(last_message.pretty_repr())

    

