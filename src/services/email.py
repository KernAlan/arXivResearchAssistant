"""Email service for sending digests"""
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os

class EmailService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        if not self.api_key:
            raise ValueError("SendGrid API key not found")
        self.client = SendGridAPIClient(api_key=self.api_key)
    
    def send_digest(
        self,
        html_content: str,
        to_email: str,
        from_email: str,
        subject: str = "ArXiv Research Digest"
    ) -> bool:
        """Send digest email using SendGrid"""
        message = Mail(
            from_email=Email(from_email),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        response = self.client.send(message)
        return 200 <= response.status_code < 300 