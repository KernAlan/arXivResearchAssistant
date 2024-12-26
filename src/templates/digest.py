"""Digest-specific HTML templates"""
from datetime import datetime
from typing import Dict, List

PAPER_STYLE = """
.paper {
    background: white;
    margin-bottom: 30px;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
}
.paper:hover {
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-color: #cbd5e0;
}
.title {
    font-size: 1.3em;
    color: #2b6cb0;
    margin-bottom: 12px;
    font-weight: 600;
    line-height: 1.4;
}
.title a {
    text-decoration: none;
    color: inherit;
}
.title a:hover {
    color: #2c5282;
    text-decoration: underline;
}
.score {
    display: inline-block;
    padding: 4px 12px;
    background: var(--score-color);
    border-radius: 20px;
    font-weight: 500;
    margin: 8px 0;
    font-size: 0.9em;
}
.authors {
    color: #4a5568;
    font-size: 0.95em;
    margin-bottom: 12px;
}
.abstract {
    margin-top: 15px;
    color: #4a5568;
    line-height: 1.7;
    font-size: 0.95em;
}
"""

DIGEST_TEMPLATE = """
<div class="digest">
    <div class="header">
        <h2>ArXiv Research Digest</h2>
        <p>Found {matching_papers} relevant papers out of {total_papers} new submissions</p>
    </div>
    
    <div class="highlights">
        <h3>🔥 Key Highlights</h3>
        {summary}
    </div>
    
    <div class="papers">
        <h3>📄 Detailed Papers</h3>
        {papers}
    </div>
</div>
"""

PAPER_TEMPLATE = """
<div class="paper">
    <h3>{title}</h3>
    <div class="scores">
        <span class="score relevance">Relevance: {relevance}/10</span>
        <span class="score importance">Importance: {importance}/10</span>
    </div>
    <div class="abstract">{abstract}</div>
    <div class="meta">
        <a href="{url}" target="_blank">View on arXiv</a>
    </div>
</div>
"""

STYLE = """
.digest {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    margin-bottom: 30px;
}

.highlights {
    background: #f7fafc;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 40px;
    border-left: 4px solid #4299e1;
}

.papers {
    margin-top: 40px;
}

.paper {
    background: white;
    margin-bottom: 30px;
    padding: 25px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.scores {
    display: flex;
    gap: 12px;
    margin: 12px 0;
}

.score {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9em;
}

.score.relevance {
    background: var(--relevance-color, #f0fff4);
}

.score.importance {
    background: var(--importance-color, #fff5f5);
}
"""

def render_paper(paper: dict) -> str:
    """Render a single paper"""
    return PAPER_TEMPLATE.format(
        title=paper['title'],
        abstract=paper['abstract'],
        relevance=paper.get('relevance', 'N/A'),
        importance=paper.get('importance', 'N/A'),
        url=paper.get('url', f"https://arxiv.org/abs/{paper.get('paper_id', '')}")
    )

def render_digest(papers: List[Dict], summary: str, total_papers: int, threshold: float, had_hallucination: bool) -> str:
    """Render the digest HTML"""
    return DIGEST_TEMPLATE.format(
        matching_papers=len(papers),
        total_papers=total_papers,
        summary=summary,
        papers="\n".join(render_paper(p) for p in papers)
    ) 