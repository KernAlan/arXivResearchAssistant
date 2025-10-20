"""ArXiv paper downloading service"""
import logging
import ssl
import urllib.request
from typing import Dict, List
from bs4 import BeautifulSoup as bs
from urllib.parse import quote
from ..config import config
from datetime import datetime, timedelta
import pytz
from ..utils.last_run import get_last_run_date

logger = logging.getLogger(__name__)

class ArxivService:
    BASE_URL = 'https://arxiv.org/list/{}/new'
    ARXIV_ABS = 'https://arxiv.org/abs/'
    ARXIV_PDF = 'https://arxiv.org/pdf/'
    
    # ArXiv category mappings
    CATEGORY_MAPPINGS = {
        'cs': 'cs',  # Computer Science
        'cs.AI': 'cs.AI',  # Artificial Intelligence
        'cs.CL': 'cs.CL',  # Computation and Language
        'cs.LG': 'cs.LG',  # Machine Learning
    }
    
    def get_new_papers(self, topic: str) -> List[Dict]:
        """Get new papers from arXiv"""
        # Get last run date from file, or default to 1 day ago
        last_run = get_last_run_date()
        current_time = datetime.now(pytz.UTC)
        
        # Format dates for ArXiv API (YYYYMMDD format)
        date_str = last_run.strftime("%Y%m%d")
        current_date = current_time.strftime("%Y%m%d")
        
        # Get categories from config
        categories = config.ARXIV_CONFIG["categories"].keys()
        
        # Construct query for multiple categories
        category_query = ' OR '.join(f'cat:{cat}' for cat in categories)
        query = f'({category_query}) AND lastUpdatedDate:[{date_str}0000 TO {current_date}235959]'
        
        url = (f"{config.ARXIV_CONFIG['base_url']}?"
               f"search_query={quote(query)}&"
               f"sortBy={config.ARXIV_CONFIG['sort_by']}&"
               f"sortOrder={config.ARXIV_CONFIG['sort_order']}&"
               f"max_results={config.ARXIV_CONFIG['max_results']}")
        
        logger.debug(f"Fetching papers since {last_run.date()}")
        logger.debug(f"Using URL: {url}")
        
        try:
            # Create SSL context that doesn't verify certificates (for Windows compatibility)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Get XML response
            response = urllib.request.urlopen(url, context=ssl_context)
            soup = bs(response, 'lxml-xml')
            
            # Parse entries
            papers = []
            entries = soup.find_all('entry')
            logger.info(f"Found {len(entries)} papers in feed")
            
            for entry in entries:
                try:
                    # Get all categories
                    primary_cat = entry.find('arxiv:primary_category')['term']
                    categories = [primary_cat]
                    for cat in entry.find_all('category'):
                        cat_term = cat.get('term')
                        if cat_term and cat_term not in categories:
                            categories.append(cat_term)
                    
                    paper = {
                        'title': entry.title.text.strip().replace('\n', ' '),
                        'abstract': entry.summary.text.strip().replace('\n', ' '),
                        'subjects': ', '.join(categories),
                        'paper_id': entry.id.text.split('/abs/')[-1],
                        'url': entry.id.text
                    }
                    papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing entry: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return [] 