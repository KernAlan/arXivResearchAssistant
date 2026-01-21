"""GitHub Trending HTML templates"""
from datetime import datetime
from typing import Dict, List

GITHUB_TEMPLATE = """
<div class="digest">
    <div class="header">
        <h2>GitHub Trending Report</h2>
        <p>{date} &bull; Scored {total_repos} repositories &bull; {high_score_count} worth attention</p>
    </div>

    <div class="executive-summary">
        <h3>Executive Summary</h3>
        <p>{executive_summary}</p>
    </div>

    {high_scores_section}

    <div class="repos">
        <h3>All Scored Repositories</h3>
        {repos}
    </div>
</div>
"""

HIGH_SCORES_SECTION = """
<div class="highlights">
    <h3>Worth Your Attention</h3>
    {repos}
</div>
"""

REPO_TEMPLATE = """
<div class="repo {highlight_class}">
    <div class="repo-header">
        <h3><a href="{url}" target="_blank">{name}</a></h3>
        <div class="scores">
            <span class="score composite-{composite_class}">{composite:.1f}</span>
            <span class="score relevance-{relevance_class}">R:{relevance}</span>
            <span class="score impact-{impact_class}">I:{impact}</span>
        </div>
    </div>
    <div class="repo-meta">
        <span class="language">{language}</span>
        <span class="stars">{stars:,} stars (+{stars_today} today)</span>
    </div>
    <p class="description">{description}</p>
    <div class="summary">
        <strong>Analysis:</strong> {summary}
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
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
}

.header h2 {
    margin: 0;
    color: #2d3748;
}

.header p {
    margin: 0.5rem 0 0;
    color: #718096;
}

.executive-summary {
    background: linear-gradient(135deg, #ebf8ff 0%, #bee3f8 100%);
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    border: 1px solid #90cdf4;
}

.executive-summary h3 {
    color: #2b6cb0;
    margin: 0 0 0.75rem 0;
    font-size: 1.1rem;
}

.executive-summary p {
    color: #2d3748;
    margin: 0;
    line-height: 1.7;
    font-size: 1rem;
}

.highlights {
    background: linear-gradient(135deg, #fff5f5 0%, #fed7d7 100%);
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    border: 2px solid #fc8181;
}

.highlights h3 {
    color: #c53030;
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
}

.highlights .repo {
    background: white;
    border: 1px solid #feb2b2;
}

.repos {
    margin-top: 2rem;
}

.repos h3 {
    color: #2d3748;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
}

.repo {
    background: white;
    margin-bottom: 1.5rem;
    padding: 1.25rem;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.repo.high-score {
    border-left: 4px solid #e53e3e;
}

.repo-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.repo-header h3 {
    margin: 0;
    font-size: 1.1rem;
}

.repo-header h3 a {
    color: #2b6cb0;
    text-decoration: none;
}

.repo-header h3 a:hover {
    text-decoration: underline;
}

.scores {
    display: flex;
    gap: 0.5rem;
}

.score {
    padding: 0.25rem 0.6rem;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.8rem;
    white-space: nowrap;
}

.composite-high {
    background: #c53030;
    color: white;
    font-size: 1rem;
    padding: 0.3rem 0.8rem;
}

.composite-medium {
    background: #dd6b20;
    color: white;
    font-size: 1rem;
    padding: 0.3rem 0.8rem;
}

.composite-low {
    background: #718096;
    color: white;
    font-size: 1rem;
    padding: 0.3rem 0.8rem;
}

.relevance-high {
    background: #c6f6d5;
    color: #22543d;
}

.relevance-medium {
    background: #feebc8;
    color: #744210;
}

.relevance-low {
    background: #e2e8f0;
    color: #4a5568;
}

.impact-high {
    background: #fed7d7;
    color: #c53030;
}

.impact-medium {
    background: #feebc8;
    color: #c05621;
}

.impact-low {
    background: #e2e8f0;
    color: #4a5568;
}

.repo-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.875rem;
    color: #718096;
    margin-bottom: 0.75rem;
}

.language {
    background: #edf2f7;
    padding: 0.125rem 0.5rem;
    border-radius: 4px;
}

.stars {
    color: #d69e2e;
}

.description {
    color: #4a5568;
    margin: 0.5rem 0;
    line-height: 1.5;
    font-style: italic;
}

.summary {
    background: #f7fafc;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    margin-top: 0.75rem;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #2d3748;
    border-left: 3px solid #4299e1;
}

.summary strong {
    color: #2b6cb0;
}
"""


def get_score_class(score: int) -> str:
    """Get CSS class based on score"""
    if score >= 8:
        return "high"
    elif score >= 5:
        return "medium"
    return "low"


def render_repo(repo: dict, is_highlight: bool = False) -> str:
    """Render a single repository"""
    relevance = repo.get('relevance', 0)
    impact = repo.get('impact', 0)
    composite = repo.get('composite', (relevance + impact) / 2)

    return REPO_TEMPLATE.format(
        name=repo['name'],
        url=repo.get('url', f"https://github.com/{repo['name']}"),
        relevance=relevance,
        impact=impact,
        composite=composite,
        relevance_class=get_score_class(relevance),
        impact_class=get_score_class(impact),
        composite_class=get_score_class(int(composite)),
        language=repo.get('language', 'Unknown'),
        stars=repo.get('stars', 0),
        stars_today=repo.get('stars_today', 0),
        description=repo.get('description', 'No description') or 'No description',
        summary=repo.get('summary', 'No analysis available'),
        highlight_class="high-score" if is_highlight else ""
    )


def render_github_report(repos: List[Dict], threshold: float, executive_summary: str = "") -> str:
    """Render the GitHub trending report HTML"""
    # Calculate composite score and sort by it
    for repo in repos:
        if 'composite' not in repo:
            repo['composite'] = (repo.get('relevance', 0) + repo.get('impact', 0)) / 2

    sorted_repos = sorted(
        repos,
        key=lambda x: x.get('composite', 0),
        reverse=True
    )

    # High scores are those with composite >= threshold
    high_scores = [r for r in sorted_repos if r.get('composite', 0) >= threshold]

    # Render high scores section
    if high_scores:
        high_scores_html = HIGH_SCORES_SECTION.format(
            repos="\n".join(render_repo(r, is_highlight=True) for r in high_scores)
        )
    else:
        high_scores_html = ""

    # Render all repos
    all_repos_html = "\n".join(render_repo(r) for r in sorted_repos)

    # Default executive summary if none provided
    if not executive_summary:
        executive_summary = "No executive summary generated."

    return GITHUB_TEMPLATE.format(
        date=datetime.now().strftime("%B %d, %Y"),
        total_repos=len(repos),
        high_score_count=len(high_scores),
        executive_summary=executive_summary,
        high_scores_section=high_scores_html,
        repos=all_repos_html
    )


def render_github_base(content: str) -> str:
    """Render base HTML template for GitHub report"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>GitHub Trending Report</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                line-height: 1.5;
                color: #2d3748;
                margin: 0;
                padding: 20px;
                background: #f7fafc;
            }}
            {STYLE}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """
