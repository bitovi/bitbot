from typing import List, Dict, Optional, TypedDict

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from bitbot_langgraph.graphs.plan_and_execute.steps.base_step import BaseStep

# set up logging
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)


class Model(BaseModel):
    """Plan to follow in future"""

    final_markdown: str = Field(
        description="markdown file content that cleanly formats the steps for use by the user"
    )

class Step(BaseStep):
    Model = Model
    prompt_template = """
    Convert these steps into a clean markdown file.  Each step should have a meaningful section title.
    ---
    {past_steps}
    ---

    Here's some context:

    This is the original plan
    ---
    {original_plan}
    ---

    This is the response.
    ---
    {response}
    ---
    this was the most recent query
    ---
    {query}
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
        query = ""
        if "input" in state:
            self.logger.info("input found in state")
            query = state["input"]
        else:
            self.logger.info("input not found in state")

        response = None
        if "response" in state or "Response" in state:
            self.logger.info("response found in state")
            response = state["response"]
            if response is None:
                response = state["Response"]
        else:
            self.logger.info("response not found in state")


        past_steps = []
        if "past_steps" in state:
            self.logger.info("past_steps found in state")
            past_steps = state["past_steps"]
        else:
            self.logger.info("past_steps not found in state")

        # messages_human = [HumanMessage(content=message) for message in messages]
        query_human = [HumanMessage(content=query)]

        # past steps is a list of tuples, so we need to convert them to HumanMessage objects
        past_steps_human = []
        for step in past_steps:
            # if the step is a tuple, concatenate the two strings
            # assume lists of 2 are tuples
            if isinstance(step, tuple) or (isinstance(step, list) and len(step) == 2):
                past_steps_human.append(HumanMessage(content=f"{step[0]}: {step[1]}"))
            elif isinstance(step, str):
                past_steps_human.append(HumanMessage(content=step))
            elif isinstance(step, dict):
                past_steps_human.append(HumanMessage(content=step["content"]))

        original_plan = []
        if "original_plan" in state:
            self.logger.info("original_plan found in state")
            original_plan = state["original_plan"]
        else:
            self.logger.info("original_plan not found in state")


        # self.logger.info(f"messages: {messages}")
        # self.logger.info(f"messages_human: {messages_human}")
        self.logger.info(f"query: {query}")
        self.logger.info(f"query_human: {query_human}")
        self.logger.info(f"past_steps: {past_steps}")
        self.logger.info(f"past_steps_human: {past_steps_human}")
        self.logger.info(f"response: {response}")
        self.logger.info(f"original_plan: {original_plan}")

        input_data = {
            # "messages": messages_human,
            "query": query_human,
            "past_steps": past_steps_human,
            "response": response,
            "original_plan": original_plan
        }
        output = await self._runnable.ainvoke(input_data)

        self.logger.info(f"response_formatter output: {output}")
        return {
            "final_markdown": output.final_markdown
        }

