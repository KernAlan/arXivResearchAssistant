import dataclasses
import logging
import math
import os
import sys
import time
from typing import Optional, Sequence, Union
from openai import OpenAI
import tqdm
import json
import datetime
import pytz
from bs4 import BeautifulSoup as bs
import urllib.request

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class OpenAIDecodingArguments(object):
    max_tokens: int = 1800
    temperature: float = 0.2
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    stop: Optional[Sequence[str]] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

def setup_client(provider="openai"):
    """Setup API client based on provider"""
    if provider == "groq":
        return OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
        )
    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        timeout=60.0
    )

def openai_completion(
    prompts,
    decoding_args: OpenAIDecodingArguments,
    model_name: str,
    provider: str = "openai",
    sleep_time: int = 2,
    batch_size: int = 1,
    max_instances: int = sys.maxsize,
    return_text: bool = False,
    **decoding_kwargs,
):
    """Modern OpenAI API completion function.
    
    Args:
        prompts: Single prompt or list of prompts
        decoding_args: Decoding arguments
        model_name: Name of the model to use
        provider: 'openai' or 'groq'
        sleep_time: Time to sleep between retries
        batch_size: Number of prompts per batch
        max_instances: Maximum number of prompts to process
        return_text: If True, return only the text content
        decoding_kwargs: Additional kwargs for completion
    """
    # Initialize client
    client = setup_client(provider)
    
    # Handle single prompt
    is_single_prompt = isinstance(prompts, (str, dict))
    if is_single_prompt:
        prompts = [prompts]
    
    # Limit number of prompts
    prompts = prompts[:max_instances]
    
    # Create batches
    prompt_batches = [
        prompts[i:i + batch_size] 
        for i in range(0, len(prompts), batch_size)
    ]
    
    completions = []
    for batch in tqdm.tqdm(prompt_batches, desc="Processing batches"):
        backoff = 3
        while True:
            try:
                # Prepare completion arguments
                completion_args = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": batch[0]}
                    ],
                    **dataclasses.asdict(decoding_args),
                    **decoding_kwargs
                }
                
                # Make API call
                completion = client.chat.completions.create(**completion_args)
                
                # Process response
                for choice in completion.choices:
                    if return_text:
                        completions.append(choice.message.content)
                    else:
                        completions.append(choice.message)
                break
                
            except Exception as e:
                logging.warning(f"Error during completion: {e}")
                if "Please reduce your prompt" in str(e):
                    decoding_args.max_tokens = int(decoding_args.max_tokens * 0.8)
                    logging.warning(f"Reducing max_tokens to {decoding_args.max_tokens}")
                elif not backoff:
                    logging.error("Max retries reached")
                    raise e
                else:
                    backoff -= 1
                    logging.warning(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
    
    # Return single result if single input
    if is_single_prompt and len(completions) == 1:
        return completions[0]
    
    return completions

def write_ans_to_file(ans_data, file_prefix, output_dir="./output"):
    """Write results to file"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = os.path.join(output_dir, file_prefix + ".txt")
    with open(filename, "w") as f:
        for ans in ans_data:
            f.write(ans + "\n")

def _download_new_papers(field_abbr):
    """Download new papers from arXiv for a given field"""
    NEW_SUB_URL = f'https://arxiv.org/list/{field_abbr}/new'
    page = urllib.request.urlopen(NEW_SUB_URL)
    soup = bs(page, features="html.parser")
    content = soup.body.find("div", {'id': 'content'})

    dt_list = content.dl.find_all("dt")
    dd_list = content.dl.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"

    new_paper_list = []
    for i in tqdm.tqdm(range(len(dt_list))):
        paper = {}
        paper_number = dt_list[i].text.strip().split(" ")[2].split(":")[-1]
        paper['main_page'] = arxiv_base + paper_number
        paper['pdf'] = arxiv_base.replace('abs', 'pdf') + paper_number

        paper['title'] = dd_list[i].find("div", {"class": "list-title mathjax"}).text.replace("Title: ", "").strip()
        paper['authors'] = dd_list[i].find("div", {"class": "list-authors"}).text.replace("Authors:\n", "").replace("\n", "").strip()
        paper['subjects'] = dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects: ", "").strip()
        paper['abstract'] = dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()
        new_paper_list.append(paper)

    return new_paper_list

def get_papers(topic: str, categories: list = None) -> list:
    """Get papers from arXiv for given topic and categories"""
    from . import config  # Import the config module
    
    # Get topic abbreviation and download papers
    abbr = config.config.get_topic_abbreviation(topic)  # Use the singleton instance
    papers = _download_new_papers(abbr)
    
    initial_count = len(papers)
    
    # Apply filters
    if categories:
        papers = [
            paper for paper in papers
            if any(cat in paper['subjects'] for cat in categories)
        ]
    
    # Apply keyword filtering
    papers = filter_ai_papers(papers, config.config._config)  # Pass the config dict
    
    # Log summary
    logger.info(
        f"Papers filtered: {initial_count} → {len(papers)} "
        f"({len(papers)/initial_count:.1%} kept)"
    )
    
    return papers

def create_scoring_prompt(interest: str, papers: list) -> str:
    """Create prompt for scoring papers.
    
    Args:
        interest: Interest statement from config
        papers: List of papers to score
    """
    # Load base prompt
    with open("src/relevancy_prompt.txt") as f:
        base_prompt = f.read()
    
    # Add interest statement
    prompt = base_prompt + "\n" + interest + "\n\n"
    
    # Add papers
    for i, paper in enumerate(papers, 1):
        prompt += f"###\n"
        prompt += f"{i}. Title: {paper['title']}\n"
        prompt += f"{i}. Authors: {paper['authors']}\n"
        prompt += f"{i}. Abstract: {paper['abstract']}\n"
    
    prompt += "\nGenerate response:\n1."
    return prompt

def process_scoring_response(papers: list, response, threshold: float = 7.5) -> tuple[list, bool]:
    """Process LLM response into scored papers."""
    scored_papers = []
    had_hallucination = False
    
    # Parse response into lines
    content = response.choices[0].message.content
    logger.debug(f"Raw LLM response: {content}")
    
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    
    # Extract scores
    try:
        items = []
        for line in lines:
            if "relevancy score" not in line.lower():
                continue
                
            # Handle different response formats
            try:
                if ". {" in line:
                    json_str = line.split(". ", 1)[1]
                else:
                    json_str = line
                
                item = json.loads(json_str)
                items.append(item)
            except (IndexError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to parse line: {line}")
                continue
                
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {str(e)}")
        return [], True
        
    # Check for hallucination
    if len(items) != len(papers):
        logger.warning(f"Mismatch in number of scores ({len(items)}) and papers ({len(papers)})")
        items = items[:len(papers)]
        had_hallucination = True
    
    # Process each paper
    for paper, item in zip(papers, items):
        try:
            # Parse score
            score = item["Relevancy score"]
            if isinstance(score, str) and "/" in score:
                score = float(score.split("/")[0])
            else:
                score = float(score)
                
            # Skip if below threshold
            if score < threshold:
                continue
                
            # Add score to paper
            paper_with_score = paper.copy()
            paper_with_score["score"] = score
            scored_papers.append(paper_with_score)
            
        except (KeyError, ValueError) as e:
            logger.warning(f"Failed to process paper score: {str(e)}")
            continue
    
    # Add debug logging
    content = response.choices[0].message.content
    logger.debug(f"Raw response content:\n{content}")
    
    # After parsing scores
    if items:
        logger.debug(f"Parsed scores: {items}")
    else:
        logger.warning("No scores parsed from response")
    
    return scored_papers, had_hallucination

def get_topic_abbreviation(topic: str) -> str:
    """Convert topic name to arXiv abbreviation."""
    from . import config  # Import here to avoid circular imports
    
    if topic == "Physics":
        raise ValueError("Must specify a physics subtopic")
    elif topic in config.PHYSICS_SUBTOPICS:
        return config.PHYSICS_SUBTOPICS[topic]
    elif topic in config.ARXIV_TOPICS:
        return config.ARXIV_TOPICS[topic]
    else:
        raise ValueError(f"Invalid topic: {topic}")

def create_quick_scoring_prompt(interest: str, papers: list) -> str:
    """Create a minimal prompt for initial quick scoring.
    
    Args:
        interest: Interest statement from config
        papers: List of papers to score
    """
    prompt = """Rate these papers from 1-10 based on relevance to my interests.
Respond with only scores in JSON format like:
1. {"Relevancy score": 8}
2. {"Relevancy score": 3}

My interests are:
"""
    
    # Add interest statement
    prompt += interest + "\n\n"
    
    # Add papers (title and brief abstract only)
    for i, paper in enumerate(papers, 1):
        prompt += f"{i}. Title: {paper['title']}\n"
        # Take first 200 characters of abstract for quick assessment
        brief_abstract = paper['abstract'][:200] + "..."
        prompt += f"   Abstract: {brief_abstract}\n\n"
    
    return prompt

def filter_ai_papers(papers: list, config: dict) -> list:
    """Pre-filter papers related to applied AI/LLMs"""
    
    # Define filtering keywords (could move to config.yaml if needed)
    primary_keywords = {
        'rag', 'retrieval augmented', 'vector database', 'vector store',
        'llm application', 'ai agent', 'prompt engineering',
        'production deployment', 'enterprise ai', 'business case',
        'ai system', 'llm system', 'ai engineering', 'agents',
        'agent', 'agentic framework', 'orchestration', 'LangGraph',
        'Langchain', 'graph database', 'embedding model', 'benchmark',
        'fine tuning'
    }
    
    secondary_keywords = {
        'production', 'deployment', 'enterprise', 'business',
        'implementation', 'integration', 'infrastructure',
        'cost', 'performance', 'scaling', 'monitoring',
        'reliability', 'observability', 'evaluation',
        'embeddings', 'orchestration', 'automation',
        'real-world', 'case study', 'industry', 'agents',
        'agent', 'agentic framework', 'LangGraph', 'Langchain',
        'graph database', 'embedding model', 'benchmark', 'fine tuning'
    }
    
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
        if secondary_count >= 2:  # Must match at least 2 secondary keywords
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

