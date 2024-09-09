from typing import Optional
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep


class Step(BaseStep):


    def __init__(self, logger: Optional[logging.Logger] = None, prompt_template: str = None, model_name: str = "gpt-4o-mini"):
        super().__init__(logger)
        self.logger.info("slack_send_message.py")


        self.client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])

    async def node(self, state: dict):
        logger = self.logger
        logger.info(f"slack_send_message step")
        logger.debug(f"slack_poster step: {state}")

        response = state.get("response")
        if not response:
            # a response is required
            raise ValueError("No response provided to slack poster")
        
        logger.info(f"response: {response}")

        thread_id = state.get("thread_id")
        logger.info(f"slack_send_message - thread_id: {thread_id}")
        txt = response.content
        
        if thread_id:
            try:
                response = self.client.chat_postMessage(channel='#bitbot-testing', text=txt, thread_ts=thread_id, mrkdwn=True)
            except SlackApiError as e:
                logger.error(f"Error posting message to thread: {e}")
        else:
            try:
                response = self.client.chat_postMessage(channel='#bitbot-testing', text=txt, mrkdwn=True)
            except SlackApiError as e:
                logger.error(f"Error posting message: {e}")

        return {
            "response": None
        }
