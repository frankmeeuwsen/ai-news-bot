"""
OpenRouter Provider - OpenRouter API implementation using OpenAI-compatible interface
"""
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .base_provider import BaseLLMProvider
from ..logger import setup_logger


logger = setup_logger(__name__)


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter LLM provider using OpenAI-compatible API"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key. If None, reads from OPENROUTER_API_KEY env var
            model: Model name to use. If None, uses default model

        Raises:
            ValueError: If API key is not provided and not in environment
        """
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenRouter API key must be provided or set in OPENROUTER_API_KEY environment variable"
            )

        super().__init__(api_key=api_key, model=model or self.default_model)

        # Initialize OpenAI client with OpenRouter base URL
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        logger.info(f"OpenRouter provider initialized with model: {self.model}")

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def default_model(self) -> str:
        return "anthropic/claude-sonnet-4.5"

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        return_usage: bool = False,
        **kwargs
    ) -> str | Dict[str, Any]:
        """
        Generate a response using OpenRouter API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            return_usage: If True, return dict met text + usage data
            **kwargs: Additional OpenRouter-specific parameters

        Returns:
            Generated text response, of dict met 'text' en 'usage' keys

        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug(f"Calling OpenRouter API with {len(messages)} messages")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # Extract text from response
            if not response.choices or len(response.choices) == 0:
                raise Exception("No response received from OpenRouter")

            text = response.choices[0].message.content

            # Return with usage data als gevraagd
            if return_usage:
                usage = {
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0,
                }

                # OpenRouter specific: calculate cost based on model pricing
                # Note: Echte cost data komt van OpenRouter headers, maar die zijn niet
                # altijd beschikbaar in responses. We schatten op basis van tokens.
                cost = self._estimate_cost(usage['total_tokens'])

                return {
                    'text': text,
                    'usage': usage,
                    'cost': cost,
                    'model': self.model
                }

            return text

        except Exception as e:
            logger.error(f"OpenRouter API error: {str(e)}", exc_info=True)
            raise

    def _estimate_cost(self, total_tokens: int) -> float:
        """
        Estimate cost based on tokens.

        OpenRouter pricing varies per model. Voor Claude Sonnet 4.5:
        - Input: $3.00 / 1M tokens
        - Output: $15.00 / 1M tokens

        We gebruiken gemiddelde van $9 / 1M voor simpele schatting.

        Args:
            total_tokens: Total token count

        Returns:
            Estimated cost in dollars
        """
        # Gemiddelde cost per 1M tokens (rough estimate)
        cost_per_million = 9.0

        return (total_tokens / 1_000_000) * cost_per_million

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        max_tokens: int = 2000,
        max_iterations: int = 8,
        tool_handler: Optional[callable] = None,
        **kwargs
    ) -> str:
        """
        Generate a response with tool calling support using OpenAI format.

        Args:
            messages: List of message dicts
            tools: List of tool definitions in OpenAI format
            max_tokens: Maximum tokens in response
            max_iterations: Maximum tool use iterations
            tool_handler: Function to handle tool calls, signature: (tool_name, tool_input, tool_call_id) -> str
            **kwargs: Additional OpenRouter-specific parameters

        Returns:
            Generated text response after tool interactions

        Raises:
            Exception: If generation fails
        """
        try:
            logger.debug(f"Calling OpenRouter API with tools, max_iterations={max_iterations}")

            response_text = None

            for iteration in range(max_iterations):
                # Call OpenRouter API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    max_tokens=max_tokens,
                    **kwargs
                )

                message = response.choices[0].message
                finish_reason = response.choices[0].finish_reason

                logger.debug(f"Iteration {iteration + 1}: finish_reason = {finish_reason}")

                # Check if we got a final response
                if finish_reason == "stop" or not message.tool_calls:
                    response_text = message.content
                    break

                # Check if model wants to use tools
                elif finish_reason == "tool_calls" or message.tool_calls:
                    # Add assistant's message to history
                    messages.append({
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in message.tool_calls
                        ]
                    })

                    # Process tool calls
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        # Parse arguments (they come as JSON string)
                        import json
                        tool_input = json.loads(tool_call.function.arguments)

                        logger.info(f"Tool call: {tool_name} with input: {tool_input}")

                        # Execute the tool using the handler
                        if tool_handler:
                            result_text = tool_handler(tool_name, tool_input, tool_call.id)

                            # Add tool result to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_name,
                                "content": result_text
                            })
                else:
                    # Unexpected finish reason
                    break

            if response_text is None:
                raise Exception("No text response received from OpenRouter")

            logger.info("OpenRouter generation with tools completed successfully")
            return response_text

        except Exception as e:
            logger.error(f"OpenRouter API error with tools: {str(e)}", exc_info=True)
            raise

    def convert_claude_tools_to_openai_format(self, claude_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert Claude tool definitions to OpenAI format.

        Args:
            claude_tools: List of tool definitions in Claude format

        Returns:
            List of tool definitions in OpenAI format
        """
        openai_tools = []

        for tool in claude_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "parameters": tool.get("input_schema", {})
                }
            }
            openai_tools.append(openai_tool)

        return openai_tools
