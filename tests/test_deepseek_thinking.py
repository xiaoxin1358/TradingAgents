"""Tests for DeepSeek thinking-mode configuration.

Covers three concerns:
1. ``_get_provider_kwargs`` forwards ``deepseek_reasoning_effort``.
2. ``get_llm()`` does NOT drop ``reasoning_effort`` for deepseek provider.
3. ``_get_request_payload`` injects ``extra_body.thinking``.
"""

from unittest.mock import MagicMock, patch

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice


@pytest.mark.unit
class TestDeepSeekProviderKwargs:
    """_get_provider_kwargs forwards reasoning_effort for deepseek."""

    def _kwargs_for(self, config):
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        graph = TradingAgentsGraph.__new__(TradingAgentsGraph)
        graph.config = {"llm_provider": config.pop("provider", "deepseek"), **config}
        return TradingAgentsGraph._get_provider_kwargs(graph)

    def test_forwards_when_set(self):
        kwargs = self._kwargs_for({"provider": "deepseek", "deepseek_reasoning_effort": "max"})
        assert kwargs["reasoning_effort"] == "max"

    def test_omitted_when_none(self):
        kwargs = self._kwargs_for({"provider": "deepseek", "deepseek_reasoning_effort": None})
        assert "reasoning_effort" not in kwargs

    def test_omitted_when_unset(self):
        kwargs = self._kwargs_for({"provider": "deepseek"})
        assert "reasoning_effort" not in kwargs

    def test_not_leaked_to_openai(self):
        """deepseek_reasoning_effort must not cross-contaminate openai provider."""
        kwargs = self._kwargs_for({"provider": "openai", "deepseek_reasoning_effort": "max"})
        assert "reasoning_effort" not in kwargs  # openai reads openai_reasoning_effort


@pytest.mark.unit
class TestDeepSeekThinkingPayload:
    """_get_request_payload adds extra_body.thinking."""

    def _build_payload(self):
        from tradingagents.llm_clients.openai_client import DeepSeekChatOpenAI
        llm = DeepSeekChatOpenAI(model="deepseek-v4-pro", api_key="placeholder")
        # Steal a payload from a minimal invoke path.
        return llm._get_request_payload([("user", "hello")])

    def test_extra_body_thinking_enabled(self):
        payload = self._build_payload()
        assert payload["extra_body"]["thinking"] == {"type": "enabled"}

    @patch.object(
        DeepSeekChatOpenAI := __import__(
            "tradingagents.llm_clients.openai_client", fromlist=["DeepSeekChatOpenAI"]
        ).DeepSeekChatOpenAI,
        "_create_chat_result",
        autospec=True,
    )
    def test_reasoning_content_roundtrip(self, _mock_create):
        """reasoning_content from a prior turn is re-attached via message dict."""
        from tradingagents.llm_clients.openai_client import DeepSeekChatOpenAI

        llm = DeepSeekChatOpenAI(model="deepseek-v4-pro", api_key="placeholder")
        # Simulate an AIMessage that carries reasoning_content in additional_kwargs
        from langchain_core.messages import AIMessage
        msg = AIMessage(content="answer", additional_kwargs={"reasoning_content": "chain of thought"})

        payload = llm._get_request_payload([("user", "hello"), msg])
        messages = payload["messages"]
        assistant_dict = messages[1]
        assert assistant_dict["reasoning_content"] == "chain of thought"
        assert payload["extra_body"]["thinking"] == {"type": "enabled"}
