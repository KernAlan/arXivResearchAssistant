ArXiv Research Assistant
====================

Daily digest of new arXiv papers and GitHub trending repos, scored for relevance and delivered with Telegram alerts.

Features
--------

- **ArXiv Digest** — Fetches new papers, scores them with an LLM for relevance, importance, and "arbitrage" discovery potential, then generates an HTML digest.
- **GitHub Trending** — Scrapes GitHub trending repos, scores each for relevance and impact, and generates an HTML report.
- **Telegram Alerts** — Sends real-time notifications for high-scoring papers and repos that cross your configured thresholds.
- **Automated Daily Pipeline** — GitHub Actions workflow runs daily and commits digests to the repo.

Setup
-----

1. Create and activate virtual environment:
   ```
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate
   ```

2. Clone and install:
   ```
   git clone https://github.com/KernAlan/arXivResearchAssistant.git
   cd ArxivResearchAssistant
   pip install -r requirements.txt
   ```

3. Add API keys and Telegram credentials to `.env`:
   ```
   OPENAI_API_KEY=your_key_here
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

4. Run:
   ```
   # Generate arXiv digest
   python -m src.cli generate

   # Generate GitHub trending report
   python -m src.cli github-trending
   ```

   Digests are saved to `digests/`.

Usage
-----

### ArXiv Digest

```
python -m src.cli generate [OPTIONS]
```

| Option | Description |
|---|---|
| `--commit` | Commit digest to git repository |
| `--output-dir` | Output directory (default: `digests`) |
| `--email` | Send digest via email |

### GitHub Trending

```
python -m src.cli github-trending [OPTIONS]
```

| Option | Description |
|---|---|
| `-l, --language` | Filter by language (e.g., `python`) |
| `-s, --since` | Time range: `daily`, `weekly`, `monthly` |
| `-t, --threshold` | Composite score threshold for alerts (default: 8.0) |
| `--dry-run` | Show scores without sending Telegram alerts |
| `--output-dir` | Output directory (default: `digests`) |
| `--no-report` | Skip HTML report generation |

### Score a Single Paper

```
python -m src.cli score -t "Paper Title" -a "Paper abstract text"
```

Configuration
------------

Edit `src/config.py` to customize:
- Topics and categories to monitor
- Filtering keywords
- Model settings (provider, threshold, batch size)
- Research interest profile and arbitrage discovery criteria
- Scoring prompts for both arXiv papers and GitHub repos

### Telegram Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in your `.env`

Papers with an arbitrage score >= 9.0 and GitHub repos with a composite score >= 8.0 trigger Telegram alerts.

### GitHub Actions

The daily pipeline runs at 1:25 PM UTC. To enable it, add these repository secrets:
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Note: arXiv updates at 14:00 UTC (9:00 AM EST) on weekdays. Run once daily after this time.
