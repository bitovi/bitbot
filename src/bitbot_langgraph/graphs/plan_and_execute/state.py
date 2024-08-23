import operator
from typing import Annotated, List, TypedDict, Dict, Tuple, Optional

class State(TypedDict):
    input: str
    plan: List[str]
    original_plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: Optional[str]