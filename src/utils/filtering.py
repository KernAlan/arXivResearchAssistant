"""Paper filtering utilities"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def filter_ai_papers(papers: list, config: dict) -> list:
    """Pre-filter papers related to applied AI/LLMs"""
    primary_keywords = config.FILTERING_KEYWORDS["primary"]
    secondary_keywords = config.FILTERING_KEYWORDS["secondary"]
    
    filtered_papers = []
    primary_matches = 0
    secondary_matches = 0
    
    for paper in papers:
        text = (paper['title'] + ' ' + paper['abstract']).lower()
        
        # Check if paper contains any primary keywords
        has_primary = any(kw in text for kw in primary_keywords)
        if has_primary:
            primary_matches += 1
            filtered_papers.append(paper)
            continue
            
        # Check secondary keywords
        secondary_count = sum(1 for kw in secondary_keywords if kw in text)
        if secondary_count >= config.PAPER_CONFIG["keyword_match_threshold"]:
            secondary_matches += 1
            filtered_papers.append(paper)
    
    logger.info(
        f"Keyword filtering stats:\n"
        f"  Total papers: {len(papers)}\n"
        f"  Primary keyword matches: {primary_matches}\n"
        f"  Secondary keyword matches: {secondary_matches}\n"
        f"  Papers kept: {len(filtered_papers)}"
    )
    
    return filtered_papers 