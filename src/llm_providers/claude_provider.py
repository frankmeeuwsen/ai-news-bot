"""
Claude Provider - Anthropic Claude API implementation
"""
import os
from typing import List, Dict, Any, Optional, Union
from anthropic import Anthropic
from .base_provider import BaseLLMProvider
from ..logger import setup_logger


logger = setup_logger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Claude LLM provider using Anthropic API"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Claude provider.
        
        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var
            model: Model name to use. If None, uses default model
            
        Raises:
            ValueError: If API key is not provided and not in environment
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key must be provided or set in ANTHROPIC_API_KEY environment variable"
            )
        
        super().__init__(api_key=api_key, model=model or self.default_model)
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Claude provider initialized with model: {self.model}")
    
    @property
    def provider_name(self) -> str:
        return "claude"
    
    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-5-20250929"
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        return_usage: bool = False,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate a response using Claude API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            return_usage: If True, return dict met text + usage data
            **kwargs: Additional Claude-specific parameters

        Returns:
            Generated text response, of dict met 'text' en 'usage' keys

        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug(f"Calling Claude API with {len(messages)} messages")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                **kwargs
            )

            # Extract text from response
            text = None
            for block in response.content:
                if block.type == "text":
                    text = block.text
                    break

            if text is None:
                raise Exception("No text response received from Claude")

            # Return met usage data als gevraagd
            if return_usage:
                usage = {
                    'prompt_tokens': response.usage.input_tokens if response.usage else 0,
                    'completion_tokens': response.usage.output_tokens if response.usage else 0,
                    'total_tokens': (
                        (response.usage.input_tokens + response.usage.output_tokens)
                        if response.usage else 0
                    ),
                }
                cost = self._calculate_cost(usage, self.model)

                return {
                    'text': text,
                    'usage': usage,
                    'cost': cost,
                    'model': self.model
                }

            return text

        except Exception as e:
            logger.error(f"Claude API error: {str(e)}", exc_info=True)
            raise

    def _calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """
        Bereken kosten op basis van Anthropic pricing.

        Claude Sonnet 4.5: $3/1M input, $15/1M output
        Claude Sonnet 3.5: $3/1M input, $15/1M output
        Claude Haiku 3.5:  $0.80/1M input, $4/1M output

        Args:
            usage: Dict met prompt_tokens en completion_tokens
            model: Model naam

        Returns:
            Geschatte kosten in dollars
        """
        # Pricing per 1M tokens (input, output)
        pricing = {
            'claude-sonnet-4-5-20250929': (3.0, 15.0),
            'claude-sonnet-4-20250514': (3.0, 15.0),
            'claude-haiku-4-5-20251001': (0.80, 4.0),
        }

        # Default naar Sonnet pricing als model onbekend is
        input_price, output_price = pricing.get(model, (3.0, 15.0))

        input_cost = (usage.get('prompt_tokens', 0) / 1_000_000) * input_price
        output_cost = (usage.get('completion_tokens', 0) / 1_000_000) * output_price

        return input_cost + output_cost
    
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
        Generate a response with tool calling support.
        
        Args:
            messages: List of message dicts
            tools: List of tool definitions in Claude format
            max_tokens: Maximum tokens in response
            max_iterations: Maximum tool use iterations
            tool_handler: Function to handle tool calls, signature: (tool_name, tool_input) -> str
            **kwargs: Additional Claude-specific parameters
            
        Returns:
            Generated text response after tool interactions
            
        Raises:
            Exception: If generation fails
        """
        try:
            logger.debug(f"Calling Claude API with tools, max_iterations={max_iterations}")
            
            response_text = None
            
            for iteration in range(max_iterations):
                # Call Claude API
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=messages,
                    tools=tools,
                    **kwargs
                )
                
                logger.debug(f"Iteration {iteration + 1}: stop_reason = {message.stop_reason}")
                
                # Check if we got a final response
                if message.stop_reason == "end_turn":
                    for block in message.content:
                        if block.type == "text":
                            response_text = block.text
                            break
                    break
                
                # Check if Claude wants to use a tool
                elif message.stop_reason == "tool_use":
                    # Add assistant's response to messages
                    messages.append({
                        "role": "assistant",
                        "content": message.content
                    })
                    
                    # Process tool calls
                    tool_results = []
                    for block in message.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_input = block.input
                            
                            logger.info(f"Tool call: {tool_name} with input: {tool_input}")
                            
                            # Execute the tool using the handler
                            if tool_handler:
                                result_text = tool_handler(tool_name, tool_input, block.id)
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result_text
                                })
                    
                    # Add tool results to messages
                    if tool_results:
                        messages.append({
                            "role": "user",
                            "content": tool_results
                        })
                    else:
                        break
                else:
                    # Unexpected stop reason
                    break
            
            # If we didn't get a response through the loop, extract from last message
            if response_text is None:
                for block in message.content:
                    if block.type == "text":
                        response_text = block.text
                        break
            
            if response_text is None:
                raise Exception("No text response received from Claude")
            
            logger.info("Claude generation with tools completed successfully")
            return response_text
            
        except Exception as e:
            logger.error(f"Claude API error with tools: {str(e)}", exc_info=True)
            raise
