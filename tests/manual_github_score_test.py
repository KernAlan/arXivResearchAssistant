"""Manual test script for GitHub repo scoring"""
import json
from dotenv import load_dotenv
load_dotenv()

from src.config import config
from src.utils import openai_completion, OpenAIDecodingArguments


def score_repo(name, desc, lang, stars, stars_today):
    prompt = f"""{config.github_scoring_prompt}

Repository:
- Name: {name}
- Description: {desc}
- Language: {lang}
- Stars: {stars} ({stars_today} today)

Return only valid JSON: {{"score": N, "reason": "..."}}"""

    response = openai_completion(
        prompt,
        OpenAIDecodingArguments(max_tokens=16000),
        model_name=config.model.get('name'),
        provider=config.model.get('provider')
    )
    cleaned = response.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.split('\n', 1)[1]
    if cleaned.endswith('```'):
        cleaned = cleaned.rsplit('\n', 1)[0]
    return json.loads(cleaned)


def main():
    # Fictional repos - low, medium, high, game-changer
    repos = [
        ('cryptobro/nft-generator-3000', 'Generate unique NFT art collections with AI', 'JavaScript', 2300, 180),
        ('devops-dan/kubectl-helper', 'CLI wrapper for common kubectl commands', 'Go', 8500, 95),
        ('writecraft/prose-polish', 'AI-powered grammar and style checker for long-form writing with context awareness', 'Python', 4200, 320),
        ('agentforge/reliable-agents', 'Framework for building self-healing AI agents with automatic error recovery and state persistence', 'Python', 12000, 890),
        ('coherence-ai/infinite-writer', 'Generate book-length content with perfect coherence - maintains character, plot, and style across 100k+ tokens', 'Python', 1800, 1200),
    ]

    print('FICTIONAL GITHUB REPOS - SCORING TEST')
    print('=' * 70)

    for name, desc, lang, stars, today in repos:
        result = score_repo(name, desc, lang, stars, today)
        score = result.get('score', 0)
        reason = result.get('reason', 'No reason')
        icon = '>>' if score >= 9 else '  '
        print(f'{icon} [{score:>2}/10] {name}')
        print(f'          {desc[:55]}...')
        print(f'          {reason}')
        print()


if __name__ == '__main__':
    main()
