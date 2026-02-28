"""
Tests voor Claude provider return_usage functionaliteit.

Test dat de provider correct usage data (tokens, kosten) teruggeeft
wanneer return_usage=True wordt meegegeven.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestClaudeProviderUsage:
    """Test Claude provider met return_usage parameter."""

    def _make_provider(self):
        """Maak ClaudeProvider met gemockte Anthropic client."""
        with patch('src.llm_providers.claude_provider.Anthropic') as MockAnthropic:
            mock_client = MagicMock()
            MockAnthropic.return_value = mock_client

            from src.llm_providers.claude_provider import ClaudeProvider
            provider = ClaudeProvider(api_key="test-key")

            return provider, mock_client

    def _mock_response(self, text="Hello", input_tokens=100, output_tokens=50):
        """Maak een mock Anthropic response."""
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = text

        mock_usage = MagicMock()
        mock_usage.input_tokens = input_tokens
        mock_usage.output_tokens = output_tokens

        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.usage = mock_usage

        return mock_response

    def test_generate_without_return_usage(self):
        """Standaard gedrag: return_usage=False geeft string terug."""
        provider, mock_client = self._make_provider()
        mock_client.messages.create.return_value = self._mock_response("Test output")

        result = provider.generate(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert isinstance(result, str)
        assert result == "Test output"

    def test_generate_with_return_usage(self):
        """Met return_usage=True: geeft dict terug met text, usage, cost, model."""
        provider, mock_client = self._make_provider()
        mock_client.messages.create.return_value = self._mock_response(
            text="Test output",
            input_tokens=500,
            output_tokens=200
        )

        result = provider.generate(
            messages=[{"role": "user", "content": "Hello"}],
            return_usage=True
        )

        assert isinstance(result, dict)
        assert result['text'] == "Test output"
        assert result['usage']['prompt_tokens'] == 500
        assert result['usage']['completion_tokens'] == 200
        assert result['usage']['total_tokens'] == 700
        assert result['model'] == "claude-sonnet-4-5-20250929"
        assert result['cost'] > 0  # Moet een positieve cost hebben

    def test_cost_calculation_sonnet(self):
        """Test kostenberekening voor Claude Sonnet model."""
        provider, mock_client = self._make_provider()
        mock_client.messages.create.return_value = self._mock_response(
            input_tokens=1_000_000,  # 1M input tokens
            output_tokens=1_000_000  # 1M output tokens
        )

        result = provider.generate(
            messages=[{"role": "user", "content": "Hello"}],
            return_usage=True
        )

        # Sonnet pricing: $3/1M input + $15/1M output = $18 totaal
        assert abs(result['cost'] - 18.0) < 0.01

    def test_cost_calculation_small_usage(self):
        """Test kostenberekening voor typisch gebruik (kleine aantallen)."""
        provider, mock_client = self._make_provider()
        mock_client.messages.create.return_value = self._mock_response(
            input_tokens=2000,   # Typisch Stage 1
            output_tokens=500
        )

        result = provider.generate(
            messages=[{"role": "user", "content": "Hello"}],
            return_usage=True
        )

        # 2000 input * $3/1M = $0.006, 500 output * $15/1M = $0.0075
        expected = (2000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(result['cost'] - expected) < 0.0001

    def test_usage_dict_has_all_keys(self):
        """Verify dat usage dict dezelfde keys heeft als OpenRouter provider."""
        provider, mock_client = self._make_provider()
        mock_client.messages.create.return_value = self._mock_response()

        result = provider.generate(
            messages=[{"role": "user", "content": "Hello"}],
            return_usage=True
        )

        # Zelfde keys als OpenRouter provider voor consistentie
        assert 'prompt_tokens' in result['usage']
        assert 'completion_tokens' in result['usage']
        assert 'total_tokens' in result['usage']
        assert 'text' in result
        assert 'cost' in result
        assert 'model' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
