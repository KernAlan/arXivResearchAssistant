"""Services package for AI Reader"""
from .papers import PaperService
from .email import EmailService
from .telegram import TelegramService
from .github_trending import GitHubTrendingService

__all__ = ['PaperService', 'EmailService', 'TelegramService', 'GitHubTrendingService'] 