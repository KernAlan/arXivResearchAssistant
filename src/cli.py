"""Command line interface for ArXiv Digest"""
import logging
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
import click

from .config import config
from .templates import base, digest
from .output_manager import DigestOutputManager
from .services import PaperService, EmailService
from .utils.last_run import save_last_run_date

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Set higher log levels for noisy modules
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """ArXiv Research Digest CLI"""
    pass

@cli.command()
@click.option('--commit', is_flag=True, help='Commit digest to git repository')
@click.option('--output-dir', default='digests', help='Output directory')
@click.option('--email', is_flag=True, help='Send digest via email')
def generate(commit: bool, output_dir: str, email: bool):
    """Generate research digest"""
    try:
        logger.debug("Starting digest generation...")
        
        # Verify API keys
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
            logger.error("No API key found!")
            raise RuntimeError(
                "No API key found. Please set either OPENAI_API_KEY or GROQ_API_KEY in your .env file"
            )

        logger.debug("API keys verified")
        
        # Initialize services
        logger.info(f"Using config: {config.user}")
        paper_service = PaperService(config)
        logger.debug("Paper service initialized")
        
        # Get papers
        logger.info("Fetching papers...")
        papers = paper_service.get_papers()
        logger.info(f"Got {len(papers)} papers")
        
        if not papers:
            logger.warning("No papers found!")
            return
            
        scored_papers, had_hallucination = paper_service.process_papers(papers)
        summary = paper_service.generate_summary(scored_papers)
        
        # Render HTML
        logger.info("Rendering digest...")
        digest_content = digest.render_digest(
            papers=scored_papers,
            summary=summary,
            total_papers=len(papers),
            threshold=config.model.get("threshold", 7.5),
            had_hallucination=had_hallucination
        )
        html_content = base.render_base(digest_content)
        
        # Save digest
        output_manager = DigestOutputManager(base_dir=output_dir)
        filepath = output_manager.save_digest(html_content)
        logger.info(f"Saved digest to {filepath}")
        
        # Optional actions
        if commit:
            output_manager.commit_to_git(filepath)
        
        if email:
            email_service = EmailService()
            if email_service.send_digest(
                html_content=html_content,
                to_email=os.getenv("TO_EMAIL"),
                from_email=os.getenv("FROM_EMAIL")
            ):
                logger.info("Email sent successfully")
            else:
                logger.error("Failed to send email")

        # Save successful run date
        save_last_run_date()
        logger.info("Updated last run date")

    except Exception as e:
        logger.exception("Error in generate command")
        raise

if __name__ == "__main__":
    cli()