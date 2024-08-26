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
from bitbot_langgraph.graphs.plan_and_execute.utilities import get_past_steps_from_state



# tools
from bitbot_langgraph.tools.search_sample import search
from bitbot_langgraph.tools.python_repl import python_repl
from bitbot_langgraph.tools.file_tools import create_outline, read_document, write_document, edit_document
from bitbot_langgraph.tools.scrape_webpages import scrape_webpages

# from langchain_community.tools import DuckDuckGoSearchRun, ShellTool, WikipediaQueryRun
# from langchain_community.agent_toolkits import FileManagementToolkit
# from langchain.agents import load_tools

from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults, WikipediaQueryRun

# # Setup working directory
# working_directory = "/app/docs_root"
# file_toolkit = FileManagementToolkit(root_dir=working_directory)
# file_tools = file_toolkit.get_tools()



duckduckgo_tool = DuckDuckGoSearchResults()
wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# shell_tool = ShellTool()
# input_tool = InputTool()
# directory_read_tool = DirectoryReadTool()
# directory_search_tool = DirectorySearchTool()
# code_interpreter_tool = CodeInterpreterTool()
# file_read_tool = FileReadTool()
# pdf_search_tool = PDFSearchTool()
# txt_search_tool = TXTSearchTool()
# csv_search_tool = CSVSearchTool()
# xml_search_tool = XMLSearchTool()
# json_search_tool = JSONSearchTool()
# file_append_tool = FileAppendTool()

research_tools = [scrape_webpages, duckduckgo_tool, wikipedia_tool]
file_tools = [create_outline, read_document, write_document, edit_document]
# all but the first item of tools
programmer_tools = [python_repl]


class Step(BaseStep):

    _prompt_template_intro_text = """
=============================== System Message ===============================

You are a precise and efficient execution assistant.
Your role is to follow detailed plans step by step, performing tasks accurately and effectively.
You should focus on executing each task as instructed, ensuring completion and reporting any issues or outcomes clearly.
Provide links if possible in your responses if you use tools to find information.
"""

    _prompt_template_past_steps_text = """
============================= Additional Context: The Following Steps Have Already Executed =============================
{past_steps}
"""

    _prompt_template_original_input = """
============================= Additional Context: Original Input =============================
{input}
"""

    _prompt_template_current_action = """
============================= Additional Context: step specifics =============================
for the following plan:
---
{plan}
---

You are tasked with executing step:
---
{step}
---
"""

    def __init__(self, logger: Optional[logging.Logger] = None, prompt_template: str = None, model_name: str = "gpt-4o-mini"):
        super().__init__(logger)
        logger.info("executor.py - make_step")

        if prompt_template is not None:
            self.prompt_template = prompt_template

        self.prompt_template_current_action = PromptTemplate.from_template(self._prompt_template_current_action)
        self.prompt_template_intro = PromptTemplate.from_template(self._prompt_template_intro_text)
        self.prompt_template_past_steps = PromptTemplate.from_template(self._prompt_template_past_steps_text)
        self.prompt_template_original_input = PromptTemplate.from_template(self._prompt_template_original_input)

        logger.info(f"executor prompt_template: {self.prompt_template}")
        llm = ChatOpenAI(model=model_name, temperature=0)
        self._runnable = create_react_agent(llm, research_tools, state_modifier=self.prompt_template)

    async def node(self, state: dict):
        logger = self.logger
        logger.info(f"execute executor step")
        logger.debug(f"execute step: {state}")

        core_messages = []

        # intro
        prompt_intro = self.prompt_template_intro.format()
        core_messages.append(("system", prompt_intro))


        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info("====================================")
        logger.info(f"core_messages - before: {core_messages}")
        logger.info("====================================")

        inputs_input = state.get("input")
        if not inputs_input:
            raise ValueError("No input provided to executor")
        else:
            logger.info(f"inputs_input: {inputs_input}")
            prompt_original_input = self.prompt_template_original_input.format(
                input=inputs_input
            )
            core_messages.append(("user", prompt_original_input))


        inputs_past_steps = state.get("past_steps", [])
        if not inputs_past_steps or len(inputs_past_steps) == 0:
            logger.debug("No past steps provided to executor")
        else:
            logger.debug(f"inputs_past_steps: {inputs_past_steps}")

            # append past steps to messages
            past_steps = get_past_steps_from_state(state, logger)
            logger.debug(f"past_steps_human: {past_steps}")
            prompt_past_steps = self.prompt_template_past_steps.format(
                past_steps=past_steps
            )
            core_messages.append(("user", prompt_past_steps))



        # todo: need original plan as context?
        # inputs_original_plan = state.get("originalplan")

        # todo: add input message to core messages?
        # if not input_messages:
        #     logger.info("No input messages provided to executor")
        # else:
        #     logger.info(f"input_messages: {input_messages}")
        #     # extend onto core messages
        #     core_messages.extend(input_messages)



        # final action, specify the current action based on the plan
        inputs_plan = state.get("plan")
        if not inputs_plan:
            # a plan's required
            raise ValueError("No plan provided to executor")
        else:
            logger.info(f"inputs_plan: {inputs_plan}")
            plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(inputs_plan))
            task = inputs_plan[0]
            prompt_current_action = self.prompt_template_current_action.format(
                plan=plan_str,
                step=f"{1}, {task}"
            )
            core_messages.append(("user", prompt_current_action))

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
            "past_steps": [(task, agent_response["messages"][-1].content)]
        }