"""OpenAI API utilities"""
import os
import logging
from typing import Optional
import openai

logger = logging.getLogger(__name__)


def _is_temperature_unsupported_error(error: Exception) -> bool:
    """Return True when the API rejects the temperature parameter."""
    body = getattr(error, "body", None)
    if isinstance(body, dict):
        details = body.get("error", {})
        if details.get("param") == "temperature" and details.get("code") == "unsupported_value":
            return True
        message = details.get("message", "")
        if "temperature" in message and "unsupported" in message:
            return True
    message = str(error)
    return "temperature" in message and "unsupported" in message


def openai_completion(
    prompt: str,
    args: 'OpenAIDecodingArguments',
    model_name: str = "gpt-4",
    provider: str = "openai",
    system_prompt: Optional[str] = None
) -> str:
    """Get completion from OpenAI API"""
    if provider == "openai":
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif provider == "groq":
        client = openai.OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
    else:
        raise ValueError(f"Unknown provider: {provider}")

    try:
        completion_kwargs = {k: v for k, v in vars(args).items() if v is not None}

        if provider == "openai":
            if "max_tokens" in completion_kwargs:
                completion_kwargs["max_completion_tokens"] = completion_kwargs.pop("max_tokens")
        else:
            if "max_completion_tokens" in completion_kwargs and "max_tokens" not in completion_kwargs:
                completion_kwargs["max_tokens"] = completion_kwargs.pop("max_completion_tokens")

        attempt_kwargs = dict(completion_kwargs)
        adjusted_temperature = False

        while True:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    **attempt_kwargs
                )
                return response.choices[0].message.content
            except openai.BadRequestError as api_error:
                has_temperature = "temperature" in attempt_kwargs
                if not adjusted_temperature and has_temperature and _is_temperature_unsupported_error(api_error):
                    logger.warning(
                        "Model %s does not support non-default temperature; retrying without it.",
                        model_name
                    )
                    attempt_kwargs.pop("temperature", None)
                    adjusted_temperature = True
                    continue
                raise
    except Exception as e:
        logger.error(f"Error in OpenAI completion: {e}")
        raise
