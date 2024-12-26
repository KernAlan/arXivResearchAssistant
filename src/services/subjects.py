"""Subject field processing for arXiv papers"""
import logging
import re
from typing import List
from ..config import config

logger = logging.getLogger(__name__)

def process_subject_fields(subjects: str) -> List[str]:
    """Process subject fields into categories"""
    categories = []
    for subject in subjects.split(', '):
        if subject in config.ARXIV_CONFIG["categories"]:
            categories.append(config.ARXIV_CONFIG["categories"][subject])
    
    return categories 