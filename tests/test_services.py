from src.services.slack import _format_blocks
from src.models.schemas import ScreeningNote


class TestSlackFormatting:
    """Test Slack Block Kit message formatting."""

    def test_format_blocks_returns_valid_structure(self):
        note = ScreeningNote(
            company_name="TestCo",
            business_summary="TestCo is a test company.",
            business_model="SaaS subscription model.",
            market="$10B TAM, growing 15% YoY.",
            traction_signals="Series A, $5M raised.",
            fit_assessment="Interesting early-stage opportunity.",
        )
        blocks = _format_blocks(note, "@analyst")

        # Should have: header, divider, 5 sections, divider, context = 9 blocks
        assert len(blocks) == 9
        assert blocks[0]["type"] == "header"
        assert "TestCo" in blocks[0]["text"]["text"]
        assert blocks[-1]["type"] == "context"
        assert "@analyst" in blocks[-1]["elements"][0]["text"]

    def test_format_blocks_all_sections_present(self):
        note = ScreeningNote(
            company_name="Acme",
            business_summary="Summary.",
            business_model="Model.",
            market="Market.",
            traction_signals="Traction.",
            fit_assessment="Fit.",
        )
        blocks = _format_blocks(note, "@user")
        section_texts = [
            b["text"]["text"] for b in blocks if b["type"] == "section"
        ]

        assert any("Business Summary" in t for t in section_texts)
        assert any("Business Model" in t for t in section_texts)
        assert any("Market" in t for t in section_texts)
        assert any("Traction Signals" in t for t in section_texts)
        assert any("Initial Fit Assessment" in t for t in section_texts)
