from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class AgentState(TypedDict):
    """State for the agricultural AI agent."""

    messages: List[Any]
    user_id: Optional[int]
    session_id: Optional[str]
    context: Dict[str, Any]
    farm_data: Optional[Dict[str, Any]]


class MkulimaLLMService:
    """LLM service for Mkulima Smart agricultural assistance."""

    def __init__(self, config):
        self.config = config
        self.llm = self._initialize_llm()
        self.graph = self._build_agent_graph()
