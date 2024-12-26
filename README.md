ArXiv Research Assistant
====================

Daily digest of new arXiv papers relevant to AI engineering.

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

3. Add OpenAI API key to .env:
   ```
   OPENAI_API_KEY=your_key_here
   ```

4. Run:
   ```
   python -m src.cli generate
   ```

   Digests are saved to `digests/arxiv_digest_YYYYMMDD_HHMMSS.html`

Configuration
------------

Edit config.py to customize:
- Topics and categories to monitor
- Filtering criteria
- Model settings
- Research interests

Note: arXiv updates at 14:00 UTC (9:00 AM EST) on weekdays. Run once daily after this time.
