"""Tests for the summary generation service and digest template."""

from pathlib import Path
import sys
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.services.summary import SummaryService
from src.templates import digest


def _sample_papers():
    return [
        {
            "title": "<script>alert('x')</script> Detection",
            "abstract": "<b>Impact</b> sentence. Additional context for testing.",
            "relevance": 9,
            "importance": 8,
            "paper_id": "1234.5678",
            "url": "https://arxiv.org/abs/1234.5678?v=1",
        },
        {
            "title": "Trustworthy Agent Framework",
            "abstract": "This approach reduces hallucinations significantly.",
            "relevance": 8,
            "importance": 9,
            "paper_id": "2345.6789",
            "url": "https://arxiv.org/abs/2345.6789",
        },
        {
            "title": "Memory-efficient Retrieval",
            "abstract": "Helps teams cut inference costs while keeping accuracy high.",
            "relevance": 7,
            "importance": 8,
            "paper_id": "3456.7890",
            "url": "https://arxiv.org/abs/3456.7890",
        },
    ]


def _service():
    return SummaryService({"top_p": 1.0, "provider": "openai"})


@patch("src.services.summary.openai_completion", return_value="   ")
def test_generate_summary_uses_deterministic_fallback(mock_completion):
    service = _service()
    summary_html = service.generate_summary(_sample_papers())

    assert mock_completion.called
    # When API returns empty/whitespace, should use fallback with structured list
    assert "<ol>" in summary_html
    assert "<li>" in summary_html
    assert "<strong>" in summary_html
    # HTML should be escaped
    assert "<script" not in summary_html
    assert "&lt;script&gt;" in summary_html


@patch("src.services.summary.openai_completion", side_effect=RuntimeError("boom"))
def test_render_digest_includes_key_highlights_when_model_fails(_mock_completion):
    service = _service()
    summary_html = service.generate_summary(_sample_papers())
    html = digest.render_digest(
        papers=_sample_papers(),
        summary=summary_html,
        total_papers=6,
        threshold=7.5,
        had_hallucination=False,
    )

    assert "🔥 Key Highlights" in html
    # When model fails, fallback summary should be included
    assert "<ol>" in html
    assert "<li>" in html
    assert "<strong>" in html
