import os
from typing import List, Dict, Optional, TypedDict, Literal

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from langchain_community.chat_models import ChatOllama
# from langchain_experimental.llms.ollama_functions import OllamaFunctions

from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep
from bitbot_langgraph.graphs.plan_and_execute.utilities import get_past_steps_from_state
from bitbot_langgraph.utilities.ollama_functions import OllamaFunctions

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)


OLLAMA_BASE_URL=os.environ.get("OLLAMA_BASE_URL", "http://localhost:8000")
LM_STUDIO_BASE_URL=os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_API_KEY=os.environ.get("LM_STUDIO_API_KEY")

class Model(BaseModel):
    """Plan to follow in future"""
    next: Literal['plan', 'respond']

class Step(BaseStep):
    Model = Model
    prompt_template = """
    If the following message seems like a question or a response, then answer "respond". otherwise, answer "plan".
    If the message seems like a conclusion, then answer "respond".
    err on the side of "respond" if you are unsure.
    only respond with "respond" or "plan".
    do not respond with anything else.
    ---
    {last_step}
    ---
    """

    def __init__(self, logger: Optional[logging.Logger] = None, prompt_template: str = None, model_name: str = "gpt-4o-mini"):
        super().__init__(logger)
        self.prompt_template = prompt_template or self.prompt_template
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                self.prompt_template
            )
        ])
        if model_name == "dwightfoster03/functionary-small-v3.1:latest":
            logger.info(f"using ollama model")
            try:
                # runnable_without_functions = self.prompt | ChatOllama(
                #     model=model_name, 
                #     temperature=0
                # )
                runnable_without_functions = OllamaFunctions(
                    model=model_name,
                    format="json",
                    temperature=0,
                    base_url=OLLAMA_BASE_URL,
                    keep_alive="8h"
                )
                logger.info(f"    - runnable without functions: {runnable_without_functions}")

                self._runnable = self.prompt | runnable_without_functions.with_structured_output(self.Model)
                logger.info(f"    - definition successful")
            except Exception as e:
                logger.error(f"    - error: {e}")
                raise e
            
        elif model_name == "lm_studio":
            logger.info(f"using lm_studio model")
            try:
                runnable_without_functions = ChatOpenAI(
                    model=model_name,
                    temperature=0,
                    base_url=LM_STUDIO_BASE_URL,
                    api_key=LM_STUDIO_API_KEY
                )
                logger.info(f"    - runnable without functions: {runnable_without_functions}")

                self._runnable = self.prompt | runnable_without_functions.with_structured_output(self.Model)
                logger.info(f"    - definition successful")
            except Exception as e:
                logger.error(f"    - error: {e}")
                raise e

        else:
            self._runnable = self.prompt | ChatOpenAI(model=model_name, temperature=0).with_structured_output(self.Model)


    async def node(self, state: dict):
        past_steps = get_past_steps_from_state(state, self.logger)
        last_step = past_steps[-1]

        output = await self._runnable.ainvoke({
            "last_step": last_step
        })

        # if we should respond next, add the last step to the 'response' key
        self.logger.info(f"plan or response output: {output}")
        if output.next == "respond":
            return {
                "response": last_step
            }

