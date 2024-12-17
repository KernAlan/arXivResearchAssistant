"""Paper relevancy scoring using LLMs"""
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import os
import backoff

from openai import AsyncOpenAI
import tqdm
import time

from . import config
from . import utils

logger = logging.getLogger(__name__)

@backoff.on_exception(
    backoff.expo,
    (aiohttp.ClientError, asyncio.TimeoutError),
    max_tries=3,
    max_time=30
)
async def score_batch_async(
    client: AsyncOpenAI,
    batch: List[Dict],
    interest: str,
    model_config: Dict,
    is_quick_scoring: bool = True
) -> Tuple[List[Dict], bool]:
    """Score a single batch of papers asynchronously"""
    try:
        # Create appropriate prompt
        if is_quick_scoring:
            prompt = utils.create_quick_scoring_prompt(interest, batch)
            temperature = 0.3
        else:
            prompt = utils.create_scoring_prompt(interest, batch)
            temperature = model_config.get("temperature", 0.7)
        
        response = await client.chat.completions.create(
            model=model_config["name"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            timeout=30.0
        )
        
        threshold = 5 if is_quick_scoring else model_config.get("threshold", 7.5)
        return utils.process_scoring_response(batch, response, threshold)
        
    except Exception as e:
        logger.error(f"Batch scoring failed: {str(e)}")
        return [], True

async def score_papers_async(
    papers: List[Dict],
    interest: str,
    model_config: Optional[Dict] = None,
    threshold: float = 7.5,
    batch_size: int = 8,
    max_concurrent: int = 5
) -> Tuple[List[Dict], bool]:
    """Score papers using concurrent processing"""
    model_config = model_config or config.get_model_config()
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        timeout=aiohttp.ClientTimeout(total=60),
        max_retries=3
    )
    
    logger.info(f"Scoring {len(papers)} papers with {max_concurrent} concurrent requests")
    
    # Initialize variables
    all_quick_scores = []
    had_hallucination = False
    
    # Add delay between batches
    async def process_batch_with_delay(batch):
        async with semaphore:
            result = await score_batch_async(client, batch, interest, model_config, True)
            await asyncio.sleep(0.5)
            return result
    
    # Process in smaller chunks to avoid overwhelming the API
    chunk_size = 50
    
    for chunk_start in range(0, len(papers), chunk_size):
        chunk = papers[chunk_start:chunk_start + chunk_size]
        batches = [
            chunk[i:i + batch_size * 2] 
            for i in range(0, len(chunk), batch_size * 2)
        ]
        
        # Process chunk with semaphore
        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = [process_batch_with_delay(batch) for batch in batches]
        
        for result in tqdm.tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc=f"Quick scoring chunk {chunk_start//chunk_size + 1}"
        ):
            scores, hallu = await result
            all_quick_scores.extend(scores)
            had_hallucination = had_hallucination or hallu
            
        # Add delay between chunks
        await asyncio.sleep(1.0)
    
    # Keep top papers
    top_papers = sorted(all_quick_scores, key=lambda x: x["score"], reverse=True)[:20]
    logger.info(f"Selected top {len(top_papers)} papers for detailed scoring")
    
    # After quick scoring
    logger.info(
        f"Quick scoring results:\n"
        f"  Papers processed: {len(papers)}\n"
        f"  Papers scored: {len(all_quick_scores)}\n"
        f"  Score distribution: "
        + ', '.join(
            f"{s}:{len([p for p in all_quick_scores if p.get('score') == s])}"
            for s in range(1,11)
        )
    )
    
    # Second stage: Detailed scoring
    final_scores = []
    
    # Create batches for detailed scoring
    detail_batches = [
        top_papers[i:i + batch_size]
        for i in range(0, len(top_papers), batch_size)
    ]
    
    # Process detailed scoring concurrently
    tasks = [
        process_batch_with_delay(batch) 
        for batch in detail_batches
    ]
    
    for result in tqdm.tqdm(
        asyncio.as_completed(tasks),
        total=len(tasks),
        desc="Detailed scoring"
    ):
        scores, hallu = await result
        final_scores.extend(scores)
        had_hallucination = had_hallucination or hallu
    
    # After detailed scoring
    logger.info(
        f"Detailed scoring results:\n"
        f"  Papers processed: {len(top_papers)}\n"
        f"  Papers above threshold: {len(final_scores)}\n"
        f"  Score distribution: "
        + ', '.join(
            f"{s}:{len([p for p in final_scores if p.get('score') == s])}"
            for s in range(1,11)
        )
    )
    
    if had_hallucination:
        logger.warning("Some responses may contain hallucinations")
    
    logger.info(f"Final selection: {len(final_scores)} papers above threshold {threshold}")
    return sorted(final_scores, key=lambda x: x["score"], reverse=True), had_hallucination

def score_papers(*args, **kwargs) -> Tuple[List[Dict], bool]:
    """Synchronous wrapper for async scoring function"""
    return asyncio.run(score_papers_async(*args, **kwargs))
