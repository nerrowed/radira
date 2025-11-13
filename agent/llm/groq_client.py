"""Groq API client wrapper for LLM interactions."""

import os
import time
from typing import Optional, Dict, Any, List, Generator
from groq import Groq
from config.settings import settings


class GroqClient:
    """Wrapper for Groq API with support for multiple models and streaming."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        fast_model: Optional[str] = None,
    ):
        """Initialize Groq client.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            default_model: Default model to use (defaults to llama-3.1-70b-versatile)
            fast_model: Fast model for simple tasks (defaults to gemma2-9b-it)
        """
        self.api_key = api_key or settings.groq_api_key
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not set. Please set it in .env file or pass it to GroqClient."
            )

        self.client = Groq(api_key=self.api_key)
        self.default_model = default_model or settings.groq_model
        self.fast_model = fast_model or getattr(settings, 'groq_fast_model', 'gemma2-9b-it')

        # Token tracking
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request to Groq API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            **kwargs: Additional arguments to pass to API

        Returns:
            Response dict with 'content', 'usage', etc.
        """
        model = model or self.default_model

        try:
            if stream:
                return self._chat_stream(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            # Track token usage
            usage = response.usage
            self.prompt_tokens += usage.prompt_tokens
            self.completion_tokens += usage.completion_tokens
            self.total_tokens += usage.total_tokens

            return {
                "content": response.choices[0].message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason,
            }

        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}") from e

    def _chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Generator[str, None, None]:
        """Stream chat completion response.

        Yields:
            Content chunks as they arrive
        """
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise RuntimeError(f"Groq API streaming error: {str(e)}") from e

    def chat_with_system(
        self,
        user_message: str,
        system_prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convenience method for chat with system prompt.

        Args:
            user_message: User's message
            system_prompt: System instruction prompt
            model: Model to use
            **kwargs: Additional arguments

        Returns:
            Response dict
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.chat(messages=messages, model=model, **kwargs)

    def quick_chat(
        self,
        message: str,
        **kwargs
    ) -> str:
        """Quick chat using fast model, returns only content string.

        Args:
            message: User message
            **kwargs: Additional arguments

        Returns:
            Response content string
        """
        response = self.chat(
            messages=[{"role": "user", "content": message}],
            model=self.fast_model,
            **kwargs
        )
        return response["content"]

    def get_token_stats(self) -> Dict[str, int]:
        """Get cumulative token usage statistics.

        Returns:
            Dict with prompt, completion, and total token counts
        """
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }

    def reset_token_stats(self):
        """Reset token usage counters."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    @staticmethod
    def count_tokens_estimate(text: str) -> int:
        """Rough estimate of token count.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count (roughly 1 token per 4 characters)
        """
        return len(text) // 4

    def is_available(self) -> bool:
        """Check if Groq API is available.

        Returns:
            True if API is responsive
        """
        try:
            response = self.quick_chat("test", max_tokens=5)
            return True
        except Exception:
            return False


# Singleton instance for easy access
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get or create singleton GroqClient instance.

    Returns:
        GroqClient instance
    """
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
