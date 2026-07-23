from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apps.admin_agent.services.research import MAX_CITIES, run_web_research


def _grounded_response(text, chunks=None):
    grounding_metadata = SimpleNamespace(grounding_chunks=chunks or [])
    candidate = SimpleNamespace(grounding_metadata=grounding_metadata)
    return SimpleNamespace(text=text, candidates=[candidate])


def _web_chunk(uri, title=None):
    return SimpleNamespace(web=SimpleNamespace(uri=uri, title=title))


class TestRunWebResearch:
    def test_returns_findings_and_sources(self, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.return_value = _grounded_response(
            "Bangkok: mehmonxona $20/kecha...",
            chunks=[_web_chunk("https://example.com/bangkok-prices", "Bangkok Prices")],
        )

        with patch("apps.admin_agent.services.research._get_client", return_value=client):
            result = run_web_research("Tailand", 5)

        assert result["ok"] is True
        assert "Bangkok" in result["findings"]
        assert result["sources"] == [{"title": "Bangkok Prices", "uri": "https://example.com/bangkok-prices"}]

    def test_missing_grounding_metadata_still_returns_findings(self, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.return_value = SimpleNamespace(text="Ma'lumot topildi", candidates=[])

        with patch("apps.admin_agent.services.research._get_client", return_value=client):
            result = run_web_research("Tailand", 5)

        assert result["ok"] is True
        assert result["sources"] == []

    def test_empty_response_text_is_an_error(self, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.return_value = _grounded_response("")

        with patch("apps.admin_agent.services.research._get_client", return_value=client):
            result = run_web_research("Tailand", 5)

        assert result["ok"] is False

    def test_api_error_is_reported_not_raised(self, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.side_effect = RuntimeError("boom")

        with patch("apps.admin_agent.services.research._get_client", return_value=client):
            result = run_web_research("Tailand", 5)

        assert result["ok"] is False
        assert "error" in result

    def test_city_count_is_capped_at_max(self, settings):
        settings.GEMINI_ADMIN_API_KEY = "fake-key"
        client = MagicMock()
        client.models.generate_content.return_value = _grounded_response("ok")

        with patch("apps.admin_agent.services.research._get_client", return_value=client):
            run_web_research("Tailand", 999)

        prompt = client.models.generate_content.call_args.kwargs["contents"]
        assert f"eng yaxshi {MAX_CITIES} ta shaharni" in prompt
