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


class Model(BaseModel):
    """Plan to follow in future"""

    final_markdown: str = Field(
        description="markdown file content that cleanly formats the steps for use by the user"
    )

class Step(BaseStep):
    Model = Model
    prompt_template = """
    Convert these steps into richly formatted slack markdown. 
    start with a quick summary at the beginning along with any relevant context for the user (from past steps, for example).
    Then provide the markdown to convey the response/question.
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

    here are some rules to follow when generating markdown:
    ---
    1. *Bold*: Use `*` around text (e.g., `*bold*`).
    2. _Italic_: Use `_` around text (e.g., `_italic_`).
    3. ~Strikethrough~: Use `~` around text (e.g., `~strikethrough~`).
    4. `Code`: Use backticks `` ` `` around inline code or triple backticks for code blocks (e.g., `` `code` ``).
    5. Lists:
    - Unordered: Use `-` or `*` for bullet points (e.g., `-` - no space before).
    - Ordered: Use numbers followed by a period (e.g., `1.` - no space before).
    6. <https://example.com|Links>: Format as `<URL|Link Text>`.

    **Header Limitations:**
    - Slack does not support headers. Use bold or asterisks for emphasis.

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

        query_human = [HumanMessage(content=query)]
        past_steps = get_past_steps_from_state(state, self.logger)

        original_plan = []
        if "original_plan" in state:
            self.logger.info("original_plan found in state")
            original_plan = state["original_plan"]
        else:
            self.logger.info("original_plan not found in state")


        # self.logger.info(f"query: {query}")
        # self.logger.info(f"query_human: {query_human}")
        # self.logger.info(f"past_steps: {past_steps}")
        # self.logger.info(f"response: {response}")
        # self.logger.info(f"original_plan: {original_plan}")

        input_data = {
            "query": query_human,
            "past_steps": past_steps,
            "response": response,
            "original_plan": original_plan
        }
        output = await self._runnable.ainvoke(input_data)

        self.logger.info(f"response_formatter output: {output}")
        return {
            "final_markdown": output.final_markdown
        }

