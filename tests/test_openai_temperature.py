"""Tests for enforcing temperature compatibility with OpenAI models."""

from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.utils.openai import openai_completion
from src.utils.scoring import OpenAIDecodingArguments


def _fake_choice(content: str = "ok"):
    return SimpleNamespace(message=SimpleNamespace(content=content))


def _fake_response(content: str = "ok"):
    return SimpleNamespace(choices=[_fake_choice(content)])


@patch("src.utils.openai.openai.OpenAI")
def test_fixed_temperature_models_remove_custom_temperature(mock_client_factory):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response()
    mock_client_factory.return_value = mock_client

    result = openai_completion(
        "prompt",
        OpenAIDecodingArguments(temperature=0.4, max_tokens=10),
        model_name="gpt-5-mini",
        provider="openai",
    )

    assert result == "ok"
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "temperature" not in call_kwargs
    assert call_kwargs["model"] == "gpt-5-mini"


@patch("src.utils.openai.openai.OpenAI")
def test_supported_models_keep_configured_temperature(mock_client_factory):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _fake_response()
    mock_client_factory.return_value = mock_client

    openai_completion(
        "prompt",
        OpenAIDecodingArguments(temperature=0.4, max_tokens=10),
        model_name="gpt-4o",
        provider="openai",
    )

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["temperature"] == 0.4
    assert call_kwargs["model"] == "gpt-4o"
