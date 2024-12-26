"""Base HTML templates and styling"""

BASE_STYLE = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.5;
    color: #2d3748;
    margin: 0;
    padding: 20px;
    background: #f7fafc;
}

.digest {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.header {
    margin-bottom: 2rem;
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

.highlights {
    background: #f8fafc;
    padding: 1.5rem;
    border-radius: 8px;
    margin-bottom: 3rem;
    border: 1px solid #e2e8f0;
}

.highlights h3 {
    color: #2d3748;
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
}

.summary {
    white-space: pre-line;
    line-height: 1.6;
}

.summary ol {
    padding-left: 1.5rem;
    margin: 1rem 0;
}

.summary li {
    margin-bottom: 0.75rem;
    padding-left: 0.5rem;
}

.papers {
    margin-top: 3rem;
}

.papers h3 {
    color: #2d3748;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #e2e8f0;
}

.paper {
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
}

.paper:last-child {
    border-bottom: none;
}

.paper h3 {
    margin: 0 0 0.5rem;
    color: #2d3748;
}

.paper .scores {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.5rem;
}

.paper .score {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
}

.paper .relevance {
    background: #e6fffa;
    color: #047481;
}

.paper .importance {
    background: #ebf4ff;
    color: #1a56db;
}

.paper .abstract {
    color: #4a5568;
    margin: 0.5rem 0;
}

.paper .meta {
    font-size: 0.875rem;
    color: #718096;
}

.paper .meta a {
    color: #4299e1;
    text-decoration: none;
}

.paper .meta a:hover {
    text-decoration: underline;
}
"""

def render_base(content: str) -> str:
    """Render base HTML template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>ArXiv Research Digest</title>
        <style>
            {BASE_STYLE}
        </style>
    </head>
    <body>
        {content}
    </body>
    </html>
    """ 