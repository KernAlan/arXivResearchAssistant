"""OpenAI API utilities"""
import os
import logging
from typing import Optional
import openai

logger = logging.getLogger(__name__)

def openai_completion(prompt: str, args: 'OpenAIDecodingArguments', model_name: str = "gpt-4", provider: str = "openai") -> str:
    """Get completion from OpenAI API"""
    if provider == "openai":
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    elif provider == "groq":
        client = openai.OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
    else:
        raise ValueError(f"Unknown provider: {provider}")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            **args.__dict__
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in OpenAI completion: {e}")
        raise 