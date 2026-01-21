import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.telegram import TelegramService
from src.config import config

def main():
    load_dotenv()
    print("Testing Telegram hook with a real message...")
    
    service = TelegramService(config)
    
    dummy_paper = {
        "title": "Stealth Optimization: 10x KV Cache Compression for Production LLMs",
        "url": "https://arxiv.org/abs/2601.00001",
        "arbitrage_score": 9.2,
        "arbitrage_reason": "This paper introduces a bit-packing technique for KV caches that reduces memory overhead by 90% with zero loss in perplexity. It's published by a small lab in Zurich and hasn't been mentioned on Twitter yet."
    }
    
    success = service.send_alert(dummy_paper)
    
    if success:
        print("Success! Check your Telegram.")
    else:
        print("Failed to send message. Check your .env credentials.")

if __name__ == "__main__":
    main()
