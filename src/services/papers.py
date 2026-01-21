"""Paper fetching and processing service"""
import logging
from typing import Dict, List, Tuple
from .. import utils
from ..utils import filter_ai_papers
from .. import relevancy
from ..constants import get_topic_abbreviation
from .summary import SummaryService
from .arxiv import ArxivService
from .subjects import process_subject_fields
from .telegram import TelegramService

logger = logging.getLogger(__name__)

class PaperService:
    def __init__(self, config: Dict):
        self.config = config
        self.summary_service = SummaryService(config.model)
        self.arxiv_service = ArxivService()
        self.telegram_service = TelegramService(config)
    
    def get_papers(self) -> List[Dict]:
        """Get papers based on config"""
        logger.info("Fetching papers...")
        topic = self.config.user["topic"]
        abbr = get_topic_abbreviation(topic)
        logger.info(f"Using topic {topic} with abbreviation {abbr}")
        
        # Use cs.AI for AI papers
        if abbr == "cs" and "Artificial Intelligence" in self.config.user.get("categories", []):
            abbr = "cs.AI"
        
        papers = self.arxiv_service.get_new_papers(abbr)
        logger.info(f"Retrieved {len(papers)} papers")
        
        # Log a sample paper for debugging
        if papers:
            sample_paper = papers[0]
            logger.debug(f"Sample paper subjects: {sample_paper['subjects']}")
            logger.debug(f"Processed categories: {process_subject_fields(sample_paper['subjects'])}")
        
        # Apply category filtering if specified
        categories = self.config.user.get("categories", [])
        if categories:
            logger.info(f"Filtering by categories: {categories}")
            filtered_papers = []
            for paper in papers:
                paper_categories = process_subject_fields(paper['subjects'])
                if bool(set(paper_categories) & set(categories)):
                    filtered_papers.append(paper)
                else:
                    logger.debug(f"Paper filtered out. Categories: {paper_categories}")
            
            papers = filtered_papers
            logger.info(f"After filtering: {len(papers)} papers")
        
        return papers
    
    def process_papers(self, papers: list) -> tuple[list, bool]:
        """Process and score papers"""
        # Filter papers
        papers = filter_ai_papers(papers, self.config)
        logger.info(f"After filtering: {len(papers)} papers")
        
        # Score papers
        logger.info("Scoring papers...")
        scored_papers, had_hallucination = relevancy.score_papers(
            papers,
            self.config.interest,
            self.config.model,
            threshold=self.config.model.get("threshold", 7.5),
            arbitrage_interest=self.config.arbitrage_interest,
            arbitrage_threshold=self.config.model.get("arbitrage_threshold", 8.5)
        )

        # Send Telegram alerts for high arbitrage papers
        arbitrage_threshold = self.config.model.get("arbitrage_threshold", 8.5)
        for paper in scored_papers:
            if paper.get('arbitrage_score', 0) >= arbitrage_threshold:
                logger.info(f"Found arbitrage paper: {paper['title']}. Sending Telegram alert...")
                self.telegram_service.send_alert(paper)

        return scored_papers, had_hallucination
    
    def generate_summary(self, scored_papers: List[Dict]) -> str:
        """Generate executive summary"""
        logger.info("Generating summary...")
        return self.summary_service.generate_summary(scored_papers) 