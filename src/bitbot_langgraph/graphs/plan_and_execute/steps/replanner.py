from typing import List, Optional, Union
from langchain_core.pydantic_v1 import BaseModel, Field, root_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep
from bitbot_langgraph.graphs.plan_and_execute.steps.planner import planner_prompt_template_prefix

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)

class Model(BaseModel):
    steps: List[str] = Field(
        description="Different steps to follow, should be in sorted order."
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
    If no more steps are needed and you can add a final step to return to the user.
    if you need to ask the user a question, add a step to generate the question.
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

        self.logger.info("replan output: ", output)

        # if steps are present, return them as the plan
        if hasattr(output, "steps"):
            return {"plan": output.steps}
        # if no steps are present, return a step to notify the user
        return {"response": "No steps were provided. Please provide a plan."}
