"""GitHub Trending Service - Fetch and score trending repositories"""
import os
import json
import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

SEEN_REPOS_FILE = Path("data/seen_repos.json")


class GitHubTrendingService:
    def __init__(self, config):
        self.config = config
        self.base_url = "https://github.com/trending"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        SEEN_REPOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not SEEN_REPOS_FILE.exists():
            SEEN_REPOS_FILE.write_text("[]")

    def fetch_trending(self, language: str = "", since: str = "daily") -> List[Dict]:
        """
        Fetch trending repositories from GitHub.

        Args:
            language: Filter by language (e.g., "python", "javascript", or "" for all)
            since: Time range - "daily", "weekly", or "monthly"
        """
        url = self.base_url
        if language:
            url = f"{url}/{language}"

        params = {"since": since}

        try:
            response = httpx.get(url, params=params, timeout=30.0, follow_redirects=True)
            response.raise_for_status()
            return self._parse_trending_page(response.text)
        except Exception as e:
            logger.error(f"Failed to fetch GitHub trending: {e}")
            return []

    def _parse_trending_page(self, html: str) -> List[Dict]:
        """Parse the GitHub trending page HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        repos = []

        for article in soup.select('article.Box-row'):
            try:
                # Repository name (owner/repo)
                name_elem = article.select_one('h2 a')
                if not name_elem:
                    continue

                full_name = name_elem.get('href', '').strip('/')

                # Description
                desc_elem = article.select_one('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ""

                # Language
                lang_elem = article.select_one('[itemprop="programmingLanguage"]')
                language = lang_elem.get_text(strip=True) if lang_elem else "Unknown"

                # Stars
                stars_elem = article.select_one('a[href$="/stargazers"]')
                stars_text = stars_elem.get_text(strip=True) if stars_elem else "0"
                stars = self._parse_number(stars_text)

                # Stars today
                stars_today_elem = article.select_one('span.d-inline-block.float-sm-right')
                stars_today_text = stars_today_elem.get_text(strip=True) if stars_today_elem else "0"
                stars_today = self._parse_number(stars_today_text)

                # Topics/tags (from repo page - we'll skip for now to avoid extra requests)

                repos.append({
                    'name': full_name,
                    'url': f"https://github.com/{full_name}",
                    'description': description,
                    'language': language,
                    'stars': stars,
                    'stars_today': stars_today
                })

            except Exception as e:
                logger.warning(f"Failed to parse repo: {e}")
                continue

        logger.info(f"Found {len(repos)} trending repositories")
        return repos

    def _parse_number(self, text: str) -> int:
        """Parse numbers like '1,234' or '1.2k' """
        text = text.lower().replace(',', '').replace(' ', '')
        text = text.replace('stars', '').replace('today', '').strip()

        try:
            if 'k' in text:
                return int(float(text.replace('k', '')) * 1000)
            elif 'm' in text:
                return int(float(text.replace('m', '')) * 1000000)
            else:
                return int(float(text)) if text else 0
        except:
            return 0

    def get_seen_repos(self) -> set:
        """Get set of already-seen repository names"""
        try:
            data = json.loads(SEEN_REPOS_FILE.read_text())
            return set(data)
        except:
            return set()

    def mark_seen(self, repo_names: List[str]):
        """Mark repositories as seen"""
        seen = self.get_seen_repos()
        seen.update(repo_names)
        # Keep only last 1000 to avoid unbounded growth
        seen_list = list(seen)[-1000:]
        SEEN_REPOS_FILE.write_text(json.dumps(seen_list))

    def filter_new(self, repos: List[Dict]) -> List[Dict]:
        """Filter out already-seen repositories"""
        seen = self.get_seen_repos()
        new_repos = [r for r in repos if r['name'] not in seen]
        logger.info(f"Filtered to {len(new_repos)} new repositories (from {len(repos)})")
        return new_repos
