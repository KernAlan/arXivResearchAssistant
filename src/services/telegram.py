import os
import logging
import httpx
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self, config):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or config.telegram.get("bot_token")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID") or config.telegram.get("chat_id")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def send_alert(self, paper: Dict) -> bool:
        """
        Sends a Telegram alert for a high-value 'arbitrage' paper.
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) not set. Skipping alert.")
            return False

        try:
            title = paper.get('title', 'Unknown Title')
            url = paper.get('url', 'No URL')
            arbitrage_score = paper.get('arbitrage_score', 0)
            reason = paper.get('arbitrage_reason', 'No reason provided.')

            message = (
                f"🚨 *Arbitrage Discovery Alert* 🚨\n\n"
                f"*Title:* {title}\n"
                f"*Score:* {arbitrage_score}/10\n"
                f"*Why:* {reason}\n\n"
                f"[Read Paper]({url})"
            )

            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }

            response = httpx.post(self.base_url, json=payload, timeout=10.0)
            response.raise_for_status()
            
            logger.info(f"Telegram alert sent for paper: {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
