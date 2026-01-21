import os
import unittest
from unittest.mock import MagicMock, patch
from src.services.telegram import TelegramService
from src.config import config

class TestTelegramService(unittest.TestCase):
    def setUp(self):
        self.config = config
        # Mock environment variables
        os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"
        os.environ["TELEGRAM_CHAT_ID"] = "test_chat_id"

    @patch("httpx.post")
    def test_send_alert_success(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        service = TelegramService(self.config)
        paper = {
            "title": "Test Paper",
            "main_page": "https://arxiv.org/abs/1234.5678",
            "arbitrage_score": 9,
            "arbitrage_reason": "This is a breakthrough optimization."
        }
        
        result = service.send_alert(paper)
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("Test Paper", kwargs["json"]["text"])
        self.assertIn("9/10", kwargs["json"]["text"])

    @patch("httpx.post")
    def test_send_alert_failure(self, mock_post):
        # Setup mock response for failure
        mock_post.side_effect = Exception("Connection error")

        service = TelegramService(self.config)
        paper = {"title": "Test Paper"}
        
        result = service.send_alert(paper)
        
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
