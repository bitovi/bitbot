from typing import List, Optional, Union
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep
from bitbot_langgraph.graphs.plan_and_execute.steps.planner import planner_prompt_template_prefix

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)


class Response(BaseModel):
    """Response to user."""
    response: str

class Plan(BaseModel):
    """Plan to follow in the future."""
    steps: List[str] = Field(
        description="Different steps to follow, should be in sorted order."
    )

class Model(BaseModel):
    """Action to perform."""
    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
                    "If you need information from the user, use Response."
                    "If you need to further use tools to get the answer, use Plan."
    )


class Step(BaseStep):
    Model = Model
    prompt_template = planner_prompt_template_prefix + """

    ---

    Your objective was this:
    ---
    {input}
    ---

    Your original plan was this:
    ---
    {original_plan}
    ---

    Your most recent plan was:
    ---
    {plan}
    ---

    You have currently done the following steps:
    ---
    {past_steps}
    ---
    Update your plan accordingly.
    If no more steps are needed and you can return to the user, then provide a final response.
    if you need to ask the user a question, use that as the response instead of providing steps so they can provide the necessary information.
    Otherwise, fill out the plan.
    """

    def __init__(self, logger: Optional[logging.Logger] = None, prompt_template: str = None, model_name: str = "gpt-4o-mini"):
        super().__init__(logger)
        self.prompt_template = prompt_template or self.prompt_template
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)
        self._runnable = self.prompt | ChatOpenAI(model=model_name, temperature=0).with_structured_output(self.Model)

    async def node(self, state: dict):
        self.logger.info(f"replan step")
        output = await self._runnable.ainvoke(state)

        self.logger.debug("replan output: ", output)
        if isinstance(output.action, Response):
            return {"response": output.action.response}
        else:
            return {"plan": output.action.steps}