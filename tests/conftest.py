import pytest
from agent.providers.base import BaseLLM
from agent.providers.models import LLMResponse, FinishReason

class DummyLLM(BaseLLM):
    def __init__(self, responses):
        self._responses = list(responses)

    def generate(self, conversation, tool_results=None):
        if not self._responses:
            return LLMResponse(text="Done", finish_reason=FinishReason.STOP)
        return self._responses.pop(0)

@pytest.fixture
def dummy_llm_factory():
    def _factory(responses):
        return DummyLLM(responses)
    return _factory
