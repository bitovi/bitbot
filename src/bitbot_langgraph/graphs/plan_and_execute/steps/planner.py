from typing import List, Dict, Optional, TypedDict

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


planner_prompt_template_prefix = """
You are an advanced planning assistant specialized in creating and executing efficient, multi-step plans.

For the given objective, come up with a simple step-by-step plan. This plan should involve individual tasks, that if executed correctly, will yield the correct answer.

Rules to follow when making the plan:
---
1. Do not add any unnecessary or superfluous steps. You prefer fewer steps.
2. Only include steps that still NEED to be done.
3. Use a numbered list for the steps, starting at the next number in the sequence.
4. Make sure that each step has all the information needed - do not skip steps.
5. The result of the final step should be the final answer.
6. Ensure the penultimate step in the plan is one that makes it easy to conclude you are finished.
7. Do not return previously completed steps as part of the plan.
8. Once all steps are completed, respond directly with the final answer rather than generating a new plan.
9. If the final step is already in the past steps, conclude by providing a response, not a new plan.
10. Do not rework the original plan unless a step reveals new information that should change the plan.
11. Do not replan more than 2 times.
12. If you have a question for the user, use that as the response so they can provide the necessary information.
  - For example, if recent message says something like "Please confirm if ...", then respond instead of plan.

Once the plan is formed, guide the execution of each step, making adjustments as necessary to ensure success. Remember, the best plans are simple, efficient, and clear.
"""

class Model(BaseModel):
    """Plan to follow in future"""

    steps: Optional[List[str]] = Field(
        description="different steps to follow, should be in sorted order"
    )

class Step(BaseStep):
    Model = Model
    prompt_template = planner_prompt_template_prefix + """
    For your reference, the following steps have been completed:
    ---
    {past_steps}
    ---

    This is the original plan
    ---
    {original_plan}
    ---

    It's possible there is a previous response:
    ---
    {response}
    ---
    If there is a previous response, the following query is an answer to it.
    Accept it and get back on track with the next step of the original plan.
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
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"==============================")
        self.logger.info(f"==============================")
        self.logger.info(f"==============================")
        self.logger.info(f"==============================")
        self.logger.info(f"==============================")
        self.logger.info(f"Executing planner state")
        self.logger.debug(f"Executing step with state: {state}")

        self.logger.info(f"state: {state}")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"")
        self.logger.info(f"==============================")
        # messages = []
        # if "messages" in state:
        #     self.logger.info("messages found in state")
        #     messages = state["messages"]
        # else:
        #     self.logger.info("messages not found in state")

        query = ""
        if "input" in state:
            self.logger.info("input found in state")
            query = state["input"]
        else:
            self.logger.info("input not found in state")

        response = None
        if "response" in state:
            self.logger.info("response found in state")
            response = state["response"]    
        else:
            self.logger.info("response not found in state")

        # messages_human = [HumanMessage(content=message) for message in messages]
        query_human = [HumanMessage(content=query)]


        past_steps = get_past_steps_from_state(state, self.logger)
        

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
        self.logger.info(f"response: {response}")
        self.logger.info(f"original_plan: {original_plan}")

        input_data = {
            # "messages": messages_human,
            "query": query_human,
            "past_steps": past_steps,
            "response": response,
            "original_plan": original_plan
        }
        plan = await self._runnable.ainvoke(input_data)
        return {
            "plan": plan.steps,
            "original_plan": plan.steps,
            "response": None
        }

