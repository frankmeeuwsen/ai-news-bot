"""
LLM Providers Module - Abstracts different LLM API providers

Providers are imported lazily to avoid requiring all dependencies.
"""
from .base_provider import BaseLLMProvider


def get_llm_provider(provider_name: str, **kwargs) -> BaseLLMProvider:
    """
    Factory function to get the appropriate LLM provider.

    Args:
        provider_name: Name of the provider ('claude', 'deepseek', 'gemini', 'grok', 'openai', or 'openrouter')
        **kwargs: Additional arguments passed to the provider constructor

    Returns:
        An instance of the requested LLM provider

    Raises:
        ValueError: If provider_name is not recognized
    """
    provider_name = provider_name.lower()

    # Lazy imports - only load the provider that's needed
    if provider_name == 'claude':
        from .claude_provider import ClaudeProvider
        return ClaudeProvider(**kwargs)
    elif provider_name == 'deepseek':
        from .deepseek_provider import DeepSeekProvider
        return DeepSeekProvider(**kwargs)
    elif provider_name == 'gemini':
        from .gemini_provider import GeminiProvider
        return GeminiProvider(**kwargs)
    elif provider_name == 'grok':
        from .grok_provider import GrokProvider
        return GrokProvider(**kwargs)
    elif provider_name == 'openai':
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(**kwargs)
    elif provider_name == 'openrouter':
        from .openrouter_provider import OpenRouterProvider
        return OpenRouterProvider(**kwargs)
    else:
        available = ['claude', 'deepseek', 'gemini', 'grok', 'openai', 'openrouter']
        raise ValueError(
            f"Unknown LLM provider: {provider_name}. "
            f"Available providers: {', '.join(available)}"
        )


__all__ = [
    'BaseLLMProvider',
    'get_llm_provider',
]
