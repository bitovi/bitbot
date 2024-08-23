from typing import List, Dict, Optional, TypedDict

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)



class Model(BaseModel):
    """Plan to follow in future"""

    steps: Optional[List[str]] = Field(
        description="different steps to follow, should be in sorted order"
    )

class Step(BaseStep):
    Model = Model
    prompt_template = """
    You are an advanced planning assistant specialized in creating and executing multi-step plans.
    For the given objective, come up with a simple step by step plan.

    This plan should involve individual tasks, that if executed correctly will yield the correct answer.
    Once a plan is formed, you will guide the execution of each step, making adjustments as necessary to ensure success.
    The result of the final step should be the final answer. 
    You understand that not all plans need to have a lot of steps, and that the best plans are simple and efficient.
    Do not add any superfluous steps.
    Make sure that each step has all the information needed - do not skip steps.
"""

    def __init__(self, logger: Optional[logging.Logger] = None, prompt_template: str = None, model_name: str = "gpt-4o"):
        super().__init__(logger)
        self.prompt_template = prompt_template or self.prompt_template
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                self.prompt_template
            ),
            ("placeholder", "{messages}"),
        ])
        self._runnable = self.prompt | ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(self.Model)


    async def node(self, state: dict):
        self.logger.info(f"Executing step")
        self.logger.debug(f"state: {state}")
        plan = await self._runnable.ainvoke({"messages": [("user", state["input"])]})
        return {"plan": plan.steps}

