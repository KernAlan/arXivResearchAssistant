"""ArXiv Research Assistant - Daily paper digest generator"""
import logging
from datetime import datetime
from pathlib import Path
import yaml
import os
from dotenv import load_dotenv

from . import relevancy
from . import utils
from . import config as config_module

# Setup logging with a cleaner format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Verify API keys are present
if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
    raise RuntimeError(
        "No API key found. Please set either OPENAI_API_KEY or GROQ_API_KEY in your .env file"
    )

def generate_summary(scored_papers: list, config: dict) -> str:
    """Generate an executive summary of the papers using GPT-4"""
    client = utils.setup_client(config["model"]["provider"])
    
    system_prompt = """You are a highly selective research assistant for an applied AI engineer named Alan Kern who:
- Implements and deploys LLM-based solutions in production environments
- Focuses on Applied AI: RAG systems, agents, vector databases, graph databases, embedding models, orchestration frameworks, and prompt engineering.
- Needs to know about significant improvements in:
  * RAG and retrieval systems
  * Production deployment patterns
  * Vector database optimizations
  * Real-world implementation case studies
  * Enterprise integration approaches
  * Cost and performance benchmarks
  * Agentic systems
  * Prompt engineering
  * Prompting techniques
  * Prompting best practices
  * Orchestration frameworks

Your role is to:
1. Identify truly significant developments that could impact AI systems
2. Highlight practical implementation insights
3. Filter out purely theoretical or academic papers related to pretraining models that only research scientists working on foundation models would care about

Be selective - only highlight papers that demonstrate substantial practical value or game-changing approaches."""

    papers_text = "\n\n".join(
        f"Title: {p['title']}\nScore: {p['score']}\nAbstract: {p['abstract']}\n---"
        for p in scored_papers
    )
    user_prompt = (
        "Hey! As my friendly and helpful research assistant, your task is to review these papers and provide a detailed, high-impact summary "
        "of only the most significant developments in AI engineering. Let's make this interesting and engaging!\n\n"
        f"Papers:\n{papers_text}\n\n"
        "For each significant paper, format your response using this HTML structure:\n\n"
        "<div class='paper-summary'>\n"
        "  <h3>Title of the Paper</h3>\n"
        "  <div class='significance'>Significance: [Key metrics and breakthrough claims]</div>\n"
        "  <div class='impact'>Impact: [Why it matters for production AI systems]</div>\n"
        "  <div class='implementation'>Implementation: [Practical insights and considerations]</div>\n"
        "</div>\n\n"
        "Only include papers that demonstrate substantial, concrete value for AI engineering. "
        "Quality over quantity - it's fine to highlight just 1-2 papers if that's all that's truly significant."
    )

    response = client.chat.completions.create(
        model=config["model"]["name"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5
    )
    
    return response.choices[0].message.content

def generate_digest(config: dict) -> str:
    """Generate HTML digest from config"""
    # Get papers
    papers = utils.get_papers(
        topic=config["user"]["topic"],
        categories=config["user"].get("categories", [])
    )
    logger.info(f"Found {len(papers)} papers")
    
    # Score and filter papers
    scored_papers, had_hallucination = relevancy.score_papers(
        papers=papers,
        interest=config["interest"],
        model_config=config["model"],
        threshold=config["model"].get("threshold", 7.5)
    )
    logger.info(f"Selected {len(scored_papers)} relevant papers")
    
    # Generate executive summary
    logger.info("Generating executive summary...")
    summary = generate_summary(scored_papers, config)
    
    # Generate HTML
    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                max-width: 1200px;
                margin: 40px auto;
                padding: 20px;
                line-height: 1.6;
                color: #1a202c;
                background: #f7fafc;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .summary {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                margin: 20px 0;
                border: 1px solid #e2e8f0;
            }}
            .paper-summary {{
                margin: 30px 0;
                padding: 20px;
                border-left: 4px solid #4299e1;
                background: #f8fafc;
                border-radius: 8px;
            }}
            .paper-summary h3 {{
                color: #2c5282;
                margin: 0 0 15px 0;
                font-size: 1.3em;
            }}
            .significance {{
                background: #ebf8ff;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
            }}
            .impact {{
                background: #e6fffa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
            }}
            .implementation {{
                background: #f0fff4;
                padding: 15px;
                margin: 10px 0;
                border-radius: 6px;
            }}
            h1 {{
                color: #2d3748;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 15px;
                margin-bottom: 30px;
            }}
            h2 {{
                color: #2c5282;
                margin: 0 0 20px 0;
                font-size: 1.5em;
            }}
            .stats {{
                background: #f0fff4;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                font-size: 0.95em;
                color: #2f855a;
                border-left: 4px solid #48bb78;
            }}
            .paper {{
                background: white;
                margin-bottom: 30px;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
            }}
            .paper:hover {{
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-color: #cbd5e0;
            }}
            .title {{
                font-size: 1.3em;
                color: #2b6cb0;
                margin-bottom: 12px;
                font-weight: 600;
                line-height: 1.4;
            }}
            .title a {{
                text-decoration: none;
                color: inherit;
            }}
            .title a:hover {{
                color: #2c5282;
                text-decoration: underline;
            }}
            .score {{
                display: inline-block;
                padding: 4px 12px;
                background: {{"#9ae6b4" if paper['score'] >= 8 else "#faf089"}};
                border-radius: 20px;
                font-weight: 500;
                margin: 8px 0;
                font-size: 0.9em;
            }}
            .authors {{
                color: #4a5568;
                font-size: 0.95em;
                margin-bottom: 12px;
            }}
            .abstract {{
                margin-top: 15px;
                color: #4a5568;
                line-height: 1.7;
                font-size: 0.95em;
            }}
            .warning {{
                background: #fff5f5;
                color: #c53030;
                padding: 12px 20px;
                border-radius: 8px;
                margin: 15px 0;
                border-left: 4px solid #fc8181;
                font-size: 0.95em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ArXiv Research Digest - {datetime.now().strftime('%Y-%m-%d')}</h1>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                {summary}
            </div>
            
            <div class="stats">
                <strong>Overview:</strong><br>
                Total papers processed: {len(papers)}<br>
                Papers matching criteria: {len(scored_papers)}<br>
                Score threshold: {config["model"].get("threshold", 7.5)}
            </div>
            
            {f'<div class="warning">Note: Some responses may contain hallucinations</div>' if had_hallucination else ''}
            
            {f'<div class="warning">No relevant papers found matching your criteria.</div>' if not scored_papers else ''}
        </div>
    </body>
    </html>
    """
    
    for paper in scored_papers:
        html += f"""
        <div class="paper">
            <div class="title">
                <a href="{paper['main_page']}" target="_blank">{paper['title']}</a>
            </div>
            <div class="authors">{paper['authors']}</div>
            <div class="score">Relevance Score: {paper['score']}/10</div>
            <div class="abstract">{paper['abstract']}</div>
        </div>
        """
    
    html += "</body></html>"
    return html

def main():
    """Main entry point"""
    # Use the singleton config instance
    config = config_module.config._config
    
    # Create digests directory
    output_dir = Path("digests")
    output_dir.mkdir(exist_ok=True)
    
    # Generate digest
    logger.info("Generating research digest...")
    html = generate_digest(config)
    
    # Save digest with UTF-8 encoding
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"arxiv_digest_{timestamp}.html"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"Digest saved to {output_path}")

if __name__ == "__main__":
    main() 