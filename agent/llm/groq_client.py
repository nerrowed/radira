"""Groq API client wrapper with retry mechanism and rate limiting."""

import os
import time
import json
import logging
from typing import Optional, Dict, Any, List, Generator
from datetime import datetime, timedelta
from collections import deque
from groq import Groq
from config.settings import settings

# Import custom exceptions
from agent.core.exceptions import (
    LLMAPIError,
    LLMTimeoutError,
    RateLimitError,
    TokenLimitExceededError,
    LLMResponseError
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding window rate limiter for API requests."""

    def __init__(self, max_requests: int, time_window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window
            time_window_seconds: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.time_window = timedelta(seconds=time_window_seconds)
        self.requests: deque = deque()  # Store request timestamps

    def acquire(self) -> bool:
        """Try to acquire a request slot.

        Returns:
            True if request is allowed, False if rate limited
        """
        now = datetime.now()

        # Remove old requests outside time window
        while self.requests and (now - self.requests[0]) > self.time_window:
            self.requests.popleft()

        # Check if we can make a new request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        return False

    def wait_time(self) -> float:
        """Get wait time in seconds until next request is allowed.

        Returns:
            Seconds to wait (0 if request is allowed now)
        """
        if len(self.requests) < self.max_requests:
            return 0.0

        # Calculate when oldest request will expire
        now = datetime.now()
        oldest = self.requests[0]
        expires_at = oldest + self.time_window
        wait_seconds = (expires_at - now).total_seconds()

        return max(0.0, wait_seconds)

    def reset(self):
        """Reset rate limiter."""
        self.requests.clear()


class GroqClient:
    """Wrapper for Groq API with retry mechanism, rate limiting, and better error handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        fast_model: Optional[str] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        timeout: Optional[int] = None,
        rate_limit_rpm: Optional[int] = None,
    ):
        """Initialize Groq client with retry and rate limiting.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            default_model: Default model to use
            fast_model: Fast model for simple tasks
            max_retries: Maximum retry attempts (defaults to settings)
            retry_delay: Initial retry delay in seconds (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            rate_limit_rpm: Rate limit in requests per minute (defaults to settings)
        """
        self.api_key = api_key or settings.groq_api_key
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY not set. Please set it in .env file or pass it to GroqClient."
            )

        self.client = Groq(api_key=self.api_key)
        self.default_model = default_model or settings.groq_model
        self.fast_model = fast_model or getattr(settings, 'groq_fast_model', 'gemma2-9b-it')

        # Retry configuration
        self.max_retries = max_retries if max_retries is not None else settings.api_max_retries
        self.retry_delay = retry_delay if retry_delay is not None else settings.api_retry_delay
        self.timeout = timeout if timeout is not None else settings.api_timeout_seconds

        # Rate limiting
        rate_limit = rate_limit_rpm if rate_limit_rpm is not None else settings.rate_limit_requests_per_minute
        self.rate_limiter = RateLimiter(max_requests=rate_limit, time_window_seconds=60)

        # Token tracking
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

        # Statistics
        self.total_requests = 0
        self.failed_requests = 0
        self.retried_requests = 0

        logger.info(
            f"GroqClient initialized - Model: {self.default_model}, "
            f"Max Retries: {self.max_retries}, Timeout: {self.timeout}s, "
            f"Rate Limit: {rate_limit} req/min"
        )

    def _execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Function result

        Raises:
            LLMAPIError: If all retries failed
            RateLimitError: If rate limited
            LLMTimeoutError: If request timed out
        """
        last_exception = None
        retry_count = 0

        while retry_count <= self.max_retries:
            try:
                # Check rate limit
                if not self.rate_limiter.acquire():
                    wait_time = self.rate_limiter.wait_time()
                    logger.warning(
                        f"Rate limit reached. Waiting {wait_time:.2f}s before retry..."
                    )
                    raise RateLimitError(
                        f"Rate limit exceeded. Wait {wait_time:.2f}s",
                        retry_after=int(wait_time) + 1
                    )

                # Execute the function
                self.total_requests += 1
                result = func(*args, **kwargs)

                # Log retry success if this was a retry
                if retry_count > 0:
                    logger.info(f"Request succeeded after {retry_count} retries")

                return result

            except RateLimitError:
                # Don't retry rate limit errors, just raise
                raise

            except Exception as e:
                last_exception = e
                self.failed_requests += 1

                # Check if error is retryable
                is_timeout = "timeout" in str(e).lower()
                is_network = any(
                    keyword in str(e).lower()
                    for keyword in ["connection", "network", "unavailable"]
                )
                is_retryable = is_timeout or is_network

                if not is_retryable or retry_count >= self.max_retries:
                    # Not retryable or max retries reached
                    logger.error(
                        f"Request failed: {e} (retries: {retry_count}/{self.max_retries})"
                    )

                    # Wrap in appropriate exception
                    if is_timeout:
                        raise LLMTimeoutError(
                            f"Request timed out after {self.timeout}s",
                            details={"original_error": str(e)}
                        ) from e
                    else:
                        raise LLMAPIError(
                            f"Groq API error: {str(e)}",
                            details={"retry_count": retry_count}
                        ) from e

                # Calculate exponential backoff delay
                delay = self.retry_delay * (2 ** retry_count)
                logger.warning(
                    f"Request failed: {e}. Retrying in {delay:.2f}s... "
                    f"(attempt {retry_count + 1}/{self.max_retries})"
                )

                time.sleep(delay)
                retry_count += 1
                self.retried_requests += 1

        # Should not reach here, but just in case
        raise LLMAPIError(
            f"Request failed after {retry_count} retries",
            details={"last_error": str(last_exception)}
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat completion request to Groq API with retry.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            **kwargs: Additional arguments to pass to API

        Returns:
            Response dict with 'content', 'usage', etc.

        Raises:
            LLMAPIError: If API call fails
            LLMTimeoutError: If request times out
            RateLimitError: If rate limited
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

            def _make_request():
                """Inner function for retry wrapper."""
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout,
                    **kwargs
                )
                return response

            # Execute with retry
            response = self._execute_with_retry(_make_request)

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

        except (LLMAPIError, LLMTimeoutError, RateLimitError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            raise LLMAPIError(f"Unexpected error in chat: {str(e)}") from e

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
            def _make_stream():
                """Inner function for creating stream."""
                return self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    timeout=self.timeout,
                    **kwargs
                )

            stream = self._execute_with_retry(_make_stream)

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except (LLMAPIError, LLMTimeoutError, RateLimitError):
            raise
        except Exception as e:
            raise LLMAPIError(f"Streaming error: {str(e)}") from e

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

    def chat_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tool_choice: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with function calling support (Claude-like) with retry.

        Args:
            messages: List of message dicts with 'role' and 'content'
            functions: List of function definitions (OpenAI format)
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            tool_choice: "auto", "required", or "none"
            **kwargs: Additional arguments

        Returns:
            Response dict with:
            - content: Text response (if any)
            - tool_calls: List of tool calls (if any)
            - usage: Token usage stats
            - finish_reason: Why generation stopped
            - failed_generation: If tool_use_failed, contains the partial text response

        Raises:
            LLMAPIError: If API call fails
            LLMResponseError: If response parsing fails
        """
        model = model or self.default_model

        try:
            # Convert function definitions to Groq tools format
            tools = functions  # Groq uses same format as OpenAI

            # Prepare API call parameters
            api_params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tools": tools,
                "timeout": self.timeout,
            }

            # Add tool_choice if specified
            if tool_choice != "auto":
                api_params["tool_choice"] = tool_choice

            # Add any extra kwargs
            api_params.update(kwargs)

            def _make_request():
                """Inner function for retry wrapper."""
                return self.client.chat.completions.create(**api_params)

            # Execute with retry
            response = self._execute_with_retry(_make_request)

            # Track token usage
            usage = response.usage
            self.prompt_tokens += usage.prompt_tokens
            self.completion_tokens += usage.completion_tokens
            self.total_tokens += usage.total_tokens

            message = response.choices[0].message

            # Parse response
            result = {
                "content": message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                "finish_reason": response.choices[0].finish_reason,
                "tool_calls": None
            }

            # Extract tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments  # JSON string
                        }
                    })
                result["tool_calls"] = tool_calls

            return result

        except (LLMAPIError, LLMTimeoutError, RateLimitError):
            raise
        except Exception as e:
            # Special handling for tool_use_failed error
            error_str = str(e)
            if "tool_use_failed" in error_str and "failed_generation" in error_str:
                logger.warning(f"Tool use failed, LLM generated text instead of calling function")

                # Try to extract failed_generation content from error
                try:
                    import re
                    import json as json_module

                    # Try to extract as JSON first
                    # Look for the error dict in the string
                    json_match = re.search(r'\{[^}]*"error":\s*\{[^}]*"failed_generation":', error_str)
                    if json_match:
                        # Try to find complete JSON object
                        start_idx = error_str.find("{'error':")
                        if start_idx == -1:
                            start_idx = error_str.find('{"error":')

                        if start_idx != -1:
                            # Find matching brace
                            brace_count = 0
                            end_idx = start_idx
                            for i in range(start_idx, len(error_str)):
                                if error_str[i] == '{':
                                    brace_count += 1
                                elif error_str[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end_idx = i + 1
                                        break

                            if end_idx > start_idx:
                                try:
                                    # Try to parse as JSON
                                    json_str = error_str[start_idx:end_idx].replace("'", '"')
                                    error_dict = json_module.loads(json_str)
                                    failed_content = error_dict.get('error', {}).get('failed_generation', '')

                                    if failed_content:
                                        logger.info(f"Extracted failed_generation via JSON ({len(failed_content)} chars)")
                                        return {
                                            "content": failed_content,
                                            "model": model,
                                            "usage": {
                                                "prompt_tokens": 0,
                                                "completion_tokens": 0,
                                                "total_tokens": 0,
                                            },
                                            "finish_reason": "tool_use_failed",
                                            "tool_calls": None,
                                            "failed_generation": True
                                        }
                                except json_module.JSONDecodeError:
                                    pass

                    # Fallback: regex extraction
                    match = re.search(r"'failed_generation':\s*'([^']+(?:\\'[^']*)*)'", error_str)
                    if not match:
                        match = re.search(r'"failed_generation":\s*"([^"]+(?:\\"[^"]*)*)"', error_str)

                    if match:
                        failed_content = match.group(1)
                        # Unescape newlines and quotes
                        failed_content = failed_content.replace('\\n', '\n').replace("\\'", "'").replace('\\"', '"')

                        logger.info(f"Extracted failed_generation via regex ({len(failed_content)} chars)")
                        return {
                            "content": failed_content,
                            "model": model,
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                            },
                            "finish_reason": "tool_use_failed",
                            "tool_calls": None,
                            "failed_generation": True
                        }
                except Exception as parse_error:
                    logger.warning(f"Failed to parse failed_generation: {parse_error}")

            raise LLMAPIError(f"Function calling error: {str(e)}") from e

    def parse_function_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Parse function call from tool_calls response.

        Args:
            tool_call: Single tool call dict from response

        Returns:
            Dict with:
            - function_name: Name of function to call
            - arguments: Parsed arguments dict
            - call_id: Tool call ID for response

        Raises:
            LLMResponseError: If parsing fails
        """
        try:
            function_name = tool_call["function"]["name"]
            arguments_str = tool_call["function"]["arguments"]

            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse function arguments: {e}")
                # Fallback: return raw string
                arguments = {"raw": arguments_str}

            return {
                "function_name": function_name,
                "arguments": arguments,
                "call_id": tool_call["id"]
            }

        except KeyError as e:
            raise LLMResponseError(
                f"Invalid tool call format: missing key {e}",
                details={"tool_call": tool_call}
            )

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

    def get_request_stats(self) -> Dict[str, int]:
        """Get request statistics.

        Returns:
            Dict with request counts and success rate
        """
        success_rate = (
            (self.total_requests - self.failed_requests) / self.total_requests * 100
            if self.total_requests > 0 else 0.0
        )

        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "retried_requests": self.retried_requests,
            "success_rate": success_rate,
        }

    def reset_token_stats(self):
        """Reset token usage counters."""
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    def reset_request_stats(self):
        """Reset request statistics."""
        self.total_requests = 0
        self.failed_requests = 0
        self.retried_requests = 0

    @staticmethod
    def count_tokens_estimate(text: str) -> int:
        """Rough estimate of token count.

        Note: This is a simple heuristic. For accurate counting,
        use tiktoken library with the appropriate model tokenizer.

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
        except Exception as e:
            logger.warning(f"Groq API availability check failed: {e}")
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
