"""
OpenAI Adapter for UAM Compliance Intelligence System.

AI analysis using OpenAI API via LangChain.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..interfaces.ports import OpenAIClient
from ..interfaces.errors import IntegrationError


class OpenAIAdapter(OpenAIClient):
    """
    OpenAI integration using LangChain.

    Example:
        openai = OpenAIAdapter(api_key="sk-...")
        analysis = openai.analyze("Analyze KPI spike...", max_tokens=500)
    """

    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=0.7
        )

    def analyze(self, prompt: str, max_tokens: int) -> str:
        """Generate AI analysis for prompt."""
        try:
            message = HumanMessage(content=prompt)
            response = self.client.invoke([message])
            return response.content
        except Exception as e:
            raise IntegrationError(
                message=f"OpenAI API call failed: {str(e)}",
                context={"model": self.model, "error": str(e)}
            )

    def get_token_count(self, text: str) -> int:
        """Estimate token count."""
        # Simple estimation: 4 chars per token
        return len(text) // 4


class MockOpenAIClient(OpenAIClient):
    """Mock OpenAI client for testing."""

    def __init__(self, response: str = "Mock analysis"):
        self.response = response
        self.calls = []

    def analyze(self, prompt: str, max_tokens: int) -> str:
        self.calls.append({"prompt": prompt, "max_tokens": max_tokens})
        return self.response

    def get_token_count(self, text: str) -> int:
        return len(text) // 4
