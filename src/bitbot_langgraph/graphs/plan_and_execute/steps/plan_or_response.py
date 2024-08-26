from typing import List, Dict, Optional, TypedDict, Literal

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep
from bitbot_langgraph.graphs.plan_and_execute.utilities import get_past_steps_from_state

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

class Model(BaseModel):
    """Plan to follow in future"""
    next: Literal['plan', 'respond']

class Step(BaseStep):
    Model = Model
    prompt_template = """
    If the following message seems like a question or a response, then answer "respond". otherwise, answer "plan".
    If the message seems like a conclusion, then answer "respond".
    erro on the side of "respond" if you are unsure.
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

