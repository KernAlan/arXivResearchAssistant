"""Test configuration for the AI Reader project."""

from unittest.mock import MagicMock
import sys


# The production code imports the real OpenAI SDK, but our tests never make
# network calls. Providing a lightweight stub keeps the import from failing
# when the dependency is absent in the CI environment.
sys.modules.setdefault("openai", MagicMock())
