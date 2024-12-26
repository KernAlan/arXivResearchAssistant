"""Scoring utilities for paper evaluation"""
import logging
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class OpenAIDecodingArguments:
    max_tokens: int = 1800
    temperature: float = 0.2
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: List[str] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

def create_quick_scoring_prompt(interest: str, papers: List[Dict]) -> str:
    """Create prompt for quick scoring of papers"""
    papers_text = "\n\n".join(
        f"Paper {i+1}:\nTitle: {p['title']}\nAbstract: {p['abstract']}"
        for i, p in enumerate(papers)
    )
    return f"""For each paper below, evaluate its relevance to production AI engineering and its importance as a breakthrough.

You MUST return a JSON object with exactly {len(papers)} scores in the array, one for each paper.
The scores array should look like this:
{{
    "scores": [
        {{"Relevancy score": 8, "Importance score": 6}},
        {{"Relevancy score": 5, "Importance score": 7}}
    ]
}}

Each paper must have both a Relevancy score and Importance score between 1 and 10.

My interests are:
{interest}

Papers to evaluate:
{papers_text}"""

def process_scoring_response(papers: List[Dict], response: str, threshold: float) -> Tuple[List[Dict], bool]:
    """Process scoring response from LLM"""
    try:
        # Clean up response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith('```'):
            response = response.split('\n', 1)[1]  # Remove first line with ```json
        if response.endswith('```'):
            response = response.rsplit('\n', 1)[0]  # Remove last line with ```
        
        data = json.loads(response)
        scores = data.get('scores', [])
        
        if len(scores) != len(papers):
            logger.warning(f"Score count mismatch: got {len(scores)} scores for {len(papers)} papers")
            logger.debug(f"Papers: {len(papers)}, Scores: {scores}")
            return [], True
            
        scored_papers = []
        for i, (paper, score) in enumerate(zip(papers, scores)):
            try:
                relevance = score.get('Relevancy score', 0)
                importance = score.get('Importance score', 0)
                
                if not (1 <= relevance <= 10 and 1 <= importance <= 10):
                    logger.warning(f"Invalid scores for paper {i+1}: relevance={relevance}, importance={importance}")
                    continue
                    
                paper['relevance'] = relevance
                paper['importance'] = importance
                
                if (relevance + importance) / 2 >= threshold:
                    scored_papers.append(paper)
            except Exception as e:
                logger.error(f"Error processing score for paper {i+1}: {e}")
                continue
                
        return scored_papers, False
        
    except json.JSONDecodeError:
        logger.error("Failed to parse scoring response")
        logger.debug(f"Response was: {response}")
        return [], True 