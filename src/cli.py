"""Command line interface for ArXiv Digest"""
import logging
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv
import click

from .config import config
from .templates import base, digest, github_trending as gh_template
from .output_manager import DigestOutputManager
from .services import PaperService, EmailService, TelegramService, GitHubTrendingService
from .utils.last_run import save_last_run_date
from .utils import create_quick_scoring_prompt, openai_completion, OpenAIDecodingArguments
import json

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

@cli.command()
@click.option('--title', '-t', required=True, help='Paper title')
@click.option('--abstract', '-a', required=True, help='Paper abstract')
def score(title: str, abstract: str):
    """Score a single paper (real or fake) to test the scoring system"""
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        click.echo("Error: OPENAI_API_KEY not set")
        return

    # Create fake paper
    paper = {
        'title': title,
        'abstract': abstract,
        'url': 'https://example.com/fake-paper'
    }

    click.echo(f"\nScoring paper:")
    click.echo(f"  Title: {title[:80]}{'...' if len(title) > 80 else ''}")
    click.echo(f"  Abstract: {abstract[:100]}{'...' if len(abstract) > 100 else ''}")
    click.echo("\nCalling LLM...")

    # Run through scoring
    prompt = create_quick_scoring_prompt(
        config.interest,
        [paper],
        arbitrage_interest=config.arbitrage_interest
    )

    response = openai_completion(
        prompt,
        OpenAIDecodingArguments(temperature=config.model.get("temperature", 1.0)),
        model_name=config.model.get("name", "gpt-4.1-mini"),
        provider=config.model.get("provider", "openai")
    )

    # Parse response
    try:
        cleaned = response.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('\n', 1)[0]

        data = json.loads(cleaned)
        scores = data.get('scores', [{}])[0]

        rel = scores.get('Relevancy score', '?')
        imp = scores.get('Importance score', '?')
        arb = scores.get('Arbitrage score', '?')
        reason = scores.get('Arbitrage reason', 'No reason')

        click.echo(f"\n{'='*50}")
        click.echo(f"RESULTS:")
        click.echo(f"  Relevancy:  {rel}/10")
        click.echo(f"  Importance: {imp}/10")
        click.echo(f"  Arbitrage:  {arb}/10")
        click.echo(f"  Reason:     {reason}")
        click.echo(f"{'='*50}")

        # Check thresholds
        arb_thresh = config.model.get("arbitrage_threshold", 8.5)
        if isinstance(arb, (int, float)) and arb >= arb_thresh:
            click.echo(f"\n🚨 Would trigger Telegram alert! (>= {arb_thresh})")
        else:
            click.echo(f"\n✓ Below alert threshold ({arb_thresh})")

    except Exception as e:
        click.echo(f"\nError parsing response: {e}")
        click.echo(f"Raw response:\n{response}")


@cli.command('github-trending')
@click.option('--language', '-l', default='', help='Filter by language (e.g., python)')
@click.option('--since', '-s', default='daily', type=click.Choice(['daily', 'weekly', 'monthly']), help='Time range')
@click.option('--threshold', '-t', default=8.0, help='Composite score threshold (avg of relevance+impact) for Telegram alerts')
@click.option('--dry-run', is_flag=True, help='Show scores without sending alerts')
@click.option('--output-dir', default='digests', help='Output directory for HTML report')
@click.option('--no-report', is_flag=True, help='Skip HTML report generation')
def github_trending(language: str, since: str, threshold: float, dry_run: bool, output_dir: str, no_report: bool):
    """Fetch GitHub trending repos, score them, and alert on high-value finds"""
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        click.echo("Error: OPENAI_API_KEY not set")
        return

    click.echo(f"\nFetching GitHub trending ({since})...")
    if language:
        click.echo(f"  Language filter: {language}")

    # Fetch trending
    gh_service = GitHubTrendingService(config)
    repos = gh_service.fetch_trending(language=language, since=since)

    if not repos:
        click.echo("No trending repos found.")
        return

    click.echo(f"Found {len(repos)} trending repos")

    # Filter to new repos only
    new_repos = gh_service.filter_new(repos)
    if not new_repos:
        click.echo("No new repos (all already seen).")
        return

    click.echo(f"Scoring {len(new_repos)} new repos...\n")

    # Score each repo
    telegram = TelegramService(config)
    scored_repos = []
    high_scores = []

    for repo in new_repos:
        score_result = _score_github_repo(repo)

        if score_result:
            relevance = score_result.get('relevance', 0)
            impact = score_result.get('impact', 0)
            summary = score_result.get('summary', 'No summary')
            composite = (relevance + impact) / 2

            icon = ">>" if composite >= threshold else "  "
            click.echo(f"{icon} [R:{relevance:>2} I:{impact:>2} C:{composite:.1f}] {repo['name'][:32]:<32} *{repo['stars']:>6} (+{repo['stars_today']})")
            click.echo(f"          {summary[:75]}...")

            scored_repo = {**repo, 'relevance': relevance, 'impact': impact, 'composite': composite, 'summary': summary}
            scored_repos.append(scored_repo)

            if composite >= threshold:
                high_scores.append(scored_repo)

    # Generate executive summary
    executive_summary = ""
    if scored_repos:
        click.echo(f"\nGenerating executive summary...")
        executive_summary = _generate_executive_summary(scored_repos)

    # Generate HTML report
    if not no_report and scored_repos:
        report_content = gh_template.render_github_report(scored_repos, threshold, executive_summary)
        html_content = gh_template.render_github_base(report_content)

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_path / f"github_trending_{timestamp}.html"
        report_file.write_text(html_content, encoding='utf-8')
        click.echo(f"\nSaved report to {report_file}")

    # Send alerts
    if high_scores and not dry_run:
        click.echo(f"\n{'='*50}")
        click.echo(f"Sending {len(high_scores)} Telegram alerts...")
        for repo in high_scores:
            _send_github_alert(telegram, repo)
        click.echo("Done!")
    elif high_scores and dry_run:
        click.echo(f"\n[DRY RUN] Would send {len(high_scores)} alerts")
    else:
        click.echo(f"\nNo repos with composite score >= {threshold}")

    # Mark all as seen
    gh_service.mark_seen([r['name'] for r in new_repos])


def _score_github_repo(repo: dict) -> dict:
    """Score a single GitHub repo using LLM"""
    prompt = f"""{config.github_scoring_prompt}

Repository:
- Name: {repo['name']}
- Description: {repo['description'] or 'No description'}
- Language: {repo['language']}
- Stars: {repo['stars']} ({repo['stars_today']} today)

Return only valid JSON: {{"relevance": N, "impact": N, "summary": "..."}}"""

    try:
        response = openai_completion(
            prompt,
            OpenAIDecodingArguments(temperature=0.3, max_tokens=400),
            model_name=config.model.get("name", "gpt-4.1-mini"),
            provider=config.model.get("provider", "openai")
        )

        cleaned = response.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('\n', 1)[0]

        return json.loads(cleaned)
    except Exception as e:
        logger.warning(f"Failed to score {repo['name']}: {e}")
        return None


def _generate_executive_summary(scored_repos: list) -> str:
    """Generate an executive summary of the scored repos"""
    # Build repo summary for the prompt
    repo_summaries = []
    for repo in scored_repos:
        repo_summaries.append(
            f"- {repo['name']}: Relevance {repo.get('relevance', 0)}/10, "
            f"Impact {repo.get('impact', 0)}/10 - {repo.get('summary', 'No summary')[:100]}"
        )

    prompt = config.github_executive_summary_prompt.format(
        repos="\n".join(repo_summaries)
    )

    try:
        response = openai_completion(
            prompt,
            OpenAIDecodingArguments(temperature=0.7, max_tokens=300),
            model_name=config.model.get("name", "gpt-4.1-mini"),
            provider=config.model.get("provider", "openai")
        )
        return response.strip()
    except Exception as e:
        logger.warning(f"Failed to generate executive summary: {e}")
        return "Could not generate executive summary."


def _send_github_alert(telegram: TelegramService, repo: dict) -> bool:
    """Send Telegram alert for a high-scoring repo"""
    try:
        import httpx

        composite = repo.get('composite', (repo.get('relevance', 0) + repo.get('impact', 0)) / 2)
        message = (
            f"🔥 *GitHub Trending Alert* 🔥\n\n"
            f"*Repo:* {repo['name']}\n"
            f"*Score:* {composite:.1f}/10 (R:{repo.get('relevance', 0)} I:{repo.get('impact', 0)})\n"
            f"*Stars:* {repo['stars']} (+{repo['stars_today']} today)\n\n"
            f"*Analysis:* {repo.get('summary', 'No summary')}\n\n"
            f"[View on GitHub]({repo['url']})"
        )

        payload = {
            "chat_id": telegram.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = httpx.post(telegram.base_url, json=payload, timeout=10.0)
        response.raise_for_status()
        logger.info(f"GitHub alert sent for: {repo['name']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send GitHub alert: {e}")
        return False


if __name__ == "__main__":
    cli()