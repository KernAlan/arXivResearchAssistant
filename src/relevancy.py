"""Paper relevancy scoring using LLMs"""
from typing import List, Dict, Tuple
import logging
from tqdm import tqdm

from .utils import (
    create_quick_scoring_prompt,
    process_scoring_response,
    openai_completion,
    OpenAIDecodingArguments
)

logger = logging.getLogger(__name__)

def score_papers(
    papers: List[Dict],
    interest: str,
    model_config: Dict,
    threshold: float = 7.5
) -> Tuple[List[Dict], bool]:
    """Score papers for relevance and importance"""
    logger.info(f"Scoring {len(papers)} papers")
    
    # Split papers into chunks
    chunk_size = model_config.get("papers_per_batch", 8)
    paper_chunks = [papers[i:i+chunk_size] for i in range(0, len(papers), chunk_size)]
    
    # Score papers in chunks
    scored_papers = []
    had_hallucination = False
    
    for chunk in tqdm(paper_chunks, desc="Scoring papers"):
        prompt = create_quick_scoring_prompt(interest, chunk)
        response = openai_completion(
            prompt,
            OpenAIDecodingArguments(
                temperature=model_config.get("temperature", 1.0)
            ),
            model_name=model_config.get("name", "gpt-4"),
            provider=model_config.get("provider", "openai")
        )
        
        chunk_scored, chunk_hallu = process_scoring_response(chunk, response, threshold)
        scored_papers.extend(chunk_scored)
        had_hallucination = had_hallucination or chunk_hallu
    
    # Log results
    logger.info(f"Papers processed: {len(papers)}")
    logger.info(f"Papers above threshold: {len(scored_papers)}")
    
    # Get score distributions
    relevance_dist = {i: 0 for i in range(1, 11)}
    importance_dist = {i: 0 for i in range(1, 11)}
    
    for p in scored_papers:
        rel_score = round(p["relevance"])
        imp_score = round(p["importance"])
        if 1 <= rel_score <= 10:
            relevance_dist[rel_score] += 1
        if 1 <= imp_score <= 10:
            importance_dist[imp_score] += 1
            
    logger.info(f"Relevance distribution: " + ", ".join(f"{k}:{v}" for k, v in relevance_dist.items()))
    logger.info(f"Importance distribution: " + ", ".join(f"{k}:{v}" for k, v in importance_dist.items()))
    
    # Sort by combined score and take top 20
    final_papers = sorted(
        scored_papers,
        key=lambda x: (x["relevance"] + x["importance"])/2,
        reverse=True
    )[:20]
    
    logger.info(f"Final selection: {len(final_papers)} papers")
    return final_papers, had_hallucination
