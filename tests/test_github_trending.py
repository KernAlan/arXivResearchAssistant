import os
import json
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from src.services.github_trending import GitHubTrendingService
from src.config import config


class TestGitHubTrendingService(unittest.TestCase):
    def setUp(self):
        self.config = config
        self.service = GitHubTrendingService(self.config)

    def test_parse_number_simple(self):
        """Test parsing simple numbers"""
        self.assertEqual(self.service._parse_number("100"), 100)
        self.assertEqual(self.service._parse_number("1,234"), 1234)
        self.assertEqual(self.service._parse_number("0"), 0)

    def test_parse_number_with_k(self):
        """Test parsing numbers with k suffix"""
        self.assertEqual(self.service._parse_number("1k"), 1000)
        self.assertEqual(self.service._parse_number("1.5k"), 1500)
        self.assertEqual(self.service._parse_number("10.2k"), 10200)

    def test_parse_number_with_m(self):
        """Test parsing numbers with m suffix"""
        self.assertEqual(self.service._parse_number("1m"), 1000000)
        self.assertEqual(self.service._parse_number("1.5m"), 1500000)

    def test_parse_number_with_text(self):
        """Test parsing numbers with extra text like 'stars today'"""
        self.assertEqual(self.service._parse_number("100 stars today"), 100)
        self.assertEqual(self.service._parse_number("1.2k stars"), 1200)

    def test_parse_number_empty(self):
        """Test parsing empty or invalid strings"""
        self.assertEqual(self.service._parse_number(""), 0)
        self.assertEqual(self.service._parse_number("   "), 0)

    def test_parse_trending_page(self):
        """Test parsing HTML from GitHub trending page"""
        sample_html = """
        <html>
        <body>
        <article class="Box-row">
            <h2><a href="/openai/gpt-4">openai/gpt-4</a></h2>
            <p>Next generation language model</p>
            <span itemprop="programmingLanguage">Python</span>
            <a href="/openai/gpt-4/stargazers">50,000</a>
            <span class="d-inline-block float-sm-right">1,000 stars today</span>
        </article>
        <article class="Box-row">
            <h2><a href="/anthropic/claude">anthropic/claude</a></h2>
            <p>AI assistant</p>
            <span itemprop="programmingLanguage">TypeScript</span>
            <a href="/anthropic/claude/stargazers">25k</a>
            <span class="d-inline-block float-sm-right">500 stars today</span>
        </article>
        </body>
        </html>
        """

        repos = self.service._parse_trending_page(sample_html)

        self.assertEqual(len(repos), 2)

        # First repo
        self.assertEqual(repos[0]['name'], 'openai/gpt-4')
        self.assertEqual(repos[0]['description'], 'Next generation language model')
        self.assertEqual(repos[0]['language'], 'Python')
        self.assertEqual(repos[0]['stars'], 50000)
        self.assertEqual(repos[0]['stars_today'], 1000)
        self.assertEqual(repos[0]['url'], 'https://github.com/openai/gpt-4')

        # Second repo
        self.assertEqual(repos[1]['name'], 'anthropic/claude')
        self.assertEqual(repos[1]['language'], 'TypeScript')
        self.assertEqual(repos[1]['stars'], 25000)

    @patch('httpx.get')
    def test_fetch_trending_success(self, mock_get):
        """Test successful fetch of trending repos"""
        mock_response = MagicMock()
        mock_response.text = """
        <html><body>
        <article class="Box-row">
            <h2><a href="/test/repo">test/repo</a></h2>
            <p>Test description</p>
            <a href="/test/repo/stargazers">100</a>
        </article>
        </body></html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        repos = self.service.fetch_trending()

        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]['name'], 'test/repo')
        mock_get.assert_called_once()

    @patch('httpx.get')
    def test_fetch_trending_with_language(self, mock_get):
        """Test fetch with language filter"""
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.service.fetch_trending(language="python", since="weekly")

        args, kwargs = mock_get.call_args
        self.assertIn("python", args[0])
        self.assertEqual(kwargs['params']['since'], 'weekly')

    @patch('httpx.get')
    def test_fetch_trending_failure(self, mock_get):
        """Test handling of fetch failure"""
        mock_get.side_effect = Exception("Network error")

        repos = self.service.fetch_trending()

        self.assertEqual(repos, [])


class TestGitHubTrendingDeduplication(unittest.TestCase):
    def setUp(self):
        """Set up test with temporary seen repos file"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "seen_repos.json"

        # Patch the SEEN_REPOS_FILE constant
        self.patcher = patch('src.services.github_trending.SEEN_REPOS_FILE', self.temp_file)
        self.patcher.start()

        self.service = GitHubTrendingService(config)

    def tearDown(self):
        """Clean up temp files"""
        self.patcher.stop()
        if self.temp_file.exists():
            self.temp_file.unlink()
        Path(self.temp_dir).rmdir()

    def test_get_seen_repos_empty(self):
        """Test getting seen repos when file is empty"""
        self.temp_file.write_text("[]")
        seen = self.service.get_seen_repos()
        self.assertEqual(seen, set())

    def test_mark_seen(self):
        """Test marking repos as seen"""
        self.temp_file.write_text("[]")

        self.service.mark_seen(["repo1", "repo2"])

        seen = self.service.get_seen_repos()
        self.assertIn("repo1", seen)
        self.assertIn("repo2", seen)

    def test_mark_seen_appends(self):
        """Test that mark_seen appends to existing list"""
        self.temp_file.write_text('["existing/repo"]')

        self.service.mark_seen(["new/repo"])

        seen = self.service.get_seen_repos()
        self.assertIn("existing/repo", seen)
        self.assertIn("new/repo", seen)

    def test_filter_new(self):
        """Test filtering out already-seen repos"""
        self.temp_file.write_text('["seen/repo"]')

        repos = [
            {'name': 'seen/repo', 'url': 'https://github.com/seen/repo'},
            {'name': 'new/repo', 'url': 'https://github.com/new/repo'}
        ]

        new_repos = self.service.filter_new(repos)

        self.assertEqual(len(new_repos), 1)
        self.assertEqual(new_repos[0]['name'], 'new/repo')

    def test_filter_new_all_seen(self):
        """Test when all repos have been seen"""
        self.temp_file.write_text('["repo1", "repo2"]')

        repos = [
            {'name': 'repo1'},
            {'name': 'repo2'}
        ]

        new_repos = self.service.filter_new(repos)

        self.assertEqual(len(new_repos), 0)

    def test_seen_repos_limit(self):
        """Test that seen repos list is capped at 1000"""
        self.temp_file.write_text("[]")

        # Mark 1100 repos as seen
        repos = [f"repo{i}" for i in range(1100)]
        self.service.mark_seen(repos)

        # Should only keep last 1000
        data = json.loads(self.temp_file.read_text())
        self.assertEqual(len(data), 1000)


if __name__ == "__main__":
    unittest.main()
