from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate

from typing import Optional

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep

# tools
from bitbot_langgraph.tools.slack import tools as slack_tools

class Step(BaseStep):

    _prompt_template = """
=============================== System Message ===============================
You are a precise and efficient slack posting assistant.
Your role is to post messages to slack.
your response should be super well formatted markdown
============================= Here is the message to post =============================
{messages}
"""


    def __init__(self, logger: Optional[logging.Logger] = None, prompt_template: str = None, model_name: str = "gpt-4o-mini"):
        super().__init__(logger)
        logger.info("executor.py - make_step")

        if prompt_template is not None:
            self._prompt_template = prompt_template

        self.prompt_template = PromptTemplate.from_template(self._prompt_template)

        logger.info(f"executor prompt_template: {self.prompt_template}")
        llm = ChatOpenAI(model=model_name, temperature=0)
        self._runnable = create_react_agent(llm, slack_tools, state_modifier=self.prompt_template)

    async def node(self, state: dict):
        logger = self.logger
        logger.info(f"slack_poster step")
        logger.debug(f"slack_poster step: {state}")

        core_messages = []

        response = state.get("response")
        if not response:
            # a response is required
            raise ValueError("No response provided to slack poster")
        
        logger.info(f"response: {response}")

        prompt = self.prompt_template.format(
            messages=[response]
        )

        logger.info(f"prompt: {prompt}")
        
        core_messages.append(("system", prompt))
        core_messages.append(("system", "always finish after posting the message"))
        core_messages.append(("system", "if the resonse is a full plan, post the full plan"))
        core_messages.append(("system", "always use the #bitbot-testing channel"))


        logger.info("")
        logger.info("")
        logger.info("====================================")
        logger.info(f"core_messages - after: {core_messages}")
        logger.info("====================================")

        
        agent_response = await self._runnable.ainvoke({
            "messages": core_messages
        })

        logger.debug(f"agent_response: {agent_response}")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("")

        return {
            "response": None
        }
