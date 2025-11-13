"""Custom function tools for AI agent.

These are example functions that can be invoked by the AI agent
during reasoning and task execution.
"""

import logging
import requests
from typing import Dict, Any, Optional
from agent.tools.base import BaseTool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class BitcoinPriceTool(BaseTool):
    """Tool to get current Bitcoin price from CoinDesk API."""

    def __init__(self):
        super().__init__(
            name="get_bitcoin_price",
            description="Get current Bitcoin price in USD from CoinDesk API. No parameters needed.",
            parameters={},
            is_dangerous=False
        )

    def _execute(self, **kwargs) -> ToolResult:
        """Execute Bitcoin price retrieval.

        Returns:
            ToolResult with Bitcoin price
        """
        try:
            logger.info("[ACTION] Fetching Bitcoin price from CoinDesk API...")

            response = requests.get(
                "https://api.coindesk.com/v1/bpi/currentprice.json",
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            price = data["bpi"]["USD"]["rate"]
            rate_float = data["bpi"]["USD"]["rate_float"]

            result = {
                "price": price,
                "price_float": rate_float,
                "currency": "USD",
                "source": "CoinDesk",
                "disclaimer": data.get("disclaimer", "")
            }

            logger.info(f"[ACTION] Bitcoin price retrieved: ${price}")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=f"Bitcoin (BTC) price: ${price} USD (${rate_float:,.2f})",
                metadata=result
            )

        except requests.RequestException as e:
            logger.error(f"[ACTION] Failed to fetch Bitcoin price: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Failed to fetch Bitcoin price: {str(e)}"
            )

        except (KeyError, ValueError) as e:
            logger.error(f"[ACTION] Invalid response format: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Invalid API response format: {str(e)}"
            )


class WeatherTool(BaseTool):
    """Tool to get weather information (example - requires API key)."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(
            name="get_weather",
            description="Get current weather for a city. Parameters: city (string)",
            parameters={
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'Jakarta', 'London')",
                    "required": True
                }
            },
            is_dangerous=False
        )
        self.api_key = api_key

    def _execute(self, city: str, **kwargs) -> ToolResult:
        """Execute weather retrieval.

        Args:
            city: City name

        Returns:
            ToolResult with weather information
        """
        logger.info(f"[ACTION] Getting weather for {city}...")

        if not self.api_key:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="Weather API key not configured. This is a demo tool."
            )

        # This is a placeholder - in real implementation, call actual weather API
        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"Weather tool is available but requires API key configuration for {city}. This is a demo placeholder."
        )


class CalculatorTool(BaseTool):
    """Tool for mathematical calculations."""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations. Parameters: expression (string)",
            parameters={
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')",
                    "required": True
                }
            },
            is_dangerous=False
        )

    def _execute(self, expression: str, **kwargs) -> ToolResult:
        """Execute calculation.

        Args:
            expression: Mathematical expression

        Returns:
            ToolResult with calculation result
        """
        try:
            logger.info(f"[ACTION] Calculating: {expression}")

            # Safe evaluation (only allow numbers and basic operators)
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="Invalid expression. Only numbers and basic operators (+, -, *, /, parentheses) allowed."
                )

            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, {})

            logger.info(f"[ACTION] Calculation result: {expression} = {result}")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=f"{expression} = {result}",
                metadata={"expression": expression, "result": result}
            )

        except Exception as e:
            logger.error(f"[ACTION] Calculation error: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Calculation error: {str(e)}"
            )


class TimeTool(BaseTool):
    """Tool to get current time and date."""

    def __init__(self):
        super().__init__(
            name="get_current_time",
            description="Get current date and time. No parameters needed.",
            parameters={},
            is_dangerous=False
        )

    def _execute(self, **kwargs) -> ToolResult:
        """Execute time retrieval.

        Returns:
            ToolResult with current time
        """
        from datetime import datetime
        import pytz

        try:
            logger.info("[ACTION] Getting current time...")

            # UTC time
            utc_now = datetime.now(pytz.UTC)

            # Jakarta time (WIB)
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            jakarta_time = utc_now.astimezone(jakarta_tz)

            result = {
                "utc": utc_now.isoformat(),
                "jakarta": jakarta_time.isoformat(),
                "jakarta_formatted": jakarta_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                "day_of_week": jakarta_time.strftime("%A"),
                "timestamp": utc_now.timestamp()
            }

            logger.info(f"[ACTION] Current time: {result['jakarta_formatted']}")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=f"Current time (Jakarta/WIB): {result['jakarta_formatted']} ({result['day_of_week']})",
                metadata=result
            )

        except Exception as e:
            logger.error(f"[ACTION] Time retrieval error: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Failed to get current time: {str(e)}"
            )


class HttpRequestTool(BaseTool):
    """Tool to make HTTP GET requests."""

    def __init__(self):
        super().__init__(
            name="http_get",
            description="Make HTTP GET request to a URL. Parameters: url (string)",
            parameters={
                "url": {
                    "type": "string",
                    "description": "URL to fetch",
                    "required": True
                }
            },
            is_dangerous=True  # Can access external resources
        )

    def _execute(self, url: str, **kwargs) -> ToolResult:
        """Execute HTTP GET request.

        Args:
            url: URL to fetch

        Returns:
            ToolResult with response
        """
        try:
            logger.info(f"[ACTION] Making HTTP GET request to: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Limit response size
            content = response.text[:5000]  # First 5000 chars
            truncated = len(response.text) > 5000

            result = {
                "status_code": response.status_code,
                "content_length": len(response.text),
                "content_type": response.headers.get("Content-Type", ""),
                "truncated": truncated
            }

            output = f"HTTP GET {url}\n"
            output += f"Status: {response.status_code}\n"
            output += f"Content-Type: {result['content_type']}\n"
            output += f"Length: {result['content_length']} bytes\n"
            if truncated:
                output += f"\nContent (truncated to 5000 chars):\n{content}..."
            else:
                output += f"\nContent:\n{content}"

            logger.info(f"[ACTION] HTTP request successful: {response.status_code}")

            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=output,
                metadata=result
            )

        except requests.RequestException as e:
            logger.error(f"[ACTION] HTTP request failed: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"HTTP request failed: {str(e)}"
            )


def register_custom_tools(registry):
    """Register all custom function tools to the registry.

    Args:
        registry: ToolRegistry instance
    """
    logger.info("Registering custom function tools...")

    # Register tools
    tools_to_register = [
        BitcoinPriceTool(),
        WeatherTool(),
        CalculatorTool(),
        TimeTool(),
        HttpRequestTool()
    ]

    for tool in tools_to_register:
        registry.register(tool)
        logger.info(f"  ✓ Registered: {tool.name}")

    logger.info(f"Registered {len(tools_to_register)} custom function tools")
