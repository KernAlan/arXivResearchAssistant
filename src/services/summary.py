"""Summary generation service"""
import logging
from datetime import datetime
from typing import Dict, List

from ..config import config
from ..utils import OpenAIDecodingArguments, openai_completion

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self, model_config):
        self.model_config = model_config
        self.config = config  # Add reference to global config
    
    def generate_summary(self, papers: List[Dict]) -> str:
        """Generate a summary of the papers"""
        if not papers:
            return self._wrap_summary_html("No papers found matching your interests.")
            
        # Sort papers by combined score
        sorted_papers = sorted(
            papers,
            key=lambda x: (x["relevance"] + x["importance"])/2,
            reverse=True
        )
        
        # Take top N papers for summary
        top_papers = sorted_papers[:self.config.PAPER_CONFIG["summary_papers"]]
        
        if not top_papers:
            return "No high-scoring papers met the relevance threshold today."

        # Create prompt
        prompt_pieces = []
        for idx, paper in enumerate(top_papers, start=1):
            avg_score = (paper["relevance"] + paper["importance"]) / 2
            paper_url = paper.get("url") or f"https://arxiv.org/abs/{paper.get('paper_id', '')}"
            prompt_pieces.append(
                "\n".join(
                    [
                        f"Paper {idx}:",
                        f"Title: {paper['title']}",
                        f"Average score: {avg_score:.1f}/10 (Relevance {paper['relevance']}/10, Importance {paper['importance']}/10)",
                        f"Abstract: {paper['abstract']}",
                        f"URL: {paper_url}",
                    ]
                )
            )

        papers_text = "\n\n".join(prompt_pieces)

        today = datetime.utcnow().strftime("%B %d, %Y")
        prompt = f"""You are preparing the executive digest for {today}.\n\n"""
        prompt += """Audience: Head of AI Engineering who wants clear takeaways.\n"""
        prompt += """There are {count} high-scoring papers today. Reference why each matters using the scores and abstract details provided.\n""".format(count=len(top_papers))
        prompt += """Follow the style guide in the system prompt. Each bullet must:\n- Open with the paper title in bold.\n- In one sentence, explain the concrete innovation or finding.\n- In a second sentence, describe the practical impact or next step for industry teams.\nInclude the provided URL inline when useful.\nClose with one upbeat sentence on how the team should act on these findings this week."""
        prompt += "\n\nPapers to summarize:\n" + papers_text

        try:
            response = openai_completion(
                prompt,
                OpenAIDecodingArguments(
                    temperature=self.model_config.get("summary_temperature", 0.5),
                    max_tokens=900,
                    top_p=self.model_config.get("top_p", 1.0)
                ),
                model_name=self.model_config.get("summary_name", self.model_config.get("name", "gpt-5-mini")),
                provider=self.model_config.get("provider", "openai"),
                system_prompt=self.config.SUMMARY_SYSTEM_PROMPT.strip()
            )

            # Response is now a string, not an object
            return response
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._build_default_summary(top_papers)

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

    def _build_default_summary(self, papers: List[Dict]) -> str:
        """Build a deterministic HTML summary when the model response is empty."""
        if not papers:
            return "No high-scoring papers met the relevance threshold today."

        summary_items = []
        for paper in papers:
            avg_score = (paper["relevance"] + paper["importance"]) / 2
            paper_url = paper.get("url") or f"https://arxiv.org/abs/{paper.get('paper_id', '')}"
            impact_sentence = paper["abstract"].split(".")[0].strip()
            if not impact_sentence:
                impact_sentence = "See abstract for details."
            summary_items.append(
                (
                    "<li><strong>{title}</strong> — avg score {avg:.1f}/10. {impact} "
                    "<a href=\"{url}\">Read more</a>.</li>"
                ).format(
                    title=paper["title"],
                    avg=avg_score,
                    impact=impact_sentence,
                    url=paper_url
                )
            )

        return "<ol>" + "".join(summary_items) + "</ol>"
