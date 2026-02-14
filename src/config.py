"""Configuration management for ArxivDigest"""
from typing import Dict, Any

class Config:
    # System prompts
    SUMMARY_SYSTEM_PROMPT = """You are a research assistant writing a quick email to your boss, an AI engineer.
    
Write a super casual, friendly summary of today's most relevant papers (relevance/importance 8+). Imagine you're chatting with your boss at the coffee machine.

Your response should look relatively something like this:
"Hey boss, found [number] cool papers today that I think you'll love:
<ol>
<li>Researchers at Stanford developed a vector storage method that cuts costs by 90% while maintaining retrieval quality by...</li>
<li>A team from Google AI created an agent framework that reduces hallucinations by coordinating multiple specialized models...</li>
</ol>"

Basically it should be an elevator pitch for each paper.

Key rules:
- Just plain, conversational English
- Focus on why each paper matters for real-world use
- Maximum 5 papers
- Each bullet point should serve as an elevator pitch that highlights who did the research and what practical benefit it provides
"""

    QUICK_SCORING_PROMPT = """For each paper below, evaluate its relevance to production AI engineering and its importance as a breakthrough.

You MUST return a JSON object with exactly {num_papers} scores in the array, one for each paper.
The scores array should look like this:
{{
    "scores": [
        {{
            "Relevancy score": 8, 
            "Importance score": 6, 
            "Arbitrage score": 9, 
            "Arbitrage reason": "Reasoning for the arbitrage score goes here..."
        }},
        {{
            "Relevancy score": 5, 
            "Importance score": 7, 
            "Arbitrage score": 2, 
            "Arbitrage reason": "N/A"
        }}
    ]
}}

Each paper must have a Relevancy score, Importance score, and Arbitrage score between 1 and 10.

SCORING GUIDELINES:
- **Relevance/Importance**: Standard academic scoring.
- **Arbitrage Score (CRITICAL)**: Treat this as the "Intern Notification Score".
    - **Base Score is 5.**
    - **Score > 8.5**: Reserved for "Must Read Immediately" papers that fundamentally shift how we build AI. 
    - **Criteria**: Focus on Novel Architectures, New Capabilities, and Deep Explanations.
    - **Filter**: Ignore incremental stats-chasing, pure speedups without capability gain, and fluff/marketing.

My interests are:
{interest}

Also, evaluate for 'Arbitrage Discovery' potential based on these criteria:
{arbitrage_interest}

Papers to evaluate:
{papers}
"""

    # ArXiv Configuration
    ARXIV_CONFIG = {
        "max_results": 200,
        "sort_by": "submittedDate",
        "sort_order": "descending",
        "base_url": "http://export.arxiv.org/api/query",
        "default_lookback_days": 3,
        "categories": {
            'cs.AI': 'Artificial Intelligence'
        }
    }

    # Paper Processing Configuration
    PAPER_CONFIG = {
        "min_papers": 5,  # Minimum papers to include in digest
        "max_papers": 50,  # Maximum papers to show in final digest
        "summary_papers": 5,  # Number of papers to highlight in summary
        "keyword_match_threshold": 1,  # Number of secondary keywords needed to match
    }

    # Filtering Configuration
    FILTERING_KEYWORDS = {
        "primary": {
            'rag', 'retrieval augmented', 'vector database', 'vector store',
            'llm application', 'ai agent', 'prompt engineering',
            'production deployment', 'enterprise ai', 'business case',
            'ai system', 'llm system', 'ai engineering', 'agents',
            'agent', 'agentic framework', 'orchestration', 'LangGraph',
            'Langchain', 'graph database', 'embedding model', 'benchmark',
            'fine tuning'
        },
        "secondary": {
            'production', 'deployment', 'enterprise', 'business',
            'implementation', 'integration', 'infrastructure',
            'cost', 'performance', 'scaling', 'monitoring',
            'reliability', 'observability', 'evaluation',
            'embeddings', 'orchestration', 'automation',
            'real-world', 'case study', 'industry', 'agents',
            'agent', 'agentic framework', 'LangGraph', 'Langchain',
            'graph database', 'embedding model', 'benchmark', 'fine tuning'
        }
    }

    # Model Configuration
    MODEL_CONFIG = {
        "name": "gpt-5-mini",
        "provider": "openai",
        "papers_per_batch": 8,
        "threshold": 9.5,
        "arbitrage_threshold": 9.5,
        "max_tokens": 16000,
        "top_p": 1.0
    }

    # Telegram Configuration
    TELEGRAM_CONFIG = {
        "bot_token": None,  # Set via environment variable TELEGRAM_BOT_TOKEN
        "chat_id": None,    # Set via environment variable TELEGRAM_CHAT_ID
    }

    # User Configuration
    DEFAULT_USER_CONFIG = {
        "topic": "Computer Science",
        "categories": [
            "Artificial Intelligence"
        ]
    }
    
    # Default interest profile
    DEFAULT_INTEREST = """
    I am an applied AI engineer focused on implementing LLM-based solutions for business problems. 
    I am most interested in how LLMs can be used to solve business problems.
    Particularly this means understanding how to orchestrate LLMs, how to make them more reliable, how to make them more cost effective,
    how to store memories and state, how to architect retrieval better, and how to generally simulate human intelligence and human-like behavior
    for market problems. But I am also generally interested in all things AI and how the landscape is evolving.
    """

    ARBITRAGE_INTEREST = """
    I'm Alan Kern. Score papers based on PRACTICAL IMPACT to my work.

    I use LLMs daily for: WRITING (long-form, creative), building products/agents, coding.

    BE EXTREMELY CONSERVATIVE. Most papers deserve a 5 or below. A 10 should happen maybe once a month.

    **HOW TO SCORE — default low, only go high with extraordinary evidence:**

    **10** = "Once-in-a-year paradigm shift" — genuinely transforms how AI works at a fundamental level.
    - Example: Attention mechanism (Transformers paper), RLHF, diffusion models.
    - NOT incremental improvements, NOT "we beat SOTA by 2%".

    **9** = "Genuine breakthrough I must adopt immediately or lose competitive ground"
    - A truly novel architecture or capability that didn't exist before.
    - Must be immediately actionable, not theoretical.

    **7-8** = "Solid and directly useful to my work"

    **5-6** = "Interesting but incremental, or only tangentially relevant"

    **1-4** = "Not relevant to my work"
    - Infrastructure (KV cache, quantization) — I use APIs
    - Pure SOTA-chasing benchmarks
    - Training techniques (I don't train)
    - Incremental improvements to existing methods

    DEFAULT SCORE IS 5. Work UP from there only with strong justification.
    If you're unsure between two scores, pick the LOWER one.
    Most papers in any given day are 4-6. If you're giving more than 1-2 papers an 8+, you're scoring too high.
    """

    GITHUB_SCORING_PROMPT = """
    I'm Alan Kern. Evaluate this GitHub repo for my work.

    I use LLMs for: WRITING (long-form), building agents/products, coding.

    Score TWO dimensions:

    **RELEVANCE** (1-10): How relevant is this to my work?
    - 10 = Directly addresses writing, agents, or LLM product building
    - 7-9 = Related to AI/ML, could be useful
    - 4-6 = Tangentially related
    - 1-3 = Not relevant (crypto, games, pure devops, etc.)

    **IMPACT** (1-10): How game-changing is this?
    - 10 = GAME CHANGER - fundamentally new capability
      (solves long-form coherence, makes agents reliable, new LLM paradigm)
    - 9 = Major breakthrough, would change how I architect systems
    - 8 = Solid innovation, worth adopting
    - 6-7 = Incremental improvement, interesting
    - 1-5 = Nothing new, or not useful

    BE HARSH on impact. Most repos are 5 or below. Only true breakthroughs get 9-10.

    Also write a 2-3 sentence SUMMARY explaining:
    1. What this repo actually does (in plain English)
    2. Why it matters (or doesn't) for someone building AI products

    Return JSON:
    {
      "relevance": N,
      "impact": N,
      "summary": "2-3 sentences explaining what it does and why it matters"
    }
    """

    GITHUB_EXECUTIVE_SUMMARY_PROMPT = """
    You are writing a quick executive briefing for your boss, Alan Kern, about today's GitHub trending repos.

    Alan uses LLMs for: long-form writing, building agents/products, and coding.

    Write a casual, direct summary (3-5 sentences) that answers:
    - Were there any repos worth his attention today?
    - What's the overall theme/vibe of what's trending?
    - Any action items or things to check out?

    Be honest - if nothing is exciting, say so. Don't hype mediocre repos.

    Format: Just plain text, conversational tone. Like you're giving a quick verbal update.

    Here are today's scored repos:
    {repos}
    """

    # File paths and directories
    PATHS = {
        "data_dir": "data",  # Directory for storing data files
        "last_run_file": "data/last_run.txt",  # File to store last run date
        "digests_dir": "digests"  # Directory for storing digests
    }
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.user_config = self.DEFAULT_USER_CONFIG.copy()
        self.model_config = self.MODEL_CONFIG.copy()
        self.interest = self.DEFAULT_INTEREST
        self.arbitrage_interest = self.ARBITRAGE_INTEREST
        self.github_scoring_prompt = self.GITHUB_SCORING_PROMPT
        self.github_executive_summary_prompt = self.GITHUB_EXECUTIVE_SUMMARY_PROMPT
    
    @property
    def user(self) -> Dict[str, Any]:
        return self.user_config
    
    @property
    def model(self) -> Dict[str, Any]:
        return self.model_config

    @property
    def telegram(self) -> Dict[str, Any]:
        return self.TELEGRAM_CONFIG

# Global config instance
config = Config() 
