"""Summary generation service"""
import logging
from .. import utils
from ..config import config
from datetime import datetime
import json
from typing import List, Dict

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self, model_config):
        self.model_config = model_config
        self.config = config  # Add reference to global config
    
    def generate_summary(self, papers: List[Dict]) -> str:
        """Generate a summary of the papers"""
        if not papers:
            return "No papers found matching your interests."
            
        # Sort papers by combined score
        sorted_papers = sorted(
            papers,
            key=lambda x: (x["relevance"] + x["importance"])/2,
            reverse=True
        )
        
        # Take top N papers for summary
        top_papers = sorted_papers[:self.config.PAPER_CONFIG["summary_papers"]]
        
        # Create prompt
        papers_text = "\n\n".join(
            f"Title: {p['title']}\nAbstract: {p['abstract']}\nRelevance: {p['relevance']}, Importance: {p['importance']}"
            for p in top_papers
        )
        
        prompt = self.config.SUMMARY_SYSTEM_PROMPT + "\n\nPapers to summarize:\n" + papers_text
        
        try:
            response = utils.openai_completion(
                prompt,
                utils.OpenAIDecodingArguments(
                    temperature=1.0,
                    max_tokens=1000
                ),
                model_name=self.model_config.get("name", "gpt-4"),
                provider=self.model_config.get("provider", "openai")
            )
            
            # Response is now a string, not an object
            return response
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error generating summary. Please check the logs for details."

    def _render_papers(self, papers: list) -> str:
        """Render individual paper sections"""
        return "\n".join(
            f"""
            <div class='paper'>
                <h3>{p['title']}</h3>
                <div class='scores'>
                    <span class='score relevance'>Relevance: {p['relevance']}/10</span>
                    <span class='score importance'>Importance: {p['importance']}/10</span>
                </div>
                <div class='abstract'>{p['abstract']}</div>
                <div class='meta'>
                    <a href="{p.get('url', f'https://arxiv.org/abs/{p.get("paper_id", "")}')}">View on arXiv</a>
                </div>
            </div>
            """
            for p in papers
        ) 