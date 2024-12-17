ArXiv Research Digest
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
   git clone https://github.com/yourusername/ArxivDigest.git
   cd ArxivDigest
   pip install -r requirements.txt
   ```

3. Add OpenAI API key to .env:
   ```
   OPENAI_API_KEY=your_key_here
   ```

4. Run:
   ```
   python -m src.cli
   ```

   Digests are saved to `digests/arxiv_digest_YYYYMMDD_HHMMSS.html`

Configuration
------------

Edit config.yaml to customize:
- Topics and categories to monitor
- Filtering criteria
- Model settings
- Research interests

Scheduling
---------

Windows:
```
schtasks /create /tn "ArXiv Digest" /tr "C:\path\to\venv\Scripts\python.exe -m src.cli" /sc weekly /d MON,TUE,WED,THU,FRI /st 09:30
```

Linux/Mac:
```
30 9 * * 1-5 /path/to/venv/bin/python -m src.cli
```

Note: arXiv updates at 14:00 UTC (9:00 AM EST) on weekdays. Run once daily after this time.
