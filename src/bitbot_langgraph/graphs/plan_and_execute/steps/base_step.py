import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import Optional

class BaseStep:
    prompt_template = None

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def node(self):
        raise NotImplementedError("The node method must be implemented in the subclass.")